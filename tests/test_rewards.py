import concurrent.futures, json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from core import Store, Error
from app import make_server

class RewardsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=str(Path(self.temp.name)/'test.sqlite3'); self.s=Store(self.path)
        self.owner=self.s.register('factory','owner-test-password','owner')
        self.a=self.s.register('alice','alice-test-password'); self.b=self.s.register('bob','bob-test-password')
    def tearDown(self): self.temp.cleanup()
    def code(self,points=100): return self.s.issue(self.owner,'Batch A',points,1)['codes'][0]
    def value(self,sql,args=()):
        with self.s.db() as db: return db.execute(sql,args).fetchone()[0]
    def test_claim_once_across_customers(self):
        code=self.code(); self.assertEqual(self.s.claim(self.a,code),100)
        for uid in (self.a,self.b):
            with self.assertRaises(Error): self.s.claim(uid,code)
        self.assertEqual(self.value('SELECT sum(points) FROM users'),100)
    def test_concurrent_claim_one_winner(self):
        code=self.code()
        def run(uid):
            try: self.s.claim(uid,code); return True
            except Error: return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool: results=list(pool.map(run,[self.a,self.b]))
        self.assertEqual(sum(results),1); self.assertEqual(self.value('SELECT count(*) FROM ledger'),1)
    def test_revoked_expired_and_invalid_codes(self):
        code=self.code(); self.s.revoke(self.owner,1)
        with self.assertRaises(Error): self.s.claim(self.a,code)
        code=self.code()
        with self.s.db() as db: db.execute('UPDATE batches SET expires=0 WHERE id=2')
        for c in (code,'nonsense'):
            with self.assertRaises(Error): self.s.claim(self.a,c)
        self.assertEqual(self.value("SELECT count(*) FROM audit WHERE event='claim_rejected'"),3)
    def test_hashes_only(self):
        code=self.code(); self.assertNotEqual(self.value('SELECT hash FROM codes'),code)
        self.assertNotIn(code,Path(self.path).read_bytes().decode('latin1'))
    def test_concurrent_redemption_does_not_overspend(self):
        self.s.claim(self.a,self.code()); self.s.reward(self.owner,'Gift',75,10)
        def run(_):
            try: self.s.redeem(self.a,1); return True
            except Error: return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool: result=list(pool.map(run,[1,2]))
        self.assertEqual(sum(result),1); self.assertEqual(self.value('SELECT points FROM users WHERE id=?',(self.a,)),25)
    def test_last_stock_only_one_customer(self):
        for uid in (self.a,self.b): self.s.claim(uid,self.code())
        self.s.reward(self.owner,'Gift',50,1)
        def run(uid):
            try: self.s.redeem(uid,1); return True
            except Error: return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool: result=list(pool.map(run,[self.a,self.b]))
        self.assertEqual(sum(result),1); self.assertEqual(self.value('SELECT stock FROM rewards'),0)
    def test_cancel_refunds_once_at_original_price(self):
        self.s.claim(self.a,self.code()); self.s.reward(self.owner,'Gift',75,1); rid=self.s.redeem(self.a,1)
        self.s.reward(self.owner,'Gift',95,0,1)
        self.s.resolve(self.owner,rid,'cancelled')
        with self.assertRaises(Error): self.s.resolve(self.owner,rid,'cancelled')
        self.assertEqual(self.value('SELECT points FROM users WHERE id=?',(self.a,)),100)
        self.assertEqual(self.value('SELECT stock FROM rewards'),1)
    def test_fulfilled_cannot_cancel(self):
        self.s.claim(self.a,self.code()); self.s.reward(self.owner,'Gift',50,1); rid=self.s.redeem(self.a,1)
        self.s.resolve(self.owner,rid,'fulfilled')
        with self.assertRaises(Error): self.s.resolve(self.owner,rid,'cancelled')
    def test_create_hidden_reward(self):
        self.s.reward(self.owner,'Hidden',50,5,active=False)
        self.assertEqual(self.value('SELECT active FROM rewards'),0)
    def test_hidden_reward_cannot_redeem(self):
        self.s.claim(self.a,self.code()); self.s.reward(self.owner,'Hidden',50,5)
        self.s.reward(self.owner,'Hidden',50,5,1,False)
        with self.assertRaises(Error): self.s.redeem(self.a,1)
    def test_invalid_numeric_values(self):
        for v in (0,-1,True,1.2,'50'):
            with self.assertRaises(Error): self.s.issue(self.owner,'Bad',v,1)
    def test_rate_limit(self):
        for _ in range(15):
            with self.assertRaises(Error): self.s.claim(self.a,'bad')
        with self.assertRaisesRegex(Error,'Too many'): self.s.claim(self.a,self.code())
    def test_session_logout_and_expiry(self):
        token=self.s.login('alice','alice-test-password','test'); self.assertEqual(self.s.session(token)['id'],self.a)
        self.s.logout(token); self.assertIsNone(self.s.session(token))
        token=self.s.login('alice','alice-test-password','test')
        with self.s.db() as db: db.execute('UPDATE sessions SET expires=0')
        self.assertIsNone(self.s.session(token))
    def test_password_hash_and_duplicate_username(self):
        self.assertNotEqual(self.value('SELECT password FROM users WHERE id=?',(self.a,)),'alice-test-password')
        with self.assertRaises(Error): self.s.register('ALICE','another-password')
        with self.assertRaises(Error): self.s.login('alice','wrong-password','test')

class HTTPTests(RewardsTests):
    # Inherited domain tests also exercise setup with a real server attached.
    def setUp(self):
        super().setUp(); self.server=make_server('127.0.0.1',0,self.path)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.thread.join(); super().tearDown()
    def request(self,path,data=None,token='',csrf='',headers=True):
        h={'Cookie':'session='+token}
        if headers: h.update({'Content-Type':'application/json','X-App-Request':'1','X-CSRF-Token':csrf})
        req=urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers=h)
        try:
            with urllib.request.urlopen(req) as r: return r.status,r.read(),r.headers
        except urllib.error.HTTPError as e: return e.code,e.read(),e.headers
    def test_owner_permission_and_csrf(self):
        token=self.s.login('alice','alice-test-password','test'); csrf=self.s.session(token)['csrf']
        self.assertEqual(self.request('/api/owner/batches',{'name':'X','points':1,'count':1},token,csrf)[0],403)
        self.assertEqual(self.request('/api/claim',{'code':'bad'},token,'wrong')[0],403)
        self.assertEqual(self.request('/api/claim',{'code':'bad'})[0],401)
    def test_customer_cannot_choose_role(self):
        code,_,_=self.request('/api/register',{'username':'mallory','password':'mallory-password','role':'owner'})
        self.assertEqual(code,201); self.assertEqual(self.value("SELECT role FROM users WHERE username='mallory'"),'customer')
    def test_response_privacy(self):
        token=self.s.login('alice','alice-test-password','test'); code,body,_=self.request('/api/me',token=token)
        data=json.loads(body); self.assertEqual(code,200)
        self.assertNotIn('audit',data); self.assertNotIn('batches',data); self.assertNotIn('password',data['user'])
    def test_login_requires_custom_header(self):
        self.assertEqual(self.request('/api/login',{'username':'alice','password':'alice-test-password'},headers=False)[0],403)
    def test_static_and_missing_paths(self):
        for path in ('/','/app.js','/style.css'): self.assertEqual(self.request(path)[0],200)
        self.assertEqual(self.request('/../core.py')[0],404)
    def test_cookie_security_flags(self):
        code,_,headers=self.request('/api/login',{'username':'alice','password':'alice-test-password'})
        self.assertEqual(code,200); self.assertIn('HttpOnly',headers['Set-Cookie']); self.assertIn('SameSite=Strict',headers['Set-Cookie'])

if __name__=='__main__': unittest.main()
