import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .engine import ASIBBrain
from .simulator import Simulator


class DashboardHandler(BaseHTTPRequestHandler):
    simulator = Simulator()
    brain = ASIBBrain()

    def do_GET(self):
        if self.path == "/api/state":
            payload = {
                "tick": self.simulator.world.tick,
                "autonomy_mode": self.simulator.world.autonomy_mode.value,
                "nodes": self.simulator.snapshot(),
                "memory_entries": len(self.simulator.world.memory),
            }
            body = json.dumps(payload, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        html = """<!doctype html>
<html><head><meta charset="utf-8"><title>ASIB Control Room</title>
<style>body{font-family:system-ui;margin:40px;background:#0b1020;color:#eef}
.card{padding:18px;margin:10px 0;border:1px solid #334;border-radius:12px}
pre{white-space:pre-wrap}</style></head>
<body><h1>ASIB Control Room</h1><div id="app" class="card">Loading...</div>
<script>
async function refresh(){
 const r=await fetch('/api/state'); const d=await r.json();
 document.getElementById('app').innerHTML =
   '<b>Tick:</b> '+d.tick+' &nbsp; <b>Mode:</b> '+d.autonomy_mode+
   '<br><b>Memory:</b> '+d.memory_entries+' events<pre>'+JSON.stringify(d.nodes,null,2)+'</pre>';
}
refresh(); setInterval(refresh,1000);
</script></body></html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


def run(host="127.0.0.1", port=8080):
    print(f"ASIB dashboard: http://{host}:{port}")
    HTTPServer((host, port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    run()
