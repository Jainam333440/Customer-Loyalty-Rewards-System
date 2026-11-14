"""Local demo server. Put behind a trusted HTTPS reverse proxy for deployment."""
import argparse, getpass, json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from core import Store, Error, integer

ROOT=Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): pass  # Avoid logging credentials or box codes.
    def reply(self,status,data,ctype='application/json',cookie=None):
        body=json.dumps(data).encode() if ctype=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie is not None:
            secure='; Secure' if os.getenv('COOKIE_SECURE')=='1' else ''
            self.send_header('Set-Cookie',f'session={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age={28800 if cookie else 0}{secure}')
        self.end_headers(); self.wfile.write(body)
    def token(self):
        try:
            c=SimpleCookie(self.headers.get('Cookie','')); return c['session'].value if 'session' in c else ''
        except Exception: return ''
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/api/me':
            user=self.server.store.session(self.token())
            return self.reply(200,self.server.store.dashboard(user)) if user else self.reply(401,{'error':'Please sign in.'})
        assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if path not in assets: return self.reply(404,{'error':'Not found.'})
        file,ctype=assets[path]; self.reply(200,(ROOT/'static'/file).read_bytes(),ctype)
    def do_POST(self):
        try:
            # JSON plus a custom header prevents cross-site form/login CSRF; no CORS is enabled.
            if self.headers.get('Content-Type','').split(';')[0]!='application/json' or self.headers.get('X-App-Request')!='1': return self.reply(403,{'error':'Invalid request origin.'})
            if self.headers.get('Sec-Fetch-Site')=='cross-site': return self.reply(403,{'error':'Cross-site request blocked.'})
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=8192: return self.reply(413,{'error':'Request too large or empty.'})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise Error('Expected a JSON object.')
            store=self.server.store; path=self.path
            if path=='/api/register':
                store.throttle('register:'+self.client_address[0],10)
                store.register(data.get('username'),data.get('password'))
                return self.reply(201,{'message':'Account created. Sign in to start earning.'})
            if path=='/api/login':
                token=store.login(data.get('username'),data.get('password'),self.client_address[0])
                return self.reply(200,{'message':'Signed in.'},cookie=token)
            user=store.session(self.token())
            if not user: return self.reply(401,{'error':'Please sign in.'})
            if self.headers.get('X-CSRF-Token')!=user['csrf']: return self.reply(403,{'error':'Invalid security token. Refresh the page.'})
            uid=user['id']
            if path.startswith('/api/owner/') and user['role']!='owner': return self.reply(403,{'error':'Owner access required.'})
            if path in ('/api/claim','/api/redeem') and user['role']!='customer': return self.reply(403,{'error':'Use a customer account for this action.'})
            if path=='/api/logout':
                store.logout(self.token()); return self.reply(200,{'message':'Signed out.'},cookie='')
            if path=='/api/claim': return self.reply(200,{'message':f"You earned {store.claim(uid,data.get('code',''))} points!"})
            if path=='/api/redeem': return self.reply(201,{'message':f"Reward reserved. Pickup reference #{store.redeem(uid,integer(data.get('reward_id')))}."})
            if path=='/api/owner/batches': return self.reply(201,store.issue(uid,data.get('name'),data.get('points'),data.get('count')))
            if path=='/api/owner/revoke': store.revoke(uid,integer(data.get('batch_id')))
            elif path=='/api/owner/rewards': store.reward(uid,data.get('name'),data.get('cost'),data.get('stock'),integer(data['reward_id']) if data.get('reward_id') else None,data.get('active',True))
            elif path=='/api/owner/resolve': store.resolve(uid,integer(data.get('redemption_id')),data.get('status'))
            else: return self.reply(404,{'error':'Not found.'})
            return self.reply(200,{'message':'Changes saved.'})
        except (Error,ValueError,TypeError) as e: self.reply(400,{'error':str(e) if isinstance(e,Error) else 'Invalid request values.'})
        except Exception: self.reply(500,{'error':'Unable to complete request. Please try again.'})

def make_server(host,port,path):
    server=ThreadingHTTPServer((host,port),Handler); server.store=Store(path); return server

if __name__=='__main__':
    path=os.getenv('DATABASE_PATH','loyalty.sqlite3')
    if len(sys.argv)>1 and sys.argv[1]=='init':
        store=Store(path)
        try:
            username=input('Owner username: '); password=getpass.getpass('Owner password (10+ characters): ')
            if password!=getpass.getpass('Repeat password: '): raise Error('Passwords do not match.')
            uid=store.register(username,password,'owner')
            store.reward(uid,'Factory favorites gift box',150,20)
            store.reward(uid,'Everyday cotton tote',75,30)
            store.reward(uid,'Premium product hamper',300,10)
            print('Owner and starter rewards created. Run python app.py.')
        except Error as e: print(e); sys.exit(1)
    else:
        parser=argparse.ArgumentParser()
        parser.add_argument('--host',default=os.getenv('HOST','127.0.0.1'))
        parser.add_argument('--port',type=int,default=int(os.getenv('PORT','8000')))
        parser.add_argument('--strictPort',action='store_true')
        args=parser.parse_args(); host=args.host; port=args.port
        server=make_server(host,port,path)
        print(f'Box & Bonus running at http://{host}:{port}'); server.serve_forever()
