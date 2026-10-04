import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .engine import ASIBBrain
from .mission import MissionEvaluator
from .predictor import RiskPredictor
from .scenarios import run_fault_scenario
from .simulator import Simulator


class DashboardHandler(BaseHTTPRequestHandler):
    simulator = Simulator()
    brain = ASIBBrain()

    def json_response(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/state":
            world = self.simulator.world
            payload = {
                "tick": world.tick,
                "autonomy_mode": world.autonomy_mode.value,
                "comms_delay_s": world.comms_delay_s,
                "nodes": self.simulator.snapshot(),
                "risks": [r.__dict__ for r in RiskPredictor().predict(world)],
                "mission": MissionEvaluator().evaluate(world),
                "memory_entries": len(world.memory),
            }
            return self.json_response(payload)

        if parsed.path == "/api/scenario":
            name = parse_qs(parsed.query).get("name", ["compound"])[0]
            if name not in {"thermal", "power", "network", "compound"}:
                return self.json_response({"error": "unknown scenario"}, 400)
            result = run_fault_scenario(name)
            return self.json_response(result)

        html = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>ASIB Control Room</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:system-ui;margin:0;background:#080d18;color:#eaf0ff}
main{max-width:1200px;margin:auto;padding:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.card{background:#10192b;border:1px solid #263653;border-radius:14px;padding:18px}
button{padding:10px 14px;margin:4px;border:0;border-radius:8px;cursor:pointer}
.badge{font-weight:700}
pre{white-space:pre-wrap;overflow:auto}
h1{margin-bottom:4px}
small{opacity:.7}
</style></head>
<body><main>
<h1>ASIB Control Room</h1>
<small>Autonomous Space Infrastructure Brain · Earth-based research testbed</small>
<div class="card">
<b>Fault injection</b><br>
<button onclick="scenario('thermal')">Thermal</button>
<button onclick="scenario('power')">Power</button>
<button onclick="scenario('network')">Network</button>
<button onclick="scenario('compound')">Compound</button>
</div>
<div id="summary" class="grid"></div>
<div class="card"><h3>Node State</h3><pre id="nodes">Loading...</pre></div>
<div class="card"><h3>Risk Prediction</h3><pre id="risks">Loading...</pre></div>
<div class="card"><h3>Mission Health</h3><pre id="mission">Loading...</pre></div>
<script>
async function refresh(){
 const d=await (await fetch('/api/state')).json();
 document.getElementById('summary').innerHTML =
   '<div class="card"><b>Mode</b><br><span class="badge">'+d.autonomy_mode+'</span></div>'+
   '<div class="card"><b>Tick</b><br>'+d.tick+'</div>'+
   '<div class="card"><b>Memory</b><br>'+d.memory_entries+' events</div>'+
   '<div class="card"><b>Mission Score</b><br>'+d.mission.score+'/100</div>';
 document.getElementById('nodes').textContent=JSON.stringify(d.nodes,null,2);
 document.getElementById('risks').textContent=JSON.stringify(d.risks,null,2);
 document.getElementById('mission').textContent=JSON.stringify(d.mission,null,2);
}
async function scenario(name){
 await fetch('/api/scenario?name='+encodeURIComponent(name));
 await refresh();
}
refresh(); setInterval(refresh,1500);
</script>
</main></body></html>"""
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
