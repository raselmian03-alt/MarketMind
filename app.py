import json
import os
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from agent import run_agent
from tools.sales import analyze_sales

load_dotenv()

st.set_page_config(
    page_title="MarketMind Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 MarketMind Agent")
st.caption("AI-powered marketing analyst — analyze sales, campaigns, competitors, and generate reports.")


class _NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def show_charts(data: dict):
    numeric = data.get("numeric_summary", {})
    categorical = data.get("categorical_summary", {})
    correlations = data.get("top_correlations", [])
    group = data.get("group_insight", {})
    shape = data.get("shape", {})

    st.caption(f"Dataset: **{shape.get('rows', '?')} rows** × **{shape.get('columns', '?')} columns**")

    # ── 1. Group-by insight ────────────────────────────────────────────────────
    if group and group.get("values"):
        st.subheader(f"{group['metric']} by {group['grouped_by']}")
        items = sorted(group["values"].items(), key=lambda x: x[1], reverse=True)[:15]
        labels = [str(k) for k, _ in items]
        values = [v for _, v in items]
        fig = px.bar(
            x=labels, y=values,
            labels={"x": group["grouped_by"], "y": group["metric"]},
            color=values,
            color_continuous_scale="Blues",
        )
        fig.update_xaxes(tickangle=45)
        fig.update_layout(showlegend=False, height=420, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── 2. Categorical distributions (up to 4 columns, 2-per-row) ─────────────
    if categorical:
        cat_keys = list(categorical.keys())[:4]
        for row_start in range(0, len(cat_keys), 2):
            cols = st.columns(2)
            for offset in range(2):
                idx = row_start + offset
                if idx >= len(cat_keys):
                    break
                col_name = cat_keys[idx]
                top = categorical[col_name]["top_values"]
                labels = list(top.keys())[:10]
                values = list(top.values())[:10]
                fig = px.bar(
                    x=labels, y=values,
                    title=f"Top Values: {col_name}",
                    labels={"x": col_name, "y": "Count"},
                    color=values,
                    color_continuous_scale="Teal",
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(showlegend=False, height=360, coloraxis_showscale=False)
                cols[offset].plotly_chart(fig, use_container_width=True)

    # ── 3. Numeric mean vs max ─────────────────────────────────────────────────
    if numeric:
        st.subheader("Numeric Column Statistics")
        col_names = list(numeric.keys())
        means = [numeric[c]["mean"] for c in col_names]
        maxes = [numeric[c]["max"] for c in col_names]
        medians = [numeric[c]["median"] for c in col_names]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Mean", x=col_names, y=means, marker_color="#4C78A8"))
        fig.add_trace(go.Bar(name="Median", x=col_names, y=medians, marker_color="#72B7B2"))
        fig.add_trace(go.Bar(name="Max", x=col_names, y=maxes, marker_color="#F58518"))
        fig.update_layout(barmode="group", xaxis_tickangle=45, height=420)
        st.plotly_chart(fig, use_container_width=True)

    # ── 4. Correlation heatmap ─────────────────────────────────────────────────
    if correlations:
        st.subheader("Correlation Heatmap")
        all_cols = list(dict.fromkeys(
            [p["col_a"] for p in correlations] + [p["col_b"] for p in correlations]
        ))
        n = len(all_cols)
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        idx_map = {c: i for i, c in enumerate(all_cols)}
        for pair in correlations:
            i, j = idx_map[pair["col_a"]], idx_map[pair["col_b"]]
            matrix[i][j] = pair["correlation"]
            matrix[j][i] = pair["correlation"]

        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=all_cols,
            y=all_cols,
            colorscale="RdBu",
            zmid=0,
            text=[[f"{v:.2f}" for v in row] for row in matrix],
            texttemplate="%{text}",
            zmin=-1,
            zmax=1,
        ))
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)


# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_analysis" not in st.session_state:
    st.session_state.pending_analysis = None
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "last_uploaded_name" not in st.session_state:
    st.session_state.last_uploaded_name = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("API Key")
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=env_key,
        type="password",
        placeholder="sk-ant-api03-...",
        help="Get your key at console.anthropic.com → API Keys",
    )
    if not api_key_input:
        st.warning("Paste your API key above to start")
    elif not api_key_input.startswith("sk-ant-"):
        st.error("That doesn't look like a valid key. It must start with `sk-ant-`")
        api_key_input = ""
    else:
        st.success("API key looks valid")

    st.divider()
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file:
        if uploaded_file.name != st.session_state.last_uploaded_name:
            with st.spinner("Reading CSV…"):
                csv_text = uploaded_file.read().decode("utf-8")
                analysis = analyze_sales(csv_text, question="")
                if "error" in analysis:
                    st.error(f"CSV parse error: {analysis['error']}")
                else:
                    st.session_state.pending_analysis = json.dumps(
                        analysis, indent=2, cls=_NpEncoder
                    )
                    st.session_state.analysis_data = analysis
                    st.session_state.last_uploaded_name = uploaded_file.name
                    st.session_state.history = []
                    st.session_state.messages = []
        if st.session_state.pending_analysis or st.session_state.analysis_data:
            st.success(f"Loaded: {uploaded_file.name}")

    st.divider()
    st.markdown("**What MarketMind can do:**")
    st.markdown("- 📈 Analyze sales data")
    st.markdown("- 📣 Evaluate campaign KPIs")
    st.markdown("- 🔍 Research competitors")
    st.markdown("- 📝 Generate reports")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.pending_analysis = None
        st.session_state.analysis_data = None
        st.session_state.last_uploaded_name = None
        st.rerun()

# ── Guard ──────────────────────────────────────────────────────────────────────
if not api_key_input:
    st.info("Paste your **Anthropic API key** in the sidebar to start chatting.")
    st.stop()

# ── Tabs: Chat | Charts ────────────────────────────────────────────────────────
tab_chat, tab_charts = st.tabs(["💬 Chat", "📊 Charts"])

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

with tab_charts:
    if st.session_state.analysis_data:
        show_charts(st.session_state.analysis_data)
    else:
        st.info("📁 Upload a CSV file and ask a question — charts will appear here automatically.")

# ── Chat input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask MarketMind anything about your marketing data…")

if user_input:
    if st.session_state.pending_analysis:
        full_message = (
            f"{user_input}\n\n"
            f"<dataset_analysis>\n{st.session_state.pending_analysis}\n</dataset_analysis>"
        )
        st.session_state.pending_analysis = None
    else:
        full_message = user_input

    st.session_state.messages.append({"role": "user", "content": user_input})

    with tab_chat:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("MarketMind is thinking…"):
                try:
                    response_text, updated_history = run_agent(
                        user_message=full_message,
                        conversation_history=st.session_state.history,
                        api_key=api_key_input,
                    )
                except Exception as e:
                    err = str(e)
                    st.session_state.history = []
                    if "401" in err or "authentication_error" in err or "invalid x-api-key" in err:
                        st.error("**Invalid API key.** Check the key in the sidebar.")
                    else:
                        st.error(f"**Error:** {err}")
                    st.stop()
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.session_state.history = updated_history
