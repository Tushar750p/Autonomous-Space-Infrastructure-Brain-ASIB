# APSE Rover — 2D Autonomous Exploration Prototype

APSE (Autonomous Planetary Science Explorer) is a **research/simulation-only** rover prototype. It is not flight software and does not control real spacecraft or physical hardware.

## Scope

This first milestone provides a deterministic 2D grid-world with:
- obstacle-aware shortest-path planning (BFS)
- simulated science targets with different illustrative values
- energy budget and return-to-base reserve
- target inspection while travelling
- CSV route log and PNG map output
- unit tests for pathfinding and safety-budget logic

The current science score is synthetic. It is not a validated scientific information-gain model and the world is not a physically accurate lunar or Martian terrain model.

## Requirements

- Windows 10/11
- Python 3.11–3.13, 64-bit (Python 3.12 is a conservative starting point)
- Internet for the initial dependency installation

## Windows setup

Run in PowerShell:

```powershell
cd "$HOME"
git clone https://github.com/Tushar750p/Autonomous-Space-Infrastructure-Brain-ASIB.git
cd Autonomous-Space-Infrastructure-Brain-ASIB/research/apse-rover

python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Outputs are written to `results/mission_route.csv` and `results/mission_map.png`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Model behaviour

- Each grid move costs one energy unit.
- Obstacles are impassable.
- A target is eligible only when a path to it and a path back to base exist and the current energy budget covers both plus the configured reserve.
- The planner ranks targets by illustrative science value divided by outbound path length.
- The rover returns to base if a valid return path and enough energy remain.

This is a simplified algorithmic demo. It does not model wheel slip, slopes, gravity, radiation, thermal effects, realistic sensors, communications delay, or flight hardware constraints.

## Roadmap

1. Validate and benchmark this 2D baseline.
2. Add uncertainty-aware target value and multiple planner baselines.
3. Import suitable NASA PDS terrain products with documented coordinate systems and resolution.
4. Add a 3D simulator (e.g. Webots) only after the 2D tests are stable.
5. Validate any physical rover separately with hardware safety controls.

## Scientific integrity

Do not describe simulated targets as discoveries, claim novelty without prior-art review, or present simulation results as flight qualification. Preserve seeds, configuration, data provenance, and failed runs in any research report.

## License

This prototype is contributed to the parent repository under its Apache-2.0 license, subject to the repository's license terms.
