# RoadGuard — SUMO + Streamlit Hybrid Demo

A starter implementation for the RoadGuard final-year project. SUMO simulates traffic, TraCI exposes simulation state and signal control, and Streamlit displays the dashboard.

## Features in this milestone
- Small connected network with a main and alternate route
- Vehicle count, mean speed, edge queue and congestion indicators
- Adaptive green-phase extension when the current green serves a queued approach
- Dashboard event log and time-series charts
- Optional SUMO GUI

> This is a simulation prototype, not a deployed traffic-control system. Congestion thresholds and signal logic are demonstration heuristics and must be calibrated and evaluated before any real-world use.

## 1. Install SUMO

### Windows
Install SUMO from the official downloads page: https://sumo.dlr.de/docs/Downloads.html

During setup, enable adding SUMO to PATH if offered. Otherwise add the SUMO `bin` folder to PATH and set `SUMO_HOME` to the SUMO installation directory.

Open a **new** terminal and check:
```powershell
sumo --version
sumo-gui --version
netconvert --version
```

### Ubuntu / WSL
```bash
sudo apt update
sudo apt install sumo sumo-tools sumo-doc
sumo --version
netconvert --version
```

Official SUMO docs: https://sumo.dlr.de/docs/Installing/index.html

## 2. Create the Python environment

Use Python 3.10 or 3.11 for a predictable setup.

### Windows PowerShell
```powershell
cd RoadGuard
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\Scripts\activate.bat
```

### Ubuntu / WSL
```bash
cd RoadGuard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Launch the dashboard
```bash
streamlit run app.py
```
Open the local URL Streamlit prints (usually http://localhost:8501).

On first launch, the app runs `netconvert` to generate `sumo/roadguard.net.xml` from the included node and edge files.

## 4. Demo procedure
1. Start with mitigation enabled and run several batches.
2. Record the queue, average speed and congestion status.
3. Reset, disable mitigation, and run the same number of steps.
4. Compare queue and speed trends. For a fair test, repeat each scenario several times and report mean values.
5. Optionally enable “Open SUMO visual interface” to watch vehicles move in SUMO-GUI.

## Troubleshooting
- **`sumo` or `netconvert` not found:** ensure the SUMO `bin` folder is in PATH, or set `SUMO_HOME`, then restart your terminal.
- **`No module named traci`:** activate the venv and run `pip install -r requirements.txt`.
- **`netconvert` errors:** inspect the error displayed in the dashboard. Delete `sumo/roadguard.net.xml` and restart to regenerate it after changing node/edge files.
- **SUMO GUI doesn't open:** first test the app with the GUI checkbox disabled. GUI mode requires a desktop session.
- **No obvious congestion:** the provided demand is a starting point. Increase `vehsPerHour` in `sumo/roadguard.rou.xml`, then reset and restart the app.

## Project structure
```text
RoadGuard/
├── app.py
├── requirements.txt
├── README.md
└── sumo/
    ├── roadguard.nod.xml
    ├── roadguard.edg.xml
    ├── roadguard.net.xml   # generated automatically
    ├── roadguard.rou.xml
    └── roadguard.sumocfg
```

## Next milestones
1. Add route diversion based on downstream capacity and travel-time estimates.
2. Add baseline-vs-mitigation experiment runner and export CSV results.
3. Integrate YOLO + OpenCV for CCTV video vehicle detection.
4. Add road-damage classification and suspected-accident incident records.
5. Add map view and persistent SQLite event history.
