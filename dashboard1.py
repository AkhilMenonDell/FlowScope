import streamlit as st
import requests
from datetime import datetime
from collections import Counter
import time

st.set_page_config(page_title="Control-M Dashboard", layout="wide")
API_BASE = "http://localhost:8000/api"

JOB_MAP = {
    "DEV": [
        "D1_PPE_FETCHEXPID", "D1_PPE_INSERT", "D1_PPE_EXEC_DCOS", "D1_PPE_EXEC_STBL",
        "D1_PPE_EXEC_STBL_HIST", "D1_PPE_EXEC_RAW", "D1_PPE_EXEC_RAW_DQ",
        "D1_PPE_EXEC_RAW_FUNC", "D1_PPE_EXEC_DAILY", "D1_PPE_EXEC_DAILY_DQ",
        "D1_PPE_DELETE_PRIMARY", "D1_PPE_EXEC_PRIMARY", "D1_PPE_EXEC_DB_REFRESH",
        "D1_PPE_EXEC_PRIMARY_DQ", "D1_PPE_PRIMARY_FUNC", "D1_PPE_EXEC_POD-3", "D1_PPE_MONITORANDDELETE",
        "D1_PPE_BASELINE_STATUSUPDATE", "D1_PPE_REFRESH_DAILY_STACKED", "D1_PPE_REFRESH_VCCM_DAILYSTACK",
        "D1_PPE_REFRESH_WEEKLYSTACKED", "D1_PPE_REFRESH_VCCM_WEEKLYSTACKED", "D1_PPE_REFRESH_BUILDPLAN",
        "D1_PPE_REFRESH_BASELINEPURGE"
    ],
    "UAT": [
        "Q1_PPE_FETCHEXPID", "Q1_PPE_INSERT", "Q1_PPE_EXEC_DCOS", "Q1_PPE_EXEC_STBL",
        "Q1_PPE_EXEC_STBL_HIST", "Q1_PPE_EXEC_RAW", "Q1_PPE_EXEC_RAW_DQ",
        "Q1_PPE_EXEC_RAW_FUNC", "Q1_PPE_EXEC_DAILY", "Q1_PPE_EXEC_DAILY_DQ",
        "Q1_PPE_DELETE_PRIMARY", "Q1_PPE_EXEC_PRIMARY", "Q1_PPE_EXEC_DB_REFRESH",
        "Q1_PPE_EXEC_PRIMARY_DQ", "Q1_PPE_PRIMARY_FUNC", "Q1_PPE_EXEC_POD-3", "Q1_PPE_MONITORANDDELETE",
        "Q1_PPE_BASELINE_STATUSUPDATE", "Q1_PPE_REFRESH_DAILY_STACKED", "Q1_PPE_REFRESH_VCCM_DAILYSTACK",
        "Q1_PPE_REFRESH_WEEKLYSTACKED", "Q1_PPE_REFRESH_VCCM_WEEKLYSTACKED", "Q1_PPE_REFRESH_BUILDPLAN",
        "Q1_PPE_REFRESH_BASELINEPURGE"
    ],
    "PROD": [
        "PPE_FETCHEXPID", "PPE_INSERT", "PPE_EXEC_DCOS", "PPE_EXEC_STBL",
        "PPE_EXEC_STBL_HIST", "PPE_EXEC_COMMAND-1", "PPE_EXEC_DQ_COMMAND-1",
        "PPE_EXEC_FUNC_COMMAND-1", "PPE_EXEC_COMMAND-2", "PPE_EXEC_DQ_COMMAND-2",
        "PPE_EXEC_COMMAND-3", "PPE_EXEC_DQ_COMMAND-3", "PPE_EXEC_FUNC_COMMAND-1",
        "PPE_EXEC_POD-3", "PPE_MONITORANDDELETE", "PPE_BASELINE_STATUSUPDATE", "PPE_REFRESH_DAILY_STACKED",
        "PPE_REFRESH_VCCM_DAILYSTACK", "PPE_REFRESH_WEEKLYSTACKED", "PPE_REFRESH_VCCM_WEEKLYSTACKED",
        "PPE_REFRESH_BUILDPLAN", "PPE_REFRESH_BASELINEPURGE"
    ]
}

FOLDER_MAP = {
    "DEV": ["D1_PPE_BASELINE", "D1_PPE_BASELINE-0700"],
    "QA": "Q1_PPE_BASELINE",
    "PROD": "PPE_BASELINE-0200"
}

JOB_LABEL_MAP = {
    "FETCHEXPID": "FETCH EXP ID",
    "INSERT": "INSERT EXP ID",
    "EXEC_DCOS": "DCOS",
    "EXEC_STBL": "STBL",
    "EXEC_STBL_HIST": "STBL HISTORIC",
    "EXEC_RAW": "RAW",
    "EXEC_COMMAND-1": "RAW",
    "EXEC_RAW_DQ": "RAW DQ",
    "EXEC_DQ_COMMAND-1": "RAW DQ",
    "EXEC_RAW_FUNC": "RAW FUNC VAL",
    "EXEC_FUNC_COMMAND-1": "RAW FUNC VAL",
    "EXEC_DAILY": "DAILY",
    "EXEC_COMMAND-2": "DAILY",
    "EXEC_DAILY_DQ": "DAILY DQ",
    "EXEC_DQ_COMMAND-2": "DAILY DQ",
    "DELETE_PRIMARY": "PRIMARY DELETE",
    "EXEC_PRIMARY": "PRIMARY",
    "EXEC_COMMAND-3": "PRIMARY",
    "EXEC_DB_REFRESH": "DB REFRESH",
    "EXEC_PRIMARY_DQ": "PRIMARY DQ",
    "EXEC_DQ_COMMAND-3": "PRIMARY DQ",
    "PRIMARY_FUNC": "PRIMARY FUNC VAL",
    "EXEC_FUNC_COMMAND-1": "PRIMARY FUNC VAL",
    "EXEC_POD-3": "POD-3",
    "MONITORANDDELETE": "MONITOR AND DELETE",
    "BASELINE_STATUSUPDATE": "UPDATE POD STATUS",
    "REFRESH_DAILY_STACKED": "REPORT REFRESH",
    "REFRESH_VCCM_DAILYSTACK": "REPORT REFRESH",
    "REFRESH_WEEKLYSTACKED": "REPORT REFRESH",
    "REFRESH_VCCM_WEEKLYSTACKED": "REPORT REFRESH",
    "REFRESH_BUILDPLAN": "REPORT REFRESH",
    "REFRESH_BASELINEPURGE": "REPORT REFRESH"
}

def get_label(jobname: str) -> str:
    for key, label in JOB_LABEL_MAP.items():
        if key in jobname:
            return label
    return "Unknown"


# --- Sidebar UI for filters ---
with st.sidebar:
    st.markdown("### 🔎 Experiment ID Filter")
    env = st.selectbox("🌐 Select Environment", options=["DEV", "UAT", "PROD"])
    date_input = st.date_input("📅 Simulation Date", datetime.today())
    date_str_pg = date_input.strftime("%Y-%m-%d")
    date_str_job = date_input.strftime("%y%m%d")

    if st.button("🔍 Fetch Experiment IDs"):
        with st.spinner("Fetching experiment IDs..."):
            try:
                resp = requests.get(f"{API_BASE}/experiments", params={"date": date_str_pg})
                data = resp.json()
                st.session_state.experiment_ids = [exp["experiment_id"] for exp in data]
                st.success("✅ Fetched Experiment IDs")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.experiment_ids = []

    if "experiment_ids" in st.session_state and st.session_state.experiment_ids:
        # st.markdown("#### 🧪 Experiment IDs")
        for exp_id in st.session_state.experiment_ids:
            st.code(exp_id, language="text")

# --- Main Dashboard ---
st.title("🧭 Control-M FlowScope Dashboard")
st.subheader("📊 Job Statuses")

if st.button("📦 Fetch Job Statuses"):
    jobnames = JOB_MAP.get(env, [])
    # folder = FOLDER_MAP.get(env)

    status_counter = Counter()
    job_statuses = {}

    # --- KPI Area ---
    st.markdown("### 📈 Stage Status Overview")
    kpi_container = st.container()
    col1, col2, col3, col4 = kpi_container.columns(4)
    kpi1 = col1.empty()
    kpi2 = col2.empty()
    kpi3 = col3.empty()
    kpi4 = col4.empty()

    # --- Progress bars container ---
    st.markdown("### 🧾 Detailed Stage Results")
    bar_container = st.container()

    stage_placeholders = [bar_container.empty() for _ in jobnames]

    for i, jobname in enumerate(jobnames):
        stage = stage_placeholders[i]

        with stage:
            row = st.container()
            col1, col2, col3 = row.columns([2, 4, 2])  # stage name | bar | status
            label = get_label(jobname)
            stage_label = f"**🔹 Stage {i+1}: `{label}` (`{jobname}`)**"

            try:
                folders = FOLDER_MAP.get(env, [])

                def get_preferred_status(jobname: str, folders: list, date_str_job: str):
                    results = []
                    for folder in folders:
                        try:
                            resp = requests.get(f"{API_BASE}/job_status", params={
                                "limit": 1000,
                                "jobname": jobname,
                                "folder": folder,
                                "historyRunDate": date_str_job
                            })
                            resp.raise_for_status()
                            result = resp.json()
                            if result and isinstance(result, list) and result[0].get("status"):
                                results.append({"folder": folder, "status": result[0]["status"]})
                        except Exception:
                            results.append({"folder": folder, "status": "Error"})

                    # Priority Logic
                    for r in results:
                        if "Ended OK" in r["status"]:
                            return r["status"], r["folder"]
                    for r in results:
                        if "Wait Condition" in r["status"] or "Running" in r["status"]:
                            return r["status"], r["folder"]
                    return results[0]["status"] if results else "Unknown", results[0]["folder"] if results else "N/A"

                status, source_folder = get_preferred_status(jobname, folders, date_str_job)
                job_statuses[jobname] = status


                if "Ended OK" in status:
                    status_counter["Completed"] += 1
                    color = "#28a745"
                    icon = "✅"
                elif "Wait Condition" in status or "Running" in status:
                    status_counter["Running"] += 1
                    color = "#ffc107"
                    icon = "🕐"
                elif "Ended Not OK" in status:
                    status_counter["Failed"] += 1
                    color = "#dc3545"
                    icon = "❌"
                else:
                    status_counter["Pending"] += 1
                    color = "#6c757d"
                    icon = "⚠️"

                # Display stage name
                col1.markdown(stage_label)

                # Horizontal bar
                bar_html = f"""
                    <div style="height: 16px; width: 100%; background-color: #e0e0e0; border-radius: 5px;">
                        <div style="height: 100%; width: 100%; background-color: {color}; border-radius: 5px;"></div>
                    </div>
                """
                col2.markdown(bar_html, unsafe_allow_html=True)

                # Status
                # col3.markdown(f"<span style='font-size: 16px;'>{icon} {status}</span>", unsafe_allow_html=True)
                col3.markdown(f"<span style='font-size: 16px;'>{icon} {status} <br/><small><i>({source_folder})</i></small></span>", unsafe_allow_html=True)


            except Exception as e:
                status_counter["Pending"] += 1
                col1.markdown(stage_label)
                col2.markdown("")  # empty bar
                col3.error(f"❌ Error: {e}")

            # --- Update KPI metrics ---
            total = len(jobnames)
            completed = status_counter["Completed"]
            running = status_counter["Running"]
            failed = status_counter["Failed"]
            pending = total - (completed + running + failed)
            progress = round((completed / total) * 100, 2)

            kpi1.metric("Overall Progress", f"{progress}%")
            kpi2.metric("✅ Completed", f"{completed}/{total}")
            kpi3.metric("🚀 Running", str(running))
            kpi4.metric("❌ Failed", str(failed))

        




