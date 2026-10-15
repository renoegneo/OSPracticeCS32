import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DELAY = 0.3             # ручка: имитация сетевой задержки, секунды
BODY = b"x" * 100_000   # ручка: размер "файла" в байтах

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(DELAY)
        self.send_response(200)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass            # не засоряем терминал логами

ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
