import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .experiments import run_experiment_suite
from .mission import MissionEvaluator
from .predictor import RiskPredictor
from .runtime import ASIBRuntime
from .simulator import Simulator


class DashboardHandler(BaseHTTPRequestHandler):
    runtime = ASIBRuntime()
    lock = threading.Lock()

    def json_response(self, payload, status=200):
        body = json.dumps(payload, indent=2, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    @classmethod
    def state(cls):
        rt = cls.runtime
        world = rt.world
        return {
            "tick": world.tick,
            "autonomy_mode": world.autonomy_mode.value,
            "comms_delay_s": world.comms_delay_s,
            "earth_contact_available": world.earth_contact_available,
            "nodes": rt.simulator.snapshot(),
            "risks": [r.__dict__ for r in RiskPredictor().predict(world)],
            "mission": MissionEvaluator().evaluate(world),
            "memory_entries": len(world.memory),
            "knowledge": rt.knowledge.summary(world),
            "robots": {k: v.__dict__ for k, v in rt.robots.robots.items()},
            "audit": {
                "valid": world.audit_ledger.verify(),
                "entries": len(world.audit_ledger.entries),
                "latest_digest": world.audit_ledger.entries[-1].digest if world.audit_ledger.entries else None,
            },
            "replay": {
                "frames": len(rt.replay.frames),
                "valid": rt.replay.validate(),
            },
            "last_decision": world.decision_log[-1] if world.decision_log else None,
        }

    @classmethod
    def apply_injection(cls, name: str):
        rt = cls.runtime
        sim = rt.simulator
        if name == "thermal":
            sim.inject_thermal_failure("orbital-node-01", 96)
        elif name == "power":
            sim.inject_power_failure("orbital-node-02", 12)
        elif name == "network":
            sim.world.nodes["orbital-node-03"].critical_workload = 0
            sim.inject_network_failure("orbital-node-03")
        elif name == "partition":
            sim.inject_network_partition("orbital-node-02")
        elif name == "compute":
            sim.inject_compute_overload("orbital-node-01", 45)
        elif name == "earth-loss":
            sim.inject_earth_contact_loss()
        elif name == "compound":
            sim.inject_thermal_failure("orbital-node-01", 96)
            sim.inject_power_failure("orbital-node-02", 20)
            sim.world.nodes["orbital-node-03"].critical_workload = 0
            sim.inject_network_failure("orbital-node-03")
            sim.inject_network_partition("orbital-node-02")
            sim.inject_comms_delay(12.0)
        else:
            raise ValueError("unknown scenario")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/state":
            with self.lock:
                return self.json_response(self.state())

        if parsed.path == "/api/tick":
            with self.lock:
                report = self.runtime.tick()
                return self.json_response(report.__dict__)

        if parsed.path == "/api/reset":
            with self.lock:
                self.runtime.reset()
                return self.json_response(self.state())

        if parsed.path == "/api/experiments":
            ticks = int(parse_qs(parsed.query).get("ticks", ["10"])[0])
            if ticks < 1 or ticks > 500:
                return self.json_response({"error": "ticks must be in [1, 500]"}, 400)
            return self.json_response(run_experiment_suite(ticks))

        if parsed.path == "/api/scenario":
            name = parse_qs(parsed.query).get("name", ["compound"])[0]
            try:
                with self.lock:
                    self.apply_injection(name)
                    report = self.runtime.tick()
                    return self.json_response(report.__dict__)
            except ValueError:
                return self.json_response({"error": "unknown scenario"}, 400)

        html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASIB Control Room</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,sans-serif}
body{margin:0;background:#070b14;color:#edf3ff}
main{max-width:1400px;margin:auto;padding:26px}
.header{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap}
h1{margin:0 0 6px;font-size:30px}.muted{opacity:.65}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}
.card{background:#0f1728;border:1px solid #263754;border-radius:14px;padding:16px}
.kpi{font-size:26px;font-weight:750;margin-top:5px}
button{background:#1a2740;color:#fff;border:1px solid #324666;border-radius:8px;padding:9px 12px;margin:4px;cursor:pointer}
button:hover{filter:brightness(1.15)}
pre{white-space:pre-wrap;overflow:auto;max-height:420px;font-size:12px}
.status{font-weight:800}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{text-align:left;padding:8px;border-bottom:1px solid #24314b}
.good{font-weight:700}.warn{font-weight:700}
</style>
</head>
<body><main>
<div class="header">
<div><h1>🛰️ ASIB Control Room</h1><div class="muted">Autonomous Space Infrastructure Brain · Earth-based research testbed</div></div>
<div><button onclick="call('/api/tick')">Run Tick</button><button onclick="call('/api/reset')">Reset</button><button onclick="runExperiments()">Validation Suite</button></div>
</div>

<div class="card">
<b>Fault Injection / Research Scenarios</b><br>
<button onclick="scenario('thermal')">Thermal</button>
<button onclick="scenario('power')">Power</button>
<button onclick="scenario('compute')">Compute</button>
<button onclick="scenario('network')">Network</button>
<button onclick="scenario('partition')">Network Partition</button>
<button onclick="scenario('compound')">Compound</button>
<button onclick="scenario('earth-loss')">Earth Contact Loss</button>
</div>

<div id="kpis" class="grid"></div>

<div class="card"><h3>Node Telemetry</h3><div id="nodeTable"></div></div>
<div class="grid">
<div class="card"><h3>Risk Forecast</h3><pre id="risks">Loading...</pre></div>
<div class="card"><h3>Distributed Knowledge</h3><pre id="knowledge">Loading...</pre></div>
<div class="card"><h3>Robot Fleet</h3><pre id="robots">Loading...</pre></div>
<div class="card"><h3>Audit Ledger</h3><pre id="audit">Loading...</pre></div>
<div class="card"><h3>Replay Journal</h3><pre id="replay">Loading...</pre></div>
</div>
<div class="card"><h3>Experiment Validation</h3><pre id="experiments">Run the validation suite to compare ASIB against a passive baseline.</pre></div>
<div class="card"><h3>Last Autonomous Decision Trace</h3><pre id="decision">None</pre></div>

<script>
async function call(url){
  const r=await fetch(url); const d=await r.json();
  await refresh(); return d;
}
async function scenario(name){ await call('/api/scenario?name='+encodeURIComponent(name)); }
async function runExperiments(){
  const d=await (await fetch('/api/experiments?ticks=10')).json();
  document.getElementById('experiments').textContent=JSON.stringify(d,null,2);
}
function esc(x){return String(x).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
async function refresh(){
 const d=await (await fetch('/api/state',{cache:'no-store'})).json();
 document.getElementById('kpis').innerHTML =
 '<div class="card"><div class="muted">Autonomy mode</div><div class="kpi">'+esc(d.autonomy_mode)+'</div></div>'+
 '<div class="card"><div class="muted">Simulation tick</div><div class="kpi">'+d.tick+'</div></div>'+
 '<div class="card"><div class="muted">Mission score</div><div class="kpi">'+d.mission.score+'/100</div></div>'+
 '<div class="card"><div class="muted">Memory events</div><div class="kpi">'+d.memory_entries+'</div></div>'+
 '<div class="card"><div class="muted">Comms delay</div><div class="kpi">'+d.comms_delay_s+'s</div></div>'+
 '<div class="card"><div class="muted">Max knowledge age</div><div class="kpi">'+d.knowledge.max_age_ticks+'t</div></div>'+
 '<div class="card"><div class="muted">Earth contact</div><div class="kpi">'+(d.earth_contact_available?'AVAILABLE':'LOST')+'</div></div>';

 let rows='<table><tr><th>Node</th><th>Temp</th><th>Power</th><th>CPU</th><th>Workload</th><th>Network</th><th>Status</th></tr>';
 for(const [id,n] of Object.entries(d.nodes)){
   rows+='<tr><td>'+esc(id)+'</td><td>'+n.temperature_c+'°C</td><td>'+n.power_pct+'%</td><td>'+n.cpu_load+'%</td><td>'+n.workload+'</td><td>'+ (n.network_ok?'UP':'DOWN') +'</td><td class="status">'+esc(n.status)+'</td></tr>';
 }
 document.getElementById('nodeTable').innerHTML=rows+'</table>';
 document.getElementById('risks').textContent=JSON.stringify(d.risks,null,2);
 document.getElementById('knowledge').textContent=JSON.stringify(d.knowledge,null,2);
 document.getElementById('robots').textContent=JSON.stringify(d.robots,null,2);
 document.getElementById('audit').textContent=JSON.stringify(d.audit,null,2);
 document.getElementById('replay').textContent=JSON.stringify(d.replay,null,2);
 document.getElementById('decision').textContent=JSON.stringify(d.last_decision,null,2);
}
refresh(); setInterval(refresh,1500);
</script>
</main></body></html>"""

        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


def _autonomous_loop(interval_s: float):
    while True:
        time.sleep(interval_s)
        try:
            with DashboardHandler.lock:
                DashboardHandler.runtime.tick()
        except Exception:
            # The dashboard must remain available if a simulation step fails.
            pass


def run(host="127.0.0.1", port=8080, interval_s=1.0):
    thread = threading.Thread(target=_autonomous_loop, args=(interval_s,), daemon=True)
    thread.start()
    print(f"ASIB dashboard: http://{host}:{port}")
    ThreadingHTTPServer((host, port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    run()
