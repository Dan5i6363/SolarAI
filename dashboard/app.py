"""Mentor-ready SolarAI dashboard; safe by default in demo mode."""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import streamlit as st
from integration import assess, run_demo
from simulation.data_sources import CSVSource

st.set_page_config(page_title="SolarAI monitor", page_icon=":material/solar_power:", layout="wide")
st.session_state.setdefault("replay_index", 0); st.session_state.setdefault("history", [])
SCENARIOS = ["Normal", "Low Irradiance", "Partial Shading", "Soiling/Dust", "Possible Fault"]
@st.cache_data
def metadata(): return json.loads((ROOT / "models/model_metadata.json").read_text())
def reset(): st.session_state.replay_index=0; st.session_state.history=[]

with st.sidebar:
    st.header("Controls")
    source_mode=st.selectbox("Data source",["Demo / synthetic","CSV replay"])
    scenario=st.selectbox("Simulated PV condition",SCENARIOS)
    upload=st.file_uploader("CSV telemetry replay",type="csv",disabled=source_mode!="CSV replay")
    advance=st.button("Advance replay",icon=":material/play_arrow:")
    st.button("Reset replay",icon=":material/restart_alt:",on_click=reset)
    st.caption("Hardware mode not connected. Webcam is optional; CV has a demo-image fallback.")
view=st.segmented_control("View",["Monitor","Architecture","About the model"],default="Monitor")
st.title("SolarAI PV + MPPT monitor")
st.warning("Simulation / Demo mode: values and AI results are synthetic unless CSV replay is selected; they are not hardware measurements.")

if view=="Architecture":
    st.subheader("System architecture")
    st.code("PV / MPPT → Monitoring → AI + heuristic CV → Decision → LoRa protocol simulation → Dashboard")
    st.write("The communication layer uses CRC32 in a software simulation; it does not claim RF transmission.")
elif view=="About the model":
    meta=metadata(); metrics=json.loads((ROOT/"models/training_metrics.json").read_text())
    st.subheader(meta["model_type"]); st.caption(f"Model version {meta['version']}")
    st.write("Features:",", ".join(meta["features"])); st.warning(meta["disclaimer"])
    st.metric("Held-out synthetic accuracy",f"{metrics['test_accuracy']:.1%}")
    st.image(str(ROOT/"models/confusion_matrix.png"),caption="Synthetic-data confusion matrix")
else:
    if source_mode=="CSV replay" and upload:
        replay_path=ROOT/"data"/"_dashboard_replay.csv"; replay_path.write_bytes(upload.getvalue()); source=CSVSource(replay_path); source.index=st.session_state.replay_index; measurement=source.read(); label="CSV replay"
    else:
        measurement=run_demo(scenario,seed=42+st.session_state.replay_index)["measurement"]; label="Demo / synthetic"
    if advance: st.session_state.replay_index+=1; st.rerun()
    result=assess(measurement); m=result["measurement"]
    st.caption(f"Data source: {label} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Model {metadata()['version']}")
    with st.container(horizontal=True):
        for name,value in [("Irradiance",f"{m['irradiance']} W/m²"),("Voltage",f"{m['voltage']} V"),("Current",f"{m['current']} A"),("Power",f"{m['power']} W"),("MPPT reference",f"{m['mppt_reference_voltage']} V")]: st.metric(name,value,border=True)
    st.session_state.history.append({"sample":len(st.session_state.history)+1,"power":m["power"],"voltage":m["voltage"],"irradiance":m["irradiance"]}); st.session_state.history=st.session_state.history[-30:]
    left,right=st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader(f"System status: {result['status']}"); st.write(f"Severity: **{result['severity']}**"); st.metric("AI confidence",f"{result['confidence']:.1%}"); st.write("Recommendation:",result["recommended_action"])
    with right:
        with st.container(border=True):
            st.subheader("Visual monitoring"); st.write(f"CV status: **{result['cv']['visual_condition']}**"); st.caption("Heuristic panel-region/brightness analysis only; not trained visual fault detection."); st.image(result["cv"]["annotated_image"],channels="BGR",caption="Demo panel fallback")
    with st.container(border=True): st.subheader("Telemetry replay trends"); st.line_chart(pd.DataFrame(st.session_state.history).set_index("sample"))
