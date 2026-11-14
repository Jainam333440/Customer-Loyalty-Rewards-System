"""Transactional domain layer. Only the HTTP adapter decides customer identity."""
import hashlib, hmac, secrets, sqlite3, time
from contextlib import contextmanager

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('owner','customer')), points INTEGER NOT NULL DEFAULT 0 CHECK(points>=0));
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), csrf TEXT NOT NULL, expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS batches(id INTEGER PRIMARY KEY, label TEXT NOT NULL, points INTEGER NOT NULL CHECK(points>0), expires REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS codes(hash TEXT PRIMARY KEY, batch_id INTEGER REFERENCES batches(id), claimed_by INTEGER REFERENCES users(id), claimed_at REAL);
CREATE TABLE IF NOT EXISTS rewards(id INTEGER PRIMARY KEY, name TEXT NOT NULL, cost INTEGER NOT NULL CHECK(cost>0), stock INTEGER NOT NULL CHECK(stock>=0), active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS redemptions(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), reward_id INTEGER REFERENCES rewards(id), cost INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), delta INTEGER NOT NULL, reason TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, user_id INTEGER, event TEXT NOT NULL, detail TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, bucket TEXT NOT NULL, created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_bucket ON attempts(bucket,created);
'''
class Error(Exception): pass

def password_hash(password):
    if not isinstance(password,str) or not 10 <= len(password) <= 128: raise Error('Use a password with 10–128 characters.')
    salt=secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()

def password_ok(password, stored):
    if not isinstance(password,str) or len(password)>128: return False
    salt, digest=stored.split(':')
    return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex(),digest)

def integer(value, low=1, high=100000):
    if type(value) is not int or not low<=value<=high: raise Error(f'Enter a whole number from {low} to {high}.')
    return value

def label(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=80: raise Error('Name must have 1–80 characters.')
    return value.strip()

class Store:
    def __init__(self,path):
        self.path=path
        with self.db() as db: db.executescript(SCHEMA)
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=15)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback(); raise
        finally: db.close()
    def audit(self,db,uid,event,detail=''):
        db.execute('INSERT INTO audit(user_id,event,detail,created) VALUES(?,?,?,?)',(uid,event,detail,time.time()))
    def register(self,username,password,role='customer'):
        username=label(username).lower()
        if not 3<=len(username)<=32 or not all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in username): raise Error('Username: 3–32 letters, numbers, underscores or hyphens.')
        hashed=password_hash(password)
        try:
            with self.db() as db:
                uid=db.execute('INSERT INTO users(username,password,role) VALUES(?,?,?)',(username,hashed,role)).lastrowid
                self.audit(db,uid,'account_created'); return uid
        except sqlite3.IntegrityError: raise Error('Username is unavailable.')
    def throttle(self,bucket,limit):
        with self.db() as db:
            now=time.time(); db.execute('DELETE FROM attempts WHERE created<?',(now-900,))
            count=db.execute('SELECT count(*) FROM attempts WHERE bucket=?',(bucket,)).fetchone()[0]
            if count>=limit: raise Error('Too many attempts. Try again in 15 minutes.')
            db.execute('INSERT INTO attempts(bucket,created) VALUES(?,?)',(bucket,now))
    def login(self,username,password,address):
        self.throttle('login:'+address,20)
        with self.db() as db:
            user=db.execute('SELECT * FROM users WHERE username=?',(str(username).lower(),)).fetchone()
            if not user or not password_ok(password,user['password']): raise Error('Invalid username or password.')
            token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,time.time()+28800))
            return token
    def session(self,token):
        with self.db() as db:
            row=db.execute('SELECT users.id,username,role,points,csrf FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
            return dict(row) if row else None
    def logout(self,token):
        with self.db() as db: db.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(token.encode()).hexdigest(),))
    def issue(self,uid,name,points,count):
        name=label(name); points=integer(points); count=integer(count,1,500)
        raw=[secrets.token_hex(16).upper() for _ in range(count)]
        with self.db() as db:
            bid=db.execute('INSERT INTO batches(label,points,expires) VALUES(?,?,?)',(name,points,time.time()+365*86400)).lastrowid
            db.executemany('INSERT INTO codes(hash,batch_id) VALUES(?,?)',[(hashlib.sha256(c.encode()).hexdigest(),bid) for c in raw])
            self.audit(db,uid,'batch_issued',str(bid))
        return {'batch_id':bid,'codes':raw}
    def claim(self,uid,raw):
        self.throttle('claim:'+str(uid),15)
        raw=str(raw).strip().upper().replace('-','').replace(' ','')
        digest=hashlib.sha256(raw.encode()).hexdigest()
        with self.db() as db:
            row=db.execute('SELECT codes.*,batches.points,batches.expires,batches.revoked FROM codes JOIN batches ON batches.id=codes.batch_id WHERE hash=?',(digest,)).fetchone()
            if not row or row['claimed_by'] or row['revoked'] or row['expires']<=time.time():
                self.audit(db,uid,'claim_rejected','invalid, used, expired or revoked')
                failed=True
            else:
                failed=False
                db.execute('UPDATE codes SET claimed_by=?,claimed_at=? WHERE hash=?',(uid,time.time(),digest))
                db.execute('UPDATE users SET points=points+? WHERE id=?',(row['points'],uid))
                db.execute('INSERT INTO ledger(user_id,delta,reason,created) VALUES(?,?,?,?)',(uid,row['points'],'Box claim',time.time()))
                self.audit(db,uid,'claim_accepted',str(row['batch_id']))
        if failed: raise Error('Code unavailable: invalid, already claimed, expired or revoked.')
        return row['points']
    def reward(self,uid,name,cost,stock,reward_id=None,active=True):
        name=label(name); cost=integer(cost); stock=integer(stock,0)
        with self.db() as db:
            if reward_id:
                if not db.execute('UPDATE rewards SET name=?,cost=?,stock=?,active=? WHERE id=?',(name,cost,stock,int(bool(active)),reward_id)).rowcount: raise Error('Reward not found.')
            else: db.execute('INSERT INTO rewards(name,cost,stock) VALUES(?,?,?)',(name,cost,stock))
            self.audit(db,uid,'reward_saved',name)
    def redeem(self,uid,rid):
        with self.db() as db:
            reward=db.execute('SELECT * FROM rewards WHERE id=? AND active=1',(rid,)).fetchone()
            user=db.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
            if not reward or reward['stock']<1: raise Error('Reward is unavailable.')
            if user['points']<reward['cost']: raise Error('Not enough points for this reward.')
            db.execute('UPDATE users SET points=points-? WHERE id=?',(reward['cost'],uid))
            db.execute('UPDATE rewards SET stock=stock-1 WHERE id=?',(rid,))
            redemption=db.execute('INSERT INTO redemptions(user_id,reward_id,cost,created) VALUES(?,?,?,?)',(uid,rid,reward['cost'],time.time())).lastrowid
            db.execute('INSERT INTO ledger(user_id,delta,reason,created) VALUES(?,?,?,?)',(uid,-reward['cost'],'Reward #'+str(redemption),time.time()))
            self.audit(db,uid,'reward_redeemed',str(redemption)); return redemption
    def resolve(self,uid,rid,status):
        if status not in ('fulfilled','cancelled'): raise Error('Invalid status.')
        with self.db() as db:
            r=db.execute('SELECT * FROM redemptions WHERE id=?',(rid,)).fetchone()
            if not r or r['status']!='pending': raise Error('Redemption is not pending.')
            db.execute('UPDATE redemptions SET status=? WHERE id=?',(status,rid))
            if status=='cancelled':
                db.execute('UPDATE users SET points=points+? WHERE id=?',(r['cost'],r['user_id']))
                db.execute('UPDATE rewards SET stock=stock+1 WHERE id=?',(r['reward_id'],))
                db.execute('INSERT INTO ledger(user_id,delta,reason,created) VALUES(?,?,?,?)',(r['user_id'],r['cost'],'Refund #'+str(rid),time.time()))
            self.audit(db,uid,'redemption_'+status,str(rid))
    def revoke(self,uid,bid):
        with self.db() as db:
            if not db.execute('UPDATE batches SET revoked=1 WHERE id=?',(bid,)).rowcount: raise Error('Batch not found.')
            self.audit(db,uid,'batch_revoked',str(bid))
    def dashboard(self,user):
        with self.db() as db:
            rows=lambda q,p=(): [dict(r) for r in db.execute(q,p)]
            owner=user['role']=='owner'
            result={'user':user,'rewards':rows('SELECT * FROM rewards'+('' if owner else ' WHERE active=1'))}
            result['redemptions']=rows('SELECT r.*,w.name,u.username FROM redemptions r JOIN rewards w ON w.id=r.reward_id JOIN users u ON u.id=r.user_id'+('' if owner else ' WHERE r.user_id=?')+' ORDER BY r.id DESC LIMIT 100',() if owner else (user['id'],))
            result['ledger']=rows('SELECT * FROM ledger WHERE user_id=? ORDER BY id DESC LIMIT 100',(user['id'],))
            if owner:
                result['batches']=rows('SELECT b.*,count(c.hash) total,count(c.claimed_by) claimed FROM batches b LEFT JOIN codes c ON c.batch_id=b.id GROUP BY b.id ORDER BY b.id DESC LIMIT 100')
                result['audit']=rows('SELECT a.*,u.username FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 100')
                result['metrics']={k:db.execute(q).fetchone()[0] for k,q in {'customers':"SELECT count(*) FROM users WHERE role='customer'",'claimed':'SELECT count(*) FROM codes WHERE claimed_by IS NOT NULL','outstanding':'SELECT coalesce(sum(points),0) FROM users','pending':"SELECT count(*) FROM redemptions WHERE status='pending'",'rejected':"SELECT count(*) FROM audit WHERE event='claim_rejected'"}.items()}
            return result
