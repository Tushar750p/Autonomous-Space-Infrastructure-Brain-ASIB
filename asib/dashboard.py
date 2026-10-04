import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from .engine import ASIBBrain
from .mission import MissionEvaluator
from .predictor import RiskPredictor
from .simulator import Simulator


class DashboardHandler(BaseHTTPRequestHandler):
    simulator = Simulator()
    brain = ASIBBrain()
    predictor = RiskPredictor()
    evaluator = MissionEvaluator()

    def _json(self, payload):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _state(self):
        world = self.simulator.world
        return {
            "tick": world.tick,
            "autonomy_mode": world.autonomy_mode.value,
            "comms_delay_s": world.comms_delay_s,
            "nodes": self.simulator.snapshot(),
            "risks": [r.__dict__ for r in self.predictor.predict(world)],
            "mission": self.evaluator.evaluate(world),
            "memory_entries": len(world.memory),
        }

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/state":
            self._json(self._state())
            return

        if parsed.path == "/api/step":
            self.simulator.advance_physics()
            events = self.brain.step(self.simulator.world)
            self._json({"events": [e.__dict__ for e in events], "state": self._state()})
            return

        if parsed.path == "/api/fault":
            scenario = parse_qs(parsed.query).get("type", ["thermal"])[0]
            node_id = parse_qs(parsed.query).get("node", ["orbital-node-01"])[0]

            if scenario == "thermal":
                self.simulator.inject_thermal_failure(node_id)
            elif scenario == "power":
                self.simulator.inject_power_failure(node_id, 12.0)
            elif scenario == "network":
                self.simulator.inject_network_failure(node_id)
            elif scenario == "compute":
                self.simulator.inject_compute_overload(node_id, 45.0)
            else:
                self.send_error(400, "Unknown fault type")
                return

            self._json({"injected": scenario, "node": node_id, "state": self._state()})
            return

        html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASIB Autonomous Control Room</title>
<style>
body{font-family:system-ui;margin:0;background:#070b14;color:#edf2ff}
main{max-width:1200px;margin:auto;padding:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card{padding:18px;background:#0f1625;border:1px solid #26324a;border-radius:16px}
button{padding:10px 14px;margin:4px;border:0;border-radius:10px;cursor:pointer}
.meter{font-variant-numeric:tabular-nums}
pre{white-space:pre-wrap;overflow:auto}
small{opacity:.7}
</style>
</head>
<body>
<main>
<h1>ASIB Autonomous Control Room</h1>
<p><small>Earth-based digital-twin research testbed. No real spacecraft commands.</small></p>
<div id="top" class="grid"></div>
<div class="card">
<h2>Fault Injection</h2>
<button onclick="fault('thermal')">Thermal fault</button>
<button onclick="fault('power')">Power fault</button>
<button onclick="fault('network')">Network fault</button>
<button onclick="fault('compute')">Compute overload</button>
<button onclick="step()">Advance + Autonomous Step</button>
</div>
<div id="nodes" class="grid"></div>
<div class="card"><h2>Decision / Memory Trace</h2><pre id="trace">Loading...</pre></div>
</main>
<script>
async function getState(){
  const r=await fetch('/api/state'); return r.json();
}
function esc(s){return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')}
async function refresh(){
  const d=await getState();
  document.getElementById('top').innerHTML =
    '<div class="card"><h3>Autonomy</h3><div class="meter">'+esc(d.autonomy_mode)+'</div><small>Tick '+d.tick+'</small></div>'+
    '<div class="card"><h3>Mission Score</h3><div class="meter">'+d.mission.score+' / 100</div><small>Availability '+d.mission.availability_pct+'%</small></div>'+
    '<div class="card"><h3>Highest Risk</h3><div class="meter">'+(d.risks[0]?esc(d.risks[0].node_id)+' — '+d.risks[0].score:'none')+'</div><small>'+esc(d.risks[0]?.reasons?.join(', ')||'No active risk')+'</small></div>'+
    '<div class="card"><h3>Memory</h3><div class="meter">'+d.memory_entries+' events</div><small>Comms delay '+d.comms_delay_s+' s</small></div>';
  document.getElementById('nodes').innerHTML = Object.entries(d.nodes).map(([id,n]) =>
    '<div class="card"><h3>'+esc(id)+'</h3>'+
    '<div>CPU: '+n.cpu_load.toFixed(1)+'%</div>'+
    '<div>Temp: '+n.temperature_c.toFixed(1)+' °C</div>'+
    '<div>Power: '+n.power_pct.toFixed(1)+'%</div>'+
    '<div>Workload: '+n.workload.toFixed(1)+'</div>'+
    '<div>Network: '+(n.network_ok?'OK':'DOWN')+'</div>'+
    '<div>Status: <b>'+esc(n.status)+'</b></div></div>').join('');
}
async function step(){
  const r=await fetch('/api/step'); const d=await r.json();
  document.getElementById('trace').textContent = JSON.stringify(d.events,null,2);
  refresh();
}
async function fault(type){
  const r=await fetch('/api/fault?type='+encodeURIComponent(type)); const d=await r.json();
  document.getElementById('trace').textContent = JSON.stringify(d,null,2);
  refresh();
}
refresh(); setInterval(refresh,1500);
</script>
</body>
</html>"""
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
