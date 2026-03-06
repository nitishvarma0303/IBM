import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from fpdf import FPDF
import json
from datetime import datetime

from data_generator import (
    generate_sample_data,
    generate_anomaly_alerts,
    generate_fairness_metrics,
    generate_compliance_data,
    generate_lineage_data
)
from utils import calculate_dts, get_dts_rating, calculate_fairness_metrics, get_fairness_status, generate_api_output

# Page configuration
st.set_page_config(
    page_title="AI Data Trust Score Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .alert-high {
        background-color: #ffe6e6;
        border-left-color: #dc3545;
    }
    .alert-medium {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .alert-low {
        background-color: #d1ecf1;
        border-left-color: #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = generate_sample_data(30)
    alerts = generate_anomaly_alerts()
    fairness = generate_fairness_metrics()
    compliance = generate_compliance_data()
    nodes, edges = generate_lineage_data()
    return df, alerts, fairness, compliance, nodes, edges

df, alerts, fairness_metrics, compliance_data, lineage_nodes, lineage_edges = load_data()

# Sidebar
st.sidebar.title("🎯 AI Data Trust Score")
st.sidebar.markdown("---")

# Current DTS calculation
latest_data = df.iloc[-1]
current_dts = latest_data['dts']
current_ars = latest_data['ars']
current_ets = latest_data['ets']
current_ecgs = latest_data['ecgs']

st.sidebar.metric("Current DTS", f"{current_dts:.2f}", f"{get_dts_rating(current_dts)}")
st.sidebar.metric("ARS", f"{current_ars:.2f}")
st.sidebar.metric("ETS", f"{current_ets:.2f}")
st.sidebar.metric("ECGS", f"{current_ecgs:.2f}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")

# Main content
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "🔍 Data Lineage",
    "⚠️ Anomaly Monitor",
    "⚖️ Fairness & Bias",
    "📋 Compliance",
    "📑 Reports"
])

with tab1:
    st.markdown('<h1 class="main-header">DATA TRUST SCORE DASHBOARD</h1>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>March 2026</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### OVERALL DTS")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_dts * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "DTS Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 70], 'color': "#ff6b6b"},
                    {'range': [70, 80], 'color': "#ffd93d"},
                    {'range': [80, 90], 'color': "#6bcf7f"},
                    {'range': [90, 100], 'color': "#4ecdc4"}
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"**Rating:** {get_dts_rating(current_dts)}")

    with col2:
        st.markdown("### PILLAR BREAKDOWN")
        pillars = ['ARS', 'ETS', 'ECGS']
        scores = [current_ars, current_ets, current_ecgs]
        colors = ['#6bcf7f', '#ffd93d', '#4ecdc4']

        for pillar, score, color in zip(pillars, scores, colors):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{pillar}:** {score:.2f}")
                st.progress(score, text=f"{int(score*100)}%")
            with col_b:
                st.markdown(f"**{get_dts_rating(score)}**")

        if current_ets < 0.8:
            st.warning("⚠️ ETS needs attention")

    st.markdown("### HISTORICAL TREND (Last 30 Days)")
    fig = px.line(df, x='date', y='dts', title='DTS Trend')
    fig.update_layout(xaxis_title="Date", yaxis_title="DTS")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<h1 class="main-header">DATA LINEAGE VISUALIZATION</h1>', unsafe_allow_html=True)

    # Create network graph
    G = nx.DiGraph()
    for node in lineage_nodes:
        G.add_node(node['id'], label=node['label'], type=node['type'], status=node['status'])
    for edge in lineage_edges:
        G.add_edge(edge['source'], edge['target'])

    pos = nx.spring_layout(G)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(G.nodes[node]['label'])
        status = G.nodes[node]['status']
        if status == 'good':
            node_color.append('#6bcf7f')
        elif status == 'warning':
            node_color.append('#ffd93d')
        else:
            node_color.append('#ff6b6b')

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        marker=dict(
            showscale=False,
            color=node_color,
            size=20,
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title="Data Flow Graph",
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### SELECTED NODE: Fraud Model")
    st.markdown("""
    - **Type:** AI Model
    - **Version:** 2.1.0
    - **Algorithm:** XGBoost
    - **Training Data:** 1.2M records
    - **Accuracy:** 94.2%
    - **Last Updated:** 2026-03-05
    """)

with tab3:
    st.markdown('<h1 class="main-header">ANOMALY MONITOR</h1>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Last Updated: {datetime.now().strftime('%I:%M %p')}</h3>", unsafe_allow_html=True)

    # Statistics
    total_alerts = len(alerts)
    high_alerts = sum(1 for a in alerts if a['severity'] == 'HIGH')
    medium_alerts = sum(1 for a in alerts if a['severity'] == 'MEDIUM')
    low_alerts = sum(1 for a in alerts if a['severity'] == 'LOW')
    resolved = 16

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Alerts", total_alerts)
    with col2:
        st.metric("HIGH", high_alerts)
    with col3:
        st.metric("MEDIUM", medium_alerts)
    with col4:
        st.metric("LOW", low_alerts)
    with col5:
        st.metric("Resolved", resolved)

    # Active Alerts
    st.markdown("### ACTIVE ALERTS")
    for alert in alerts:
        severity_class = f"alert-{alert['severity'].lower()}"
        st.markdown(f"""
        <div class="metric-card {severity_class}">
            <strong>ID {alert['id']}:</strong> {alert['description']}<br>
            <strong>Severity:</strong> {'🔴' if alert['severity']=='HIGH' else '🟡' if alert['severity']=='MEDIUM' else '🟢'} {alert['severity']}<br>
            <strong>Confidence:</strong> {alert['confidence']}% █{'█' * (alert['confidence']//10)}<br>
            <strong>Timestamp:</strong> {alert['timestamp']}
        </div>
        """, unsafe_allow_html=True)

    # Alert Frequency Chart
    st.markdown("### ALERT FREQUENCY (Last 24 Hours)")
    hours = list(range(24))
    counts = [np.random.randint(0, 6) for _ in hours]
    fig = px.bar(x=hours, y=counts, labels={'x': 'Hour', 'y': 'Count'})
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown('<h1 class="main-header">FAIRNESS & BIAS DASHBOARD</h1>', unsafe_allow_html=True)

    st.markdown("### FAIRNESS METRICS")
    metrics_df = pd.DataFrame({
        'Metric': ['Disparate Impact', 'Demographic Parity Diff', 'Equalized Odds Diff', 'Treatment Equality'],
        'Value': [fairness_metrics['disparate_impact'], fairness_metrics['demographic_parity_diff'],
                 fairness_metrics['equalized_odds_diff'], fairness_metrics['treatment_equality']],
        'Status': [get_fairness_status(v) for v in fairness_metrics.values()]
    })
    st.table(metrics_df)

    st.markdown("### APPROVAL RATES BY GROUP")
    groups = ['Group A', 'Group B', 'Group C', 'Group D']
    rates = [85, 78, 82, 88]
    fig = px.bar(x=groups, y=rates, labels={'x': 'Group', 'y': 'Approval Rate (%)'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⚠️ WATCH LIST")
    st.warning("• Feature 'income' shows slight bias against Group B")
    st.info("• Recommendation: Retrain model with balanced sampling")

with tab5:
    st.markdown('<h1 class="main-header">COMPLIANCE DASHBOARD</h1>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Regulatory Readiness</h3>", unsafe_allow_html=True)

    st.metric("OVERALL COMPLIANCE SCORE", f"{compliance_data['overall_score']}%")

    st.markdown("### REGULATORY COMPLIANCE")
    regs = compliance_data['regulations']
    for reg, score in regs.items():
        st.progress(score/100, text=f"{reg}: {score}%")

    st.markdown("### GDPR CHECKLIST")
    checklist_df = pd.DataFrame(compliance_data['gdpr_checklist'])
    st.table(checklist_df)

    st.markdown("### ACTION ITEMS")
    for item in compliance_data['action_items']:
        st.markdown(f"• {item}")

with tab6:
    st.markdown('<h1 class="main-header">REPORTS</h1>', unsafe_allow_html=True)

    if st.button("Generate PDF Report"):
        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)
        pdf.cell(200, 10, txt="AI TRUST & COMPLIANCE REPORT", ln=True, align='C')
        pdf.cell(200, 10, txt="March 6, 2026", ln=True, align='C')
        pdf.cell(200, 10, txt="Prepared for: Executive Team", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="EXECUTIVE SUMMARY", ln=True)
        pdf.multi_cell(0, 10, txt=f"The AI Data Trust Score (DTS) for Q1 2026 is {current_dts} (Excellent), representing a 5% improvement over Q4 2025.")

        # Add more content...

        pdf.output("report.pdf")
        st.success("Report generated: report.pdf")

    st.markdown("### API OUTPUT (JSON)")
    api_data = generate_api_output(current_dts, current_ars, current_ets, current_ecgs)
    st.json(api_data)

    if st.button("Download JSON"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(api_data, indent=2),
            file_name="dts_api_output.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown("**AI Data Trust Score System** - Prototype Version")
st.markdown("*Built with Streamlit, Plotly, and Python*")