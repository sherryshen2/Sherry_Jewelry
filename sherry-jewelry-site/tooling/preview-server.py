"""Local preview and reproducible failure-mode QA."""
import argparse,http.server,socketserver
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--open',action='store_true');parser.add_argument('--port',type=int,default=4173);parser.add_argument('--fail-models',action='store_true');parser.add_argument('--fail-photos',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parents[1]/'dist'
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
 def do_GET(self):
  p=self.path.split('?')[0]
  if (args.fail_models and p.endswith('.glb')) or (args.fail_photos and ('-photo.webp' in p or '-thumb.webp' in p)):
   self.send_error(503,'Intentional local QA failure');return
  super().do_GET()
 def end_headers(self):
  self.send_header('Cache-Control','no-cache');super().end_headers()
with socketserver.TCPServer(('127.0.0.1',args.port),Handler) as server:
 print(f'Local: http://127.0.0.1:{args.port}',flush=True)
 if args.open:
  import webbrowser
  webbrowser.open(f'http://127.0.0.1:{args.port}')
 server.serve_forever()
