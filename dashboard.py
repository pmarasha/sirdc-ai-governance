import os
import csv
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# ---------- Config ----------
st.set_page_config(
    page_title="SIRDC AI Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SIRDC_BLUE = "#003366"
SIRDC_GREEN = "#1B7A3E"
SIRDC_GOLD = "#C8A415"
SIRDC_RED = "#B22222"
SIRDC_ORANGE = "#E67E22"

RISK_COLORS = {
    "Prohibited": "#8B0000",
    "High": SIRDC_RED,
    "Limited": SIRDC_ORANGE,
    "Minimal": SIRDC_GREEN,
    "Pending": "#9CA3AF",
}

SEVERITY_COLORS = {
    "Low": "#2E8B57",
    "Medium": "#E67E22",
    "High": "#B22222",
    "Critical": "#8B0000",
}

CSV_FILE = "ai_inventory.csv"
INCIDENTS_FILE = "incidents.csv"

INSTITUTES = [
    "ICT", "Agriculture", "Health", "Manufacturing", "Energy",
    "Mining", "Corporate Services", "Finance", "HR",
    "Legal", "Communications", "Research",
]

MODEL_TYPES = ["LLM", "ML model", "Computer vision", "Time series",
               "Deep learning", "Other"]

DATA_TYPES = [
    "Internal documents", "Public data", "Personal data",
    "Confidential research", "Medical data", "Financial records",
    "Biometric data", "Sensor data", "Camera images", "Other",
]

RISK_CATEGORIES = [
    "AI & Model Risk", "Cybersecurity Risk", "Legal & Compliance Risk",
    "Third Party Risk", "Reputation Risk", "Operational Risk",
]

INCIDENT_TYPES = [
    "Bias or unfair output",
    "Harmful or offensive output",
    "Incorrect / misleading result",
    "Data privacy breach",
    "Security incident",
    "System outage or failure",
    "Unauthorised use",
    "Unexpected behaviour",
    "Other",
]

CSV_COLUMNS = [
    "id", "name", "description", "owner", "department", "institute",
    "purpose", "data_types", "model_type", "vendor", "users",
    "risk_tier", "status", "last_review", "next_review",
    "controls", "incidents",
]

INCIDENT_COLUMNS = [
    "incident_id", "system_name", "system_owner", "institute",
    "incident_type", "severity", "date_occurred", "date_reported",
    "reported_by", "reported_email",
    "description", "harm_occurred", "immediate_action",
    "status",
]

# ---------- CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {display: none !important;}
    button[data-testid="collapsedControl"] {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden;}

    div[data-testid="stImage"] {margin: 0 !important; padding: 0 !important;}
    div[data-testid="stImage"] > img {display: block; margin: 0 auto;}
    div[data-testid="stMarkdownContainer"] {margin: 0 !important;}
    div[data-testid="stVerticalBlock"] > div:first-child {gap: 0 !important;}

    /* ===== Modern hero bar ===== */
    .sirdc-hero {
        background: linear-gradient(135deg, #003366 0%, #004a99 60%, #1B7A3E 130%);
        color: #FFFFFF;
        padding: 22px 32px 20px 32px;
        border-radius: 0;
        margin: -1rem -2rem 24px -2rem;
        text-align: center;
        position: relative;
    }
    .sirdc-hero .hero-logo {
        display: block;
        margin: 0 auto 12px auto;
        width: 110px;
        background: #FFFFFF;
        padding: 6px 10px;
        border-radius: 6px;
    }
    .sirdc-hero h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.1;
    }
    .sirdc-hero .hero-sub {
        color: #D6E4F0;
        font-size: 0.98rem;
        font-weight: 400;
        margin: 6px 0 0 0;
        letter-spacing: 0.005em;
    }
    .sirdc-hero .hero-meta {
        color: #9CB8D1;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 8px 0 0 0;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .sirdc-hero .hero-meta b {
        color: #FFFFFF;
        font-weight: 600;
    }

    /* ===== Sticky tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
        gap: 4px;
        padding-top: 8px;
        padding-bottom: 0;
        margin-top: -8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 16px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        font-weight: 500;
        color: #4B5563;
    }
    .stTabs [aria-selected="true"] {
        color: #003366 !important;
        border-bottom: 2px solid #003366 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #003366;
        border-radius: 6px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] > div {
        font-size: 0.82rem; color: #4B5563; font-weight: 600;
        letter-spacing: 0.04em; text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] > div {
        font-size: 1.9rem; color: #003366; font-weight: 700;
    }

    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #003366;
        font-weight: 700;
        letter-spacing: -0.015em;
    }
    h2 {font-size: 1.15rem;}
    h3 {font-size: 1rem;}

    div[data-testid="stDataFrame"] {border: 1px solid #E5E7EB; border-radius: 6px;}
    .stButton > button {
        border-radius: 6px; border: 1px solid #003366;
        color: #003366; background: #FFFFFF; font-weight: 500;
    }
    .stButton > button:hover {background: #003366; color: #FFFFFF;}
    div[data-testid="stAlert"] {border-radius: 6px;}
    details {border-radius: 6px; border: 1px solid #E5E7EB; padding: 4px 8px;}

    @media print {
        section[data-testid="stSidebar"], .stTabs [data-baseweb="tab-list"],
        .stButton, .stDownloadButton, div[data-testid="stChatInput"],
        header[data-testid="stHeader"], #MainMenu, footer {display: none !important;}
        .stApp, .block-container, body {background: #FFFFFF !important;}
        .block-container {padding: 0.5rem 0 !important; max-width: 100% !important;}
        .sirdc-hero {
            background: #003366 !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        div[data-testid="stMetric"], div[data-testid="stDataFrame"], .stPlotlyChart {
            page-break-inside: avoid; break-inside: avoid;
        }
        div[data-testid="stMetric"] {box-shadow: none !important;}
        .stTabs [data-baseweb="tab-panel"] {display: block !important; padding-top: 0 !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- LLM setup (Gemini) ----------
load_dotenv()
POLICY_FILE = "ai_policy.md"
LOG_FILE = "policy_audit_log.csv"


def get_policy_text() -> str:
    if Path(POLICY_FILE).exists():
        return Path(POLICY_FILE).read_text(encoding="utf-8")
    return ""


def log_interaction(question: str, answer: str) -> None:
    new_file = not Path(LOG_FILE).exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "question", "answer"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            question.replace("\n", " "),
            answer.replace("\n", " "),
        ])


def ask_policy(question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ("Gemini API key not configured. Add GEMINI_API_KEY to your "
                ".env file or Streamlit Secrets.")
    policy_text = get_policy_text()
    if not policy_text:
        return f"Policy file '{POLICY_FILE}' not found."

    client = genai.Client(api_key=api_key)

    system_prompt = f"""You are SIRDC's AI Governance Assistant.
Answer ONLY using the policy below. Cite section numbers like [Section 4.1].
If the answer is not in the policy, say:
"This is not covered in the policy. Recommend escalating to the AI Review Board."
Never invent rules. Keep answers under 120 words.

POLICY:
{policy_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{system_prompt}\n\nUser question: {question}",
        )
        answer = (response.text or "").strip()
    except Exception as e:
        return f"Error contacting Gemini: {e}"

    log_interaction(question, answer)
    return answer


# ---------- Data helpers ----------
def load_inventory() -> pd.DataFrame:
    df = pd.read_csv(CSV_FILE)
    df["incidents"] = df["incidents"].fillna("None")
    return df


def load_incidents() -> pd.DataFrame:
    if not Path(INCIDENTS_FILE).exists():
        return pd.DataFrame(columns=INCIDENT_COLUMNS)
    df = pd.read_csv(INCIDENTS_FILE)
    for col in INCIDENT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def next_inventory_id(df: pd.DataFrame) -> int:
    if len(df) == 0:
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").max()) + 1


def next_incident_id(df: pd.DataFrame) -> int:
    if len(df) == 0:
        return 1
    return int(pd.to_numeric(df["incident_id"], errors="coerce").max()) + 1


def _ensure_newline_before_append(path: str) -> None:
    if not Path(path).exists():
        return
    with open(path, "rb") as f:
        try:
            f.seek(-1, os.SEEK_END)
            last_byte = f.read(1)
        except OSError:
            return
    if last_byte not in (b"\n", b"\r"):
        with open(path, "a", newline="", encoding="utf-8") as f:
            f.write("\n")


def _sanitise(value) -> str:
    return str(value if value is not None else "").replace("\r", " ").replace("\n", " ").strip()


def append_system(row: dict) -> None:
    df = load_inventory()
    row["id"] = next_inventory_id(df)
    row_full = {col: _sanitise(row.get(col, "")) for col in CSV_COLUMNS}
    row_full["incidents"] = row_full.get("incidents") or "None"
    _ensure_newline_before_append(CSV_FILE)

    if Path(CSV_FILE).exists():
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=CSV_COLUMNS,
                quoting=csv.QUOTE_MINIMAL, lineterminator="\n",
            )
            writer.writerow(row_full)
    else:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=CSV_COLUMNS,
                quoting=csv.QUOTE_MINIMAL, lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(row_full)


def append_incident(row: dict) -> None:
    incidents = load_incidents()
    row["incident_id"] = next_incident_id(incidents)
    row_full = {col: _sanitise(row.get(col, "")) for col in INCIDENT_COLUMNS}
    _ensure_newline_before_append(INCIDENTS_FILE)

    if Path(INCIDENTS_FILE).exists():
        with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=INCIDENT_COLUMNS,
                quoting=csv.QUOTE_MINIMAL, lineterminator="\n",
            )
            writer.writerow(row_full)
    else:
        with open(INCIDENTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=INCIDENT_COLUMNS,
                quoting=csv.QUOTE_MINIMAL, lineterminator="\n",
            )
            writer.writeheader()
            writer.writerow(row_full)


def count_open_incidents(system_name: str = None) -> int:
    incidents = load_incidents()
    if len(incidents) == 0:
        return 0
    open_incidents = incidents[incidents["status"] != "Resolved"]
    if system_name:
        open_incidents = open_incidents[open_incidents["system_name"] == system_name]
    return len(open_incidents)


# ---------- Load data ----------
df = load_inventory()
incidents_df = load_incidents()
today = date.today().isoformat()

if "current_user" not in st.session_state:
    st.session_state.current_user = os.getenv("SIRDC_USER", "Governance Lead")

if "last_submission" not in st.session_state:
    st.session_state.last_submission = None

if "last_incident" not in st.session_state:
    st.session_state.last_incident = None


# ---------- Modern hero header ----------
logo_html = ""
if Path("logo.png").exists():
    import base64
    with open("logo.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img class="hero-logo" src="data:image/png;base64,{b64}" alt="SIRDC">'

st.markdown(
    f"""
    <div class="sirdc-hero">
        {logo_html}
        <h1>AI Governance Dashboard</h1>
        <p class="hero-sub">Real-time oversight of AI systems across all SIRDC institutes</p>
        <p class="hero-meta">
            {today} &nbsp;·&nbsp; Prepared by <b>{st.session_state.current_user}</b>
            &nbsp;·&nbsp; NIST AI RMF &nbsp;·&nbsp; ISO/IEC 42001
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Dashboard",
    "📝  Register AI System",
    "🚨  Report Incident",
    "🤖  Policy Assistant",
])

# ============ TAB 1: DASHBOARD ============
with tab1:
    with st.expander("🔎  Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        institutes = ["All"] + sorted(df["institute"].dropna().unique().tolist())
        risks = ["All", "Prohibited", "High", "Limited", "Minimal", "Pending"]
        statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())

        f_inst = fc1.selectbox("Institute", institutes)
        f_risk = fc2.selectbox("Risk tier", risks)
        f_status = fc3.selectbox("Status", statuses)
        fc4.text_input("Signed in as",
                       value=st.session_state.current_user,
                       key="user_field")

    fdf = df.copy()
    if f_inst != "All":
        fdf = fdf[fdf["institute"] == f_inst]
    if f_risk != "All":
        fdf = fdf[fdf["risk_tier"] == f_risk]
    if f_status != "All":
        fdf = fdf[fdf["status"] == f_status]

    total_open_incidents = count_open_incidents()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total AI Systems", len(fdf))
    c2.metric("High Risk", len(fdf[fdf["risk_tier"] == "High"]))
    c3.metric("Overdue Reviews", len(fdf[fdf["next_review"] < today]))
    c4.metric("Open Incidents", total_open_incidents)

    st.markdown("")

    left, right = st.columns(2)
    with left:
        st.subheader("Risk Distribution")
        rc = fdf["risk_tier"].value_counts().reset_index()
        rc.columns = ["Risk Tier", "Count"]
        fig = px.pie(rc, names="Risk Tier", values="Count",
                     color="Risk Tier", color_discrete_map=RISK_COLORS, hole=0.5)
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("AI Systems by Institute")
        ic = fdf["institute"].value_counts().reset_index()
        ic.columns = ["Institute", "Count"]
        fig = px.bar(ic, x="Count", y="Institute", orientation="h",
                     color="Count", color_continuous_scale="Blues")
        fig.update_layout(
            showlegend=False, yaxis=dict(autorange="reversed"),
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("")

    left2, right2 = st.columns(2)
    with left2:
        st.subheader("Lifecycle Stage")
        sc = fdf["status"].value_counts().reset_index()
        sc.columns = ["Status", "Count"]
        fig = px.bar(sc, x="Status", y="Count", color="Status",
                     color_discrete_sequence=[SIRDC_BLUE, SIRDC_GREEN, SIRDC_GOLD, SIRDC_ORANGE])
        fig.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right2:
        st.subheader("Risk by Institute")
        cross = fdf.groupby(["institute", "risk_tier"]).size().reset_index(name="Count")
        fig = px.bar(cross, x="institute", y="Count", color="risk_tier",
                     color_discrete_map=RISK_COLORS,
                     labels={"institute": "Institute", "risk_tier": "Risk Tier"})
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("⚠️  Systems Requiring Attention")
    overdue = fdf[fdf["next_review"] < today]
    high_risk = fdf[fdf["risk_tier"].isin(["High", "Prohibited"])]

    a1, a2, a3 = st.columns(3)
    with a1:
        if len(overdue) > 0:
            st.error(f"**{len(overdue)}** overdue review(s)")
        else:
            st.success("No overdue reviews")
    with a2:
        if len(high_risk) > 0:
            st.warning(f"**{len(high_risk)}** high-risk system(s)")
        else:
            st.info("No high-risk systems flagged")
    with a3:
        if total_open_incidents > 0:
            st.error(f"**{total_open_incidents}** open incident(s)")
        else:
            st.success("No open incidents")

    if len(overdue) > 0:
        st.dataframe(
            overdue[["name", "owner", "institute", "risk_tier", "next_review"]],
            use_container_width=True, hide_index=True,
        )

    st.divider()
    st.subheader("🚨 Incident Log")
    if len(incidents_df) == 0:
        st.info("No incidents have been reported yet.")
    else:
        display_cols = ["incident_id", "system_name", "institute",
                        "incident_type", "severity", "date_occurred",
                        "reported_by", "status"]
        st.dataframe(
            incidents_df[display_cols].sort_values(
                "incident_id", ascending=False
            ),
            use_container_width=True, hide_index=True,
        )

    st.divider()

    st.subheader("Full AI Inventory")
    st.dataframe(fdf, use_container_width=True, hide_index=True)

    csv_data = fdf.to_csv(index=False).encode("utf-8")
    st.download_button("⬇  Download Inventory (CSV)", csv_data,
                       "sirdc_ai_inventory.csv", "text/csv")

    st.markdown("")
    with st.expander("ℹ️  About this dashboard"):
        st.markdown(
            f"""
            **Purpose** — Provides real-time visibility into every AI system
            across SIRDC's institutes. Supports the AI Governance Framework, Phase 1.

            **Data source** — AI systems are registered via the
            "Register AI System" tab. Incidents are logged via the
            "Report Incident" tab.

            **Risk tiers** — Prohibited / High / Limited / Minimal / Pending,
            following NIST AI RMF and the EU AI Act.

            **Review cadence** — High-risk: every 6 months.
            Limited and minimal-risk: every 12 months.

            **Standards** — NIST AI RMF · ISO/IEC 42001 ·
            Zimbabwe National AI Strategy (2026–2030).

            **Policy Assistant** — Answers use only the SIRDC AI Policy document
            as its source, powered by Google Gemini. Every interaction is logged.
            It does not make binding decisions — escalate to the AI Review Board.

            **Version** — v2.0 · Phase 1 · {today}
            """
        )

# ============ TAB 2: REGISTER AI SYSTEM ============
with tab2:
    st.subheader("Register a New AI System")
    st.caption(
        "Complete this form to register a new AI system with the AI Governance Lead. "
        "Required fields are marked with an asterisk. "
        "You will be notified once the system is reviewed and a risk tier assigned."
    )

    if st.session_state.last_submission:
        st.success(
            f"✅ Registered **{st.session_state.last_submission}**. "
            "The AI Governance Lead will review and assign a risk tier."
        )
        if st.button("Submit another"):
            st.session_state.last_submission = None
            st.rerun()

    else:
        with st.form("register_form", clear_on_submit=False):
            r1c1, r1c2 = st.columns(2)
            name = r1c1.text_input("System name *", placeholder="e.g., Crop Yield Forecaster")
            institute = r1c2.selectbox("Institute *", INSTITUTES)

            r2c1, r2c2 = st.columns(2)
            owner = r2c1.text_input("Owner name *", placeholder="Full name")
            owner_email = r2c2.text_input("Owner email *", placeholder="name@sirdc.ac.zw")

            description = st.text_area(
                "Brief description *",
                placeholder="What does this system do, in one or two sentences?",
                height=80,
            )

            purpose = st.text_area(
                "Purpose / use case *",
                placeholder="Why is this system being deployed? What problem does it solve?",
                height=80,
            )

            r3c1, r3c2 = st.columns(2)
            model_type = r3c1.selectbox("Model type *", MODEL_TYPES)
            vendor = r3c2.text_input("Vendor / provider", placeholder="e.g., OpenAI, custom, internal")

            data_types = st.multiselect(
                "Data types used *",
                DATA_TYPES,
                help="Select all that apply. This determines the risk tier.",
            )

            users = st.text_input(
                "Who will use this system? *",
                placeholder="e.g., All staff, HR team, Farmers, Clinicians",
            )

            risk_category = st.selectbox(
                "Enterprise risk category",
                RISK_CATEGORIES,
                index=0,
                help="Defaults to AI & Model Risk. Aligns with SIRDC's enterprise risk register.",
            )

            st.markdown("---")

            agreed = st.checkbox(
                "I confirm the information provided is accurate and that this system "
                "will comply with the SIRDC AI Policy *"
            )

            submitted = st.form_submit_button("Submit registration", use_container_width=True)

            if submitted:
                errors = []
                if not name: errors.append("System name")
                if not owner: errors.append("Owner name")
                if not owner_email or "@" not in owner_email: errors.append("Owner email")
                if not description: errors.append("Brief description")
                if not purpose: errors.append("Purpose / use case")
                if not data_types: errors.append("Data types used")
                if not users: errors.append("Who will use this system")
                if not agreed: errors.append("Confirmation checkbox")

                if errors:
                    st.error("Please complete the following: " + ", ".join(errors))
                else:
                    row = {
                        "name": name,
                        "description": description,
                        "owner": owner,
                        "department": institute,
                        "institute": institute,
                        "purpose": purpose,
                        "data_types": "; ".join(data_types),
                        "model_type": model_type,
                        "vendor": vendor or "Not specified",
                        "users": users,
                        "risk_tier": "Pending",
                        "status": "Pending Review",
                        "last_review": today,
                        "next_review": "",
                        "controls": "Pending review",
                        "incidents": "None",
                    }
                    append_system(row)
                    st.session_state.last_submission = name
                    st.rerun()

    st.divider()

    with st.expander("ℹ️  What happens after submission?"):
        st.markdown(
            """
            **1. Automatic entry** — The system is added to the AI Inventory
            with status `Pending Review` and risk tier `Pending`.

            **2. Governance Lead review** — Within 48 hours, the AI Governance
            Lead reviews the submission and assigns a risk tier:
            - **Prohibited** → System cannot proceed
            - **High** → Escalated to the AI Review Board
            - **Limited** or **Minimal** → Approved with conditions

            **3. Review cadence set** — High-risk systems reviewed every 6 months.
            Limited and minimal-risk every 12 months.

            **4. Notifications** — You and the AI Governance Lead receive
            email confirmations (Phase 2 feature).

            **5. Compliance** — The system now appears on the management
            dashboard and is subject to SIRDC AI Policy.
            """
        )

# ============ TAB 3: REPORT INCIDENT ============
with tab3:
    st.subheader("Report an AI Incident")
    st.caption(
        "Use this form to report any harm, bias, error, or unexpected behaviour "
        "from an SIRDC AI system. Reports go directly to the AI Governance Lead. "
        "Every report is logged and tracked to resolution."
    )

    if st.session_state.last_incident:
        st.success(
            f"✅ Incident **#{st.session_state.last_incident}** reported. "
            "The AI Governance Lead has been notified and will review within 24 hours."
        )
        if st.button("Report another"):
            st.session_state.last_incident = None
            st.rerun()

    else:
        system_options = sorted(df["name"].dropna().unique().tolist())

        if len(system_options) == 0:
            st.warning("No AI systems are registered yet. Please register a system first.")
        else:
            with st.form("incident_form", clear_on_submit=False):
                system_name = st.selectbox(
                    "Which AI system? *",
                    options=system_options,
                    help="Pick the system where the incident occurred.",
                )

                incident_type = st.selectbox(
                    "What type of incident? *",
                    INCIDENT_TYPES,
                )

                col_sev1, col_sev2 = st.columns(2)
                severity = col_sev1.radio(
                    "Severity *",
                    ["Low", "Medium", "High", "Critical"],
                    horizontal=True,
                    help="Low = minor annoyance. Critical = serious harm or regulatory breach.",
                )
                date_occurred = col_sev2.date_input(
                    "Date it happened *",
                    value=date.today(),
                )

                description = st.text_area(
                    "What happened? *",
                    placeholder="Describe the incident clearly. Include what you observed, "
                                "who was affected, and any evidence.",
                    height=140,
                )

                harm_occurred = st.radio(
                    "Did any harm occur? *",
                    ["No", "Yes - minor", "Yes - significant", "Not sure"],
                    horizontal=True,
                )

                immediate_action = st.text_area(
                    "Immediate action taken (optional)",
                    placeholder="e.g., Stopped using the system, informed supervisor, submitted bug report.",
                    height=80,
                )

                st.markdown("**Your details**")
                col_r1, col_r2 = st.columns(2)
                reported_by = col_r1.text_input("Your name *", placeholder="Full name")
                reported_email = col_r2.text_input("Your email *", placeholder="name@sirdc.ac.zw")

                st.markdown("---")

                confirmed = st.checkbox(
                    "I confirm this report is accurate to the best of my knowledge *"
                )

                submitted = st.form_submit_button(
                    "Submit incident report",
                    use_container_width=True,
                )

                if submitted:
                    errors = []
                    if not system_name: errors.append("System")
                    if not description: errors.append("Incident description")
                    if not reported_by: errors.append("Your name")
                    if not reported_email or "@" not in reported_email:
                        errors.append("Your email")
                    if not confirmed: errors.append("Confirmation checkbox")

                    if errors:
                        st.error("Please complete the following: " + ", ".join(errors))
                    else:
                        row_sys = df[df["name"] == system_name]
                        sys_owner = row_sys.iloc[0]["owner"] if len(row_sys) else ""
                        sys_inst = row_sys.iloc[0]["institute"] if len(row_sys) else ""

                        row = {
                            "system_name": system_name,
                            "system_owner": sys_owner,
                            "institute": sys_inst,
                            "incident_type": incident_type,
                            "severity": severity,
                            "date_occurred": date_occurred.isoformat(),
                            "date_reported": today,
                            "reported_by": reported_by,
                            "reported_email": reported_email,
                            "description": description,
                            "harm_occurred": harm_occurred,
                            "immediate_action": immediate_action or "None recorded",
                            "status": "Open",
                        }
                        append_incident(row)
                        st.session_state.last_incident = next_incident_id(load_incidents()) - 1
                        st.rerun()

    st.divider()

    with st.expander("ℹ️  What happens after you report?"):
        st.markdown(
            """
            **1. Immediate log** — Your report is logged with a unique incident ID.

            **2. Governance Lead notified** — Within 24 hours, the AI Governance
            Lead reviews the report and categorises it:
            - **Low severity** — Logged for monthly review
            - **Medium** — Assigned to the Model Owner for investigation
            - **High / Critical** — Escalated to the AI Review Board

            **3. System status** — The AI system is flagged on the management
            dashboard until the incident is resolved.

            **4. Investigation** — The Model Owner investigates and proposes
            corrective action. You may be contacted for more detail.

            **5. Resolution** — Once resolved, the incident is marked `Resolved`
            and remains in the audit log permanently.

            **6. Privacy** — Your name and email are visible only to the
            AI Governance Lead and the AI Review Board.
            """
        )

# ============ TAB 4: POLICY ASSISTANT ============
with tab4:
    st.subheader("AI Policy Assistant")
    st.caption(
        "Ask any question about SIRDC's AI Policy. Answers cite the relevant "
        "section and every interaction is logged for audit."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("**Suggested questions**")
    suggestions = [
        "Can I send employee salaries to ChatGPT?",
        "What is the review cadence for a facial recognition system?",
        "Can I use anonymised patient data to train a model?",
        "Do I need approval to buy a third-party AI tool?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sugg_{i}", use_container_width=True):
            st.session_state.chat_history.append(("user", s))
            with st.spinner("Consulting policy..."):
                ans = ask_policy(s)
            st.session_state.chat_history.append(("assistant", ans))

    st.divider()

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    question = st.chat_input("Ask a policy question...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Consulting policy..."):
                answer = ask_policy(question)
            st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))

# ---------- Footer ----------
st.markdown(
    "<hr style='border:1px solid #E5E7EB; margin-top:24px;'>"
    "<p style='text-align:center; color:#9CA3AF; font-size:12px; margin:0;'>"
    "SIRDC AI Governance Framework · v2.0 · Aligned with NIST AI RMF and ISO/IEC 42001 · Internal use only"
    "</p>",
    unsafe_allow_html=True,
)