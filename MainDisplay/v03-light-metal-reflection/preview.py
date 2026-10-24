from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import webbrowser
b=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(b)))
url=f'http://127.0.0.1:{server.server_port}/viewer/'
print('主展台暖光镜面版预览：'+url+'\n关闭此窗口即可停止预览。',flush=True)
webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
