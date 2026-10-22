# RoadGuard — Traffic Detection & Congestion Mitigation

RoadGuard is a traffic-monitoring project that combines a **vehicle-detection module** with a **SUMO-based traffic simulation and Streamlit dashboard**. It is intended as a demonstrator for analysing traffic conditions and exploring congestion-mitigation strategies.

> **Current scope:** The repository contains a vehicle-detection script and a SUMO/Streamlit mitigation simulation. Treat simulation recommendations and signal adjustments as a demo; do not connect this prototype to real traffic signals or use it for operational traffic control.

## Contents

- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [1. Clone the repository](#1-clone-the-repository)
- [2. Set up traffic detection](#2-set-up-traffic-detection)
- [3. Set up traffic mitigation simulation](#3-set-up-traffic-mitigation-simulation)
- [How to use the repository](#how-to-use-the-repository)
- [Troubleshooting](#troubleshooting)
- [Limitations and next steps](#limitations-and-next-steps)

## Project structure

```text
RoadGuard-Demo/
├── RoadGuard detection/
│   ├── main.py
│   ├── requirements.txt
│   ├── yolo11n.pt
│   └── bus.jpg
├── RoadGuard mitigation/
│   ├── app.py
│   ├── requirements.txt
│   ├── README.md
│   └── sumo/
│       ├── roadguard.nod.xml
│       ├── roadguard.edg.xml
│       ├── roadguard.net.xml
│       ├── roadguard.rou.xml
│       └── roadguard.sumocfg
└── README.md
```

The exact files may change as the project develops.

| Component | Purpose | Entry point |
|---|---|---|
| Traffic detection | Runs the computer-vision vehicle-detection demo using the included YOLO model | `RoadGuard detection/main.py` |
| Congestion mitigation simulation | Runs a Streamlit dashboard connected to a SUMO traffic simulation | `RoadGuard mitigation/app.py` |
| SUMO scenario | Defines the simulated road network, routes, vehicles, and simulation configuration | `RoadGuard mitigation/sumo/` |

## Prerequisites

Install the following before running the project:

- **Git** — to clone and update the repository.
- **Python 3.10 or 3.11 recommended** — use a Python version compatible with the packages listed in each `requirements.txt`.
- **pip** — Python package installer.
- **SUMO (Simulation of Urban MObility)** — required for the mitigation simulation.
- **A terminal** — PowerShell on Windows, or a terminal on Linux/macOS.
- **Camera or video source (optional)** — only if the detection script is configured to process a live camera or video. The included `bus.jpg` can be used for an image-based test if supported by the script.

Check Python and pip:

```bash
python --version
python -m pip --version
```

On some Windows installations, use `py` instead of `python`.

### Install SUMO

Download and install SUMO from the official website:

https://sumo.dlr.de/docs/Installing/index.html

On Windows, make sure SUMO's `bin` directory is available on your `PATH`, or configure the environment variables as described in the SUMO documentation. If the app requires `SUMO_HOME`, set it to the SUMO installation directory (the directory containing SUMO's tools).

Verify that SUMO commands are available:

```bash
sumo --version
netconvert --version
```

If either command is not recognised, finish the SUMO installation or add its `bin` directory to `PATH`, then reopen the terminal.

## 1. Clone the repository

```bash
git clone https://github.com/Renet-Reji/RoadGuard-Demo.git
cd RoadGuard-Demo
```

If you already cloned the repository, enter the existing folder instead of cloning it again.

## 2. Set up traffic detection

Open a terminal at the repository root, then move into the detection folder:

```powershell
cd "RoadGuard detection"
```

### Create and activate a virtual environment

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can avoid changing the execution policy by using the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install detection dependencies

Run this from inside `RoadGuard detection`:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `-r requirements.txt` option tells pip to install the packages listed in that file. You do not need to install each listed package separately.

### Run the detection demo

```bash
python main.py
```

The script's exact input and output behaviour depends on its implementation. Check the comments or command-line options in `main.py` if it expects a particular image, video, or camera source. The included `yolo11n.pt` is a model file; keep it in the location expected by the script.

## 3. Set up traffic mitigation simulation

Open a **new terminal** or return to the repository root, then enter the mitigation folder:

```powershell
cd "RoadGuard mitigation"
```

Create a separate virtual environment for this module so its dependencies do not conflict with the detection module.

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the mitigation dependencies from its own requirements file:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> **Important:** Run the command from `RoadGuard mitigation`, because this project has a separate `requirements.txt` for each module.

### Start the Streamlit dashboard

From inside `RoadGuard mitigation`, run:

```bash
streamlit run app.py
```

Streamlit normally opens the dashboard in your browser. If it does not open automatically, use the local URL printed in the terminal (commonly `http://localhost:8501`).

### Run the SUMO scenario

The dashboard is designed to use the scenario files in `sumo/`. If you want to inspect the scenario directly in SUMO, first make sure SUMO is installed and then run this from the mitigation folder:

```bash
sumo-gui -c sumo/roadguard.sumocfg
```

If `sumo-gui` is not found, check the SUMO installation and `PATH`. The Streamlit app may start SUMO itself; avoid launching a second simulation if the dashboard is already managing the same scenario.

## How to use the repository

1. **Clone** the repository and install the prerequisites.
2. **Install detection dependencies** from `RoadGuard detection/requirements.txt` and run `main.py` to test the vehicle-detection module.
3. **Install mitigation dependencies** from `RoadGuard mitigation/requirements.txt`.
4. **Install SUMO** and confirm its commands are available.
5. **Launch the dashboard** with `streamlit run app.py` from the mitigation folder.
6. **Run and observe the simulation** through the dashboard. Use the SUMO GUI only when you want to inspect the scenario separately.
7. **Keep the two environments separate** unless you intentionally decide to consolidate dependencies.

### Installing both requirements files

If you want to install both sets of dependencies, install them in their respective environments:

```text
RoadGuard detection/requirements.txt  → detection environment
RoadGuard mitigation/requirements.txt → mitigation environment
```

Do not run `pip install -r requirements.txt` from the repository root unless you create a root-level requirements file. The root directory does not necessarily contain one.

## Troubleshooting

### `streamlit` is not recognised

Make sure the mitigation virtual environment is activated, then run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### `ModuleNotFoundError`

Check that you activated the correct virtual environment and installed the requirements file for the module you are running.

### SUMO or `netconvert` is not recognised

Install SUMO and add its `bin` directory to `PATH`. Reopen your terminal and verify with `sumo --version` and `netconvert --version`.

### `SUMO_HOME` or TraCI errors

Check the SUMO installation instructions and the app's configuration. Some SUMO Python tools, such as TraCI, are provided with SUMO; use a Python/SUMO setup compatible with the code.

### GitHub rejects a large file

GitHub blocks ordinary Git files larger than 100 MB. Large video files should generally be kept outside Git and ignored using `.gitignore`, or stored using Git LFS if they need to be versioned. Adding a file to `.gitignore` does not remove it from commits already in Git history.

### Dependency installation fails

- Confirm the Python version supported by the package versions in the relevant `requirements.txt`.
- Upgrade pip using `python -m pip install --upgrade pip`.
- Read the first package-specific error in the terminal; later errors may be consequences of that failure.
- Avoid installing both modules' dependencies into one environment until compatibility has been checked.

## Limitations and next steps

- The mitigation component is a **simulation/demo**, not a production traffic-control system.
- Vehicle detection quality depends on the model, input quality, lighting, camera angle, and configuration.
- Do not assume automatic diversion, multi-junction coordination, real CCTV ingestion, accident analysis, persistent database storage, or real signal control is implemented unless it is present in the current code.
- Before a live deployment, the system would need validated datasets, calibrated speed estimation, safety review, access controls, logging, testing, and integration with authorised traffic infrastructure.

## Contributing

1. Create a branch for your changes.
2. Keep module-specific dependencies in the correct `requirements.txt`.
3. Do not commit virtual environments, caches, secrets, or large raw videos.
4. Test the affected module before opening a pull request.

## License

Add the project's chosen license here before distributing or reusing the code.
