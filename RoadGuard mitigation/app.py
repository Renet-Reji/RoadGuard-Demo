import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import traci
except ImportError:
    traci = None

BASE_DIR = Path(__file__).resolve().parent
SUMO_DIR = BASE_DIR / "sumo"
NET_FILE = SUMO_DIR / "roadguard.net.xml"
CFG_FILE = SUMO_DIR / "roadguard.sumocfg"
NOD_FILE = SUMO_DIR / "roadguard.nod.xml"
EDG_FILE = SUMO_DIR / "roadguard.edg.xml"

st.set_page_config(page_title="RoadGuard | Traffic Operations", page_icon="🚦", layout="wide")

def find_sumo_binary(gui=False):
    name = "sumo-gui" if gui else "sumo"
    found = shutil.which(name) or shutil.which(name + ".exe")
    if found:
        return found
    home = os.environ.get("SUMO_HOME")
    if home:
        candidate = Path(home) / "bin" / (name + (".exe" if os.name == "nt" else ""))
        if candidate.exists():
            return str(candidate)
    return None

def ensure_network():
    if NET_FILE.exists():
        return True, "Network file already exists."
    netconvert = shutil.which("netconvert") or shutil.which("netconvert.exe")
    if not netconvert:
        home = os.environ.get("SUMO_HOME")
        if home:
            candidate = Path(home) / "bin" / ("netconvert.exe" if os.name == "nt" else "netconvert")
            if candidate.exists():
                netconvert = str(candidate)
    if not netconvert:
        return False, "Could not find netconvert. Install SUMO and add its bin folder to PATH, or set SUMO_HOME."
    result = subprocess.run(
        [netconvert, "--node-files", str(NOD_FILE), "--edge-files", str(EDG_FILE),
         "--output-file", str(NET_FILE), "--no-turnarounds", "true"],
        capture_output=True, text=True, cwd=str(SUMO_DIR)
    )
    if result.returncode != 0:
        return False, "netconvert failed:\n" + (result.stderr or result.stdout)
    return True, "SUMO road network generated."

def init_state():
    defaults = {
        "running": False, "step": 0, "history": [], "events": [],
        "last_error": "", "mitigation_enabled": True, "gui_enabled": False,
        "tls_id": "B", "sumo_started": False, "total_departed": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def close_sumo():
    if st.session_state.get("sumo_started") and traci:
        try:
            traci.close(False)
        except Exception:
            pass
    st.session_state["sumo_started"] = False
    st.session_state["running"] = False

def start_sumo(use_gui=False):
    if traci is None:
        raise RuntimeError("TraCI is not installed. Run: pip install -r requirements.txt")
    ok, message = ensure_network()
    if not ok:
        raise RuntimeError(message)
    binary = find_sumo_binary(gui=use_gui)
    if not binary:
        raise RuntimeError("SUMO executable not found. Install SUMO and add its bin folder to PATH, or set SUMO_HOME.")
    close_sumo()
    command = [binary, "-c", str(CFG_FILE), "--start", "--quit-on-end", "false"]
    if not use_gui:
        command += ["--no-step-log", "true", "--duration-log.disable", "true"]
    traci.start(command)
    st.session_state["sumo_started"] = True
    st.session_state["step"] = 0
    st.session_state["history"] = []
    st.session_state["events"] = []
    st.session_state["last_error"] = ""
    st.session_state["total_departed"] = 0
    st.session_state["running"] = True
    st.session_state["gui_enabled"] = use_gui
    st.session_state["events"].append({"Step": 0, "Event": "Simulation started", "Action": "Monitoring enabled"})

def collect_metrics():
    vehicle_ids = traci.vehicle.getIDList()
    speeds = [traci.vehicle.getSpeed(v) for v in vehicle_ids]
    edge_ids = ["AB", "BA", "AC", "CA", "BD", "DB", "CD", "DC", "BC", "CB"]
    edge_rows = []
    for edge in edge_ids:
        try:
            lanes = traci.edge.getLaneNumber(edge)
            halting = sum(traci.lane.getLastStepHaltingNumber(f"{edge}_{i}") for i in range(lanes))
            count = traci.edge.getLastStepVehicleNumber(edge)
            mean_speed = traci.edge.getLastStepMeanSpeed(edge)
            edge_rows.append({"Edge": edge, "Vehicles": count, "Queue": halting, "Mean speed (m/s)": round(mean_speed, 2)})
        except Exception:
            edge_rows.append({"Edge": edge, "Vehicles": 0, "Queue": 0, "Mean speed (m/s)": 0.0})
    edge_df = pd.DataFrame(edge_rows)
    total_queue = int(edge_df["Queue"].sum())
    avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
    vehicle_count = len(vehicle_ids)
    # Demo thresholds; calibrate these against the chosen road network and traffic demand.
    if total_queue >= 18 or (vehicle_count >= 35 and avg_speed < 3.0):
        level = "HIGH"
    elif total_queue >= 8 or (vehicle_count >= 20 and avg_speed < 6.0):
        level = "MODERATE"
    else:
        level = "LOW"
    return {
        "Step": st.session_state["step"],
        "Vehicles": vehicle_count,
        "Average speed (m/s)": round(avg_speed, 2),
        "Queue total": total_queue,
        "Congestion": level,
        "Edges": edge_df,
    }

def adapt_signal(metrics):
    """Extend a green phase only when that phase serves a queued incoming edge."""
    if not st.session_state["mitigation_enabled"]:
        return
    if metrics["Congestion"] == "LOW":
        return
    tls_ids = traci.trafficlight.getIDList()
    if not tls_ids:
        return
    tls = st.session_state.get("tls_id", "B")
    if tls not in tls_ids:
        tls = tls_ids[0]
    current_phase = traci.trafficlight.getPhase(tls)
    program = traci.trafficlight.getAllProgramLogics(tls)
    if not program:
        return
    logic = next((p for p in program if p.programID == traci.trafficlight.getProgram(tls)), program[0])
    if current_phase >= len(logic.phases):
        return
    state = logic.phases[current_phase].state
    links = traci.trafficlight.getControlledLinks(tls)
    queued_edges = set(metrics["Edges"].loc[metrics["Edges"]["Queue"] >= 3, "Edge"].tolist())
    serves_queued_edge = False
    for i, link_group in enumerate(links):
        if i >= len(state) or state[i] not in ("G", "g"):
            continue
        for link in link_group:
            from_lane = link[0]
            from_edge = from_lane.rsplit("_", 1)[0] if from_lane else ""
            if from_edge in queued_edges:
                serves_queued_edge = True
                break
        if serves_queued_edge:
            break
    if serves_queued_edge:
        # setPhaseDuration sets the remaining time, so add 8 seconds to the current remainder.
        remaining = max(0.0, traci.trafficlight.getNextSwitch(tls) - traci.simulation.getTime())
        traci.trafficlight.setPhaseDuration(tls, remaining + 8.0)
        st.session_state["events"].append({
            "Step": st.session_state["step"],
            "Event": f"{metrics['Congestion']} congestion at {tls}",
            "Action": "Extended current green phase by up to 8 seconds"
        })

def run_steps(number_of_steps):
    if not st.session_state["sumo_started"]:
        start_sumo(st.session_state["gui_enabled"])
    for _ in range(number_of_steps):
        traci.simulationStep()
        st.session_state["step"] += 1
        metrics = collect_metrics()
        adapt_signal(metrics)
        st.session_state["history"].append({
            "Step": metrics["Step"], "Vehicles": metrics["Vehicles"],
            "Average speed (m/s)": metrics["Average speed (m/s)"],
            "Queue total": metrics["Queue total"], "Congestion": metrics["Congestion"]
        })
        st.session_state["total_departed"] = traci.simulation.getDepartedNumber()
    if st.session_state["history"]:
        st.session_state["last_metrics"] = collect_metrics()

init_state()

st.title("🚦 RoadGuard")
st.caption("AI-powered road monitoring | SUMO traffic simulation + Streamlit operations dashboard")
with st.sidebar:
    st.header("Simulation controls")
    use_gui = st.checkbox("Open SUMO visual interface", value=False, help="Optional. Streamlit can run the simulation without the SUMO GUI.")
    steps = st.slider("Steps per run", min_value=10, max_value=500, value=100, step=10)
    st.session_state["mitigation_enabled"] = st.toggle("Enable adaptive signal mitigation", value=st.session_state["mitigation_enabled"])
    st.selectbox("Controlled junction", options=["B"], key="tls_id")
    start_col, reset_col = st.columns(2)
    if start_col.button("▶ Start / Resume", use_container_width=True):
        try:
            if not st.session_state["sumo_started"]:
                start_sumo(use_gui)
            run_steps(steps)
        except Exception as exc:
            st.session_state["last_error"] = str(exc)
    if reset_col.button("↻ Reset", use_container_width=True):
        close_sumo()
        for key in ("history", "events"):
            st.session_state[key] = []
        st.session_state["step"] = 0
        st.session_state["last_error"] = ""
        st.session_state["last_metrics"] = None
    if st.button("Run next batch", use_container_width=True):
        try:
            run_steps(steps)
        except Exception as exc:
            st.session_state["last_error"] = str(exc)
    st.markdown("---")
    st.markdown("**Demo scenario**")
    st.write("A–B–D is the main route. A–C–D provides an alternate path. Junction B is signal-controlled.")
    st.caption("Tip: run several batches to build a performance trend.")

if st.session_state["last_error"]:
    st.error(st.session_state["last_error"])

if not NET_FILE.exists():
    ok, msg = ensure_network()
    if ok:
        st.success(msg)
    else:
        st.warning(msg)

metrics = st.session_state.get("last_metrics")
if metrics is None:
    metrics = {"Vehicles": 0, "Average speed (m/s)": 0.0, "Queue total": 0, "Congestion": "NOT STARTED", "Edges": pd.DataFrame(columns=["Edge", "Vehicles", "Queue", "Mean speed (m/s)"])}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vehicles in network", metrics["Vehicles"])
c2.metric("Average speed", f'{metrics["Average speed (m/s)"]:.1f} m/s', f'{metrics["Average speed (m/s)"]*3.6:.1f} km/h')
c3.metric("Queued vehicles", metrics["Queue total"])
c4.metric("Congestion status", metrics["Congestion"])

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Network edge status")
    edge_df = metrics["Edges"]
    if not edge_df.empty:
        st.dataframe(edge_df, use_container_width=True, hide_index=True)
        st.bar_chart(edge_df.set_index("Edge")[["Queue"]])
    else:
        st.info("Start the simulation to populate live edge metrics.")
with right:
    st.subheader("Traffic performance")
    history = pd.DataFrame(st.session_state["history"])
    if not history.empty:
        st.line_chart(history.set_index("Step")[["Vehicles", "Queue total"]])
        st.line_chart(history.set_index("Step")[["Average speed (m/s)"]])
    else:
        st.info("Run a batch of simulation steps to generate charts.")
    st.subheader("RoadGuard event log")
    events = pd.DataFrame(st.session_state["events"])
    if not events.empty:
        st.dataframe(events.tail(12), use_container_width=True, hide_index=True)
    else:
        st.write("No events yet.")

st.markdown("---")
st.subheader("Evaluation checklist")
st.markdown("""
- **Detection:** congestion level derived from simulated queue length and speed.
- **Mitigation:** green-phase extension when a congested incoming approach is served by the current green.
- **Evaluation:** compare queue length and average speed with mitigation enabled and disabled under the same demand.
- **Scope note:** this first milestone controls signals; automated rerouting and the road-quality/accident modules are planned extensions.
""")
