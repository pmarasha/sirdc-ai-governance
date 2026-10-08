import os
import csv
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

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
}

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px;}

    /* Hide the sidebar completely */
    section[data-testid="stSidebar"] {display: none !important;}
    button[data-testid="collapsedControl"] {display: none !important;}

    /* Kill the default gap Streamlit adds around images */
    div[data-testid="stImage"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    div[data-testid="stImage"] > img {
        display: block;
        margin: 0 auto;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #003366;
        border-radius: 6px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] > div {
        font-size: 0.85rem; color: #4B5563; font-weight: 500;
        letter-spacing: 0.02em; text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] > div {
        font-size: 1.9rem; color: #003366; font-weight: 700;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #003366; font-weight: 600; letter-spacing: -0.01em;
    }
    .stTabs [data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid #E5E7EB;}
    .stTabs [data-baseweb="tab"] {padding: 10px 18px; font-weight: 500; color: #4B5563;}
    .stTabs [aria-selected="true"] {
        color: #003366 !important; border-bottom: 2px solid #003366 !important;
    }
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

# ---------- LLM setup ----------
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key not configured. Add OPENAI_API_KEY to your .env file."
    policy_text = get_policy_text()
    if not policy_text:
        return f"Policy file '{POLICY_FILE}' not found."
    client = OpenAI(api_key=api_key)
    system_prompt = f"""You are SIRDC's AI Governance Assistant.
Answer ONLY using the policy below. Cite section numbers like [Section 4.1].
If the answer is not in the policy, say:
"This is not covered in the policy. Recommend escalating to the AI Review Board."
Never invent rules. Keep answers under 120 words.

POLICY:
{policy_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
    )
    answer = response.choices[0].message.content.strip()
    log_interaction(question, answer)
    return answer


# ---------- Load data ----------
df = pd.read_csv("ai_inventory.csv")
df["incidents"] = df["incidents"].fillna("None")
today = date.today().isoformat()

if "current_user" not in st.session_state:
    st.session_state.current_user = os.getenv("SIRDC_USER", "Governance Lead")

# ---------- Header (centered, compact) ----------
# Logo — fixed width, centered, with tight margins
logo_col1, logo_col2, logo_col3 = st.columns([2, 1, 2])
with logo_col2:
    if Path("logo.png").exists():
        st.image("logo.png", width=180)

# Title and subtitle centered
st.markdown(
    f"""
    <div style='text-align: center; border-bottom: 3px solid {SIRDC_BLUE};
                padding-bottom: 12px; margin-top: -20px; margin-bottom: 18px;'>
        <h1 style='color:{SIRDC_BLUE}; margin: 0; font-size: 1.8rem;'>
            AI Governance Dashboard
        </h1>
        <p style='color:#6B7280; margin: 4px 0 0 0; font-size: 0.9rem;'>
            Real-time oversight of AI systems across all SIRDC institutes
        </p>
        <p style='color:#9CA3AF; margin: 2px 0 0 0; font-size: 0.8rem;'>
            {today} &nbsp;·&nbsp; Prepared by <b>{st.session_state.current_user}</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["📊  Dashboard", "🤖  Policy Assistant"])

# ============ TAB 1 ============
with tab1:
    # --- Compact filter bar ---
    with st.expander("🔎  Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        institutes = ["All"] + sorted(df["institute"].unique().tolist())
        risks = ["All", "Prohibited", "High", "Limited", "Minimal"]
        statuses = ["All"] + sorted(df["status"].unique().tolist())

        f_inst = fc1.selectbox("Institute", institutes)
        f_risk = fc2.selectbox("Risk tier", risks)
        f_status = fc3.selectbox("Status", statuses)
        fc4.text_input("Signed in as", value=st.session_state.current_user,
                       key="user_field")

    # Apply filters
    fdf = df.copy()
    if f_inst != "All":
        fdf = fdf[fdf["institute"] == f_inst]
    if f_risk != "All":
        fdf = fdf[fdf["risk_tier"] == f_risk]
    if f_status != "All":
        fdf = fdf[fdf["status"] == f_status]

    # --- Metric cards ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total AI Systems", len(fdf))
    c2.metric("High Risk", len(fdf[fdf["risk_tier"] == "High"]))
    c3.metric("Overdue Reviews", len(fdf[fdf["next_review"] < today]))
    c4.metric("Open Incidents", fdf["incidents"].ne("None").sum())

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

    a1, a2 = st.columns(2)
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

    if len(overdue) > 0:
        st.dataframe(
            overdue[["name", "owner", "institute", "risk_tier", "next_review"]],
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

            **Data source** — AI systems are registered in a central inventory
            by institute leads. Metrics recalculate on every page load.

            **Risk tiers** — Prohibited / High / Limited / Minimal, following
            NIST AI RMF and the EU AI Act.

            **Review cadence** — High-risk: every 6 months.
            Limited and minimal-risk: every 12 months.

            **Standards** — NIST AI RMF · ISO/IEC 42001 ·
            Zimbabwe National AI Strategy (2026–2030).

            **Policy Assistant** — Answers use only the SIRDC AI Policy document
            as its source. Every interaction is logged. It does not make binding
            decisions — escalate to the AI Review Board.

            **Data handling** — No personal or confidential SIRDC data is sent
            to the LLM. Only the policy text is transmitted.

            **Version** — v1.4 · Phase 1 · {today}
            """
        )

# ============ TAB 2 ============
with tab2:
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
    "SIRDC AI Governance Framework · v1.4 · Aligned with NIST AI RMF and ISO/IEC 42001 · Internal use only"
    "</p>",
    unsafe_allow_html=True,
)