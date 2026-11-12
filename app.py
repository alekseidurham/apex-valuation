"""
Interactive Streamlit & Plotly Web Application for ApexValuation.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apex_valuation.data import FinancialDataManager
from apex_valuation.models import WACCInputs
from apex_valuation.dcf import DCFValuationEngine
from apex_valuation.monte_carlo import MonteCarloValuationEngine
from apex_valuation.sensitivity import SensitivityAnalysisEngine
from apex_valuation.comps import ComparableCompanyEngine
from apex_valuation.football_field import FootballFieldChartBuilder

st.set_page_config(
    page_title="ApexValuation | Aleksei Rogozin",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1f2c; padding: 14px; border-radius: 8px; border: 1px solid #2d3748; }
    h1, h2, h3 { color: #f7fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("💼 ApexValuation: Institutional M&A & DCF Engine")
st.caption("Quantitative M&A Valuation Architecture by **Aleksei Rogozin** | Durham University (BSc Finance) / DUFS")

# Sidebar
st.sidebar.header("🎯 Target Selection")
preset_options = ["SHEL.L (Shell plc)", "AAPL (Apple Inc.)", "MSFT (Microsoft Corp)", "BP.L (BP p.l.c.)", "NVDA (NVIDIA)", "CUSTOM"]
selected_preset = st.sidebar.selectbox("Select Benchmark Target", preset_options, index=0)

if selected_preset == "CUSTOM":
    ticker_input = st.sidebar.text_input("Enter Ticker Symbol", value="BARC.L").upper()
else:
    ticker_input = selected_preset.split(" ")[0]

force_offline = st.sidebar.checkbox("Force Offline Benchmark Data", value=False, help="Ensures 100% reliability during live interview demonstrations")

st.sidebar.subheader("📈 Operating & Cash Flow Projections")
rev_growth = st.sidebar.slider("Base Revenue Growth Rate (%)", -5.0, 30.0, 7.0, 0.5) / 100.0
ebit_margin_pct = st.sidebar.slider("Target EBIT Margin (%)", 5.0, 50.0, 22.0, 1.0) / 100.0
tax_rate = st.sidebar.slider("Effective Tax Rate (%)", 15.0, 35.0, 25.0, 1.0) / 100.0

st.sidebar.subheader("🏛️ Valuation & Terminal Horizon")
terminal_g = st.sidebar.slider("Perpetual Growth Rate (g %)", 1.0, 4.0, 2.5, 0.25) / 100.0
exit_mult = st.sidebar.slider("Exit Multiple (EV / EBITDA)", 5.0, 25.0, 11.0, 0.5)

st.sidebar.subheader("🎲 Monte Carlo Simulation")
mc_trials = st.sidebar.select_slider("Number of Simulation Trials", options=[500, 1000, 1500, 2500, 5000], value=1500)

# Execute Valuation Pipeline
with st.spinner("Executing valuation engine and Monte Carlo simulations..."):
    snapshot, is_fallback = FinancialDataManager.get_financial_snapshot(ticker_input, force_offline=force_offline)

    # 5-Year Revenue Growth tapering down
    growth_trajectory = [rev_growth, rev_growth * 0.9, rev_growth * 0.8, rev_growth * 0.7, rev_growth * 0.6]

    wacc_inputs = WACCInputs(
        beta=snapshot.beta,
        effective_tax_rate=tax_rate
    )

    val_res = DCFValuationEngine.value(
        snapshot=snapshot,
        wacc_inputs=wacc_inputs,
        growth_rates=growth_trajectory,
        target_ebit_margin=ebit_margin_pct,
        terminal_growth_rate=terminal_g,
        exit_multiple=exit_mult,
        tax_rate=tax_rate
    )

    mc_engine = MonteCarloValuationEngine(trials=mc_trials, seed=42)
    mc_res = mc_engine.run(
        snapshot=snapshot,
        wacc_inputs=wacc_inputs,
        base_terminal_growth=terminal_g,
        base_growth_rates=growth_trajectory,
        tax_rate=tax_rate
    )

    sens_matrix = SensitivityAnalysisEngine.generate_matrix(
        snapshot=snapshot,
        base_wacc=val_res.wacc,
        base_growth=terminal_g,
        tax_rate=tax_rate
    )
    sens_df = SensitivityAnalysisEngine.to_dataframe(sens_matrix)

    comps = ComparableCompanyEngine.calculate_comps_ranges(snapshot)

# Top KPI Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Market Price", f"{snapshot.currency} {snapshot.current_price:.2f}", f"Cap: {snapshot.market_cap / 1e9:.1f}B")
col2.metric("DCF Gordon Growth", f"{snapshot.currency} {val_res.implied_price_gordon:.2f}", f"{val_res.upside_gordon_pct:+.1f}% Upside")
col3.metric("DCF Exit Multiple", f"{snapshot.currency} {val_res.implied_price_multiple:.2f}", f"{val_res.upside_multiple_pct:+.1f}% Upside")
col4.metric("Monte Carlo Median", f"{snapshot.currency} {mc_res.median_price:.2f}", f"{mc_res.undervalued_probability_pct:.1f}% Undervalued")
col5.metric("CAPM WACC", f"{val_res.wacc * 100:.2f}%", f"Beta: {snapshot.beta:.2f}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏈 Valuation Football Field",
    "🎲 Monte Carlo Distribution",
    "🔥 Sensitivity Heatmap",
    "📑 5-Year Cash Flow Projections",
    "📚 Investment Banking Defense"
])

with tab1:
    fig_ff = FootballFieldChartBuilder.build_chart(snapshot, val_res, mc_res)
    st.plotly_chart(fig_ff, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Relative Peer Multiples (Comps)")
        comps_data = []
        for c in comps:
            comps_data.append({
                "Multiple": c.multiple_name,
                "Peer Benchmark Range": f"{c.low_multiple:.1f}x - {c.high_multiple:.1f}x",
                f"Implied Price ({snapshot.currency})": f"{c.implied_price_low:.2f} - {c.implied_price_high:.2f}",
                "Status": "Undervalued" if c.implied_price_low > snapshot.current_price else "Fairly Valued"
            })
        st.dataframe(pd.DataFrame(comps_data), use_container_width=True, hide_index=True)

    with c2:
        st.subheader("💡 Strategic M&A Valuation Takeaways")
        status_color = "🟢" if mc_res.undervalued_probability_pct >= 55 else "🔴"
        st.markdown(f"""
        * **Target:** **{snapshot.company_name}** ({snapshot.ticker})
        * **Trading Price:** `{snapshot.currency} {snapshot.current_price:.2f}` vs **Intrinsic Value:** `{snapshot.currency} {val_res.implied_price_gordon:.2f}`
        * **Margin of Safety:** {status_color} **{mc_res.undervalued_probability_pct:.1f}% probability** that intrinsic value exceeds current market price under 1,500 stochastic scenarios.
        * **WACC Discount Rate:** `{val_res.wacc * 100:.2f}%` derived via CAPM ($r_f=4.2\\%$, $\\beta={snapshot.beta:.2f}$, $ERP=5.5\\%$).
        """)

with tab2:
    st.subheader("🎲 Monte Carlo Probabilistic Density Distribution")
    st.caption("Distribution of 1,500 simulated share prices with random shocks to WACC, Terminal Growth, and Revenue Growth.")

    fig_mc = go.Figure()
    fig_mc.add_trace(
        go.Histogram(
            x=mc_res.prices,
            nbinsx=60,
            name="Simulated Share Prices",
            marker_color="#3182ce",
            opacity=0.75
        )
    )
    fig_mc.add_vline(
        x=snapshot.current_price,
        line_width=3,
        line_dash="dash",
        line_color="#f56565",
        annotation_text=f"Market Price: {snapshot.currency} {snapshot.current_price:.2f}",
        annotation_position="top left"
    )
    fig_mc.add_vline(
        x=mc_res.median_price,
        line_width=2.5,
        line_color="#48bb78",
        annotation_text=f"Median Value: {snapshot.currency} {mc_res.median_price:.2f}",
        annotation_position="top right"
    )
    fig_mc.update_layout(
        template="plotly_dark",
        height=450,
        xaxis_title=f"Implied Fair Value Per Share ({snapshot.currency})",
        yaxis_title="Scenario Frequency",
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    mc_table = {
        "Percentile Interval": ["10th %ile (Bear)", "25th %ile (Conservative)", "50th %ile (Median Fair Value)", "75th %ile (Optimistic)", "90th %ile (Bull)"],
        f"Implied Price ({snapshot.currency})": [f"{mc_res.p10_price:.2f}", f"{mc_res.p25_price:.2f}", f"{mc_res.median_price:.2f}", f"{mc_res.p75_price:.2f}", f"{mc_res.p90_price:.2f}"],
        "Implied Premium / Discount": [
            f"{((mc_res.p10_price - snapshot.current_price)/snapshot.current_price)*100:+.1f}%",
            f"{((mc_res.p25_price - snapshot.current_price)/snapshot.current_price)*100:+.1f}%",
            f"{((mc_res.median_price - snapshot.current_price)/snapshot.current_price)*100:+.1f}%",
            f"{((mc_res.p75_price - snapshot.current_price)/snapshot.current_price)*100:+.1f}%",
            f"{((mc_res.p90_price - snapshot.current_price)/snapshot.current_price)*100:+.1f}%"
        ]
    }
    st.table(pd.DataFrame(mc_table))

with tab3:
    st.subheader("🔥 WACC vs Terminal Growth Rate Sensitivity Matrix")
    st.caption("Implied share price sensitivity across varying cost of capital and perpetual growth rate assumptions.")

    fig_sens = go.Figure(
        data=go.Heatmap(
            z=sens_df.values,
            x=sens_df.columns,
            y=sens_df.index,
            colorscale="Viridis",
            text=[[f"{v:.1f}" if not np.isnan(v) else "N/A" for v in row] for row in sens_df.values],
            texttemplate="%{text}",
            textfont={"size": 13, "color": "white"}
        )
    )
    fig_sens.update_layout(
        template="plotly_dark",
        height=450,
        xaxis_title="Perpetual Terminal Growth Rate (g)",
        yaxis_title="Weighted Average Cost of Capital (WACC)",
        margin=dict(l=40, r=40, t=30, b=40)
    )
    st.plotly_chart(fig_sens, use_container_width=True)

with tab4:
    st.subheader("📑 5-Year Projected Unlevered Free Cash Flows (UFCF)")
    proj = val_res.projections

    proj_df = pd.DataFrame({
        "Year": [f"Year {y}" for y in proj.years],
        f"Revenue ({snapshot.currency} B)": [f"{r / 1e9:.2f}" for r in proj.revenues],
        f"EBIT ({snapshot.currency} B)": [f"{e / 1e9:.2f}" for e in proj.ebit],
        f"NOPAT (1-t) ({snapshot.currency} B)": [f"{n / 1e9:.2f}" for n in proj.nopat],
        f"UFCF ({snapshot.currency} B)": [f"{u / 1e9:.2f}" for u in proj.ufcf],
        "Discount Factor": [f"{df:.4f}" for df in proj.discount_factors],
        f"PV of UFCF ({snapshot.currency} B)": [f"{pv / 1e9:.2f}" for pv in proj.pv_ufcf]
    })
    st.dataframe(proj_df, use_container_width=True, hide_index=True)

    fig_ufcf = go.Figure()
    fig_ufcf.add_trace(go.Bar(x=[f"Yr {y}" for y in proj.years], y=[u / 1e9 for u in proj.ufcf], name="Nominal UFCF", marker_color="#4299e1"))
    fig_ufcf.add_trace(go.Bar(x=[f"Yr {y}" for y in proj.years], y=[pv / 1e9 for pv in proj.pv_ufcf], name="Present Value (Discounted)", marker_color="#48bb78"))
    fig_ufcf.update_layout(
        template="plotly_dark",
        barmode="group",
        height=380,
        title=f"Nominal Free Cash Flows vs Discounted Present Value ({snapshot.currency} Billions)",
        yaxis_title=f"{snapshot.currency} Billions"
    )
    st.plotly_chart(fig_ufcf, use_container_width=True)

    st.subheader("🌉 Enterprise Value to Equity Value Bridge")
    bridge_df = pd.DataFrame({
        "Line Item": [
            "Sum of PV of 5-Year UFCF",
            "PV of Terminal Value (Gordon Growth)",
            "= Enterprise Value (EV)",
            "(+) Cash & Liquid Equivalents",
            "(-) Total Debt & Borrowings",
            "= Implied Equity Value",
            "Divided by Shares Outstanding",
            "= Implied Fair Value Per Share"
        ],
        f"Value ({snapshot.currency})": [
            f"{proj.sum_pv_ufcf / 1e9:.2f} B",
            f"{proj.pv_terminal_value_gordon / 1e9:.2f} B",
            f"{val_res.enterprise_value_gordon / 1e9:.2f} B",
            f"{snapshot.cash_and_equivalents / 1e9:.2f} B",
            f"{snapshot.total_debt / 1e9:.2f} B",
            f"{val_res.equity_value_gordon / 1e9:.2f} B",
            f"{snapshot.shares_outstanding / 1e9:.2f} B shares",
            f"{snapshot.currency} {val_res.implied_price_gordon:.2f}"
        ]
    })
    st.table(bridge_df)

with tab5:
    st.markdown("""
    ### 🏛️ Investment Banking Valuation Methodology & Interview Defense

    #### 1. Unlevered Free Cash Flow (FCFF) Formula
    $$\\text{UFCF} = \\text{EBIT} \\times (1 - t) + \\text{D\\&A} - \\text{CapEx} - \\Delta \\text{NWC}$$
    * **Why Unlevered?** Unlevered cash flows reflect cash generated by core operations available to **all capital providers** (both debt and equity holders), independent of capital structure.

    #### 2. Weighted Average Cost of Capital (WACC) via CAPM
    $$WACC = \\left(\\frac{E}{E + D} \\times r_e\\right) + \\left(\\frac{D}{E + D} \\times r_d \\times (1 - t)\\right)$$
    $$r_e = r_f + \\beta \\times ERP$$
    * **Cost of Equity ($r_e$):** Sourced via CAPM using 10-Year risk-free benchmark and long-term equity risk premium (5.5%).
    * **Cost of Debt ($r_d$):** Tax-shielded by $(1 - t)$ because interest expense is tax-deductible.

    #### 3. Terminal Value (Dual-Methodology)
    * **Gordon Growth Model (Perpetual Growth):**
      $$TV = \\frac{\\text{UFCF}_5 \\times (1 + g)}{WACC - g}, \\quad g \\le 2.5\\% \\text{ (capped at long-term GDP growth)}$$
    * **Exit Multiple Model:**
      $$TV = \\text{EBITDA}_5 \\times \\text{EV/EBITDA Multiple}$$

    #### 4. The Enterprise Value to Equity Value Bridge
    $$\\text{Equity Value} = \\text{Enterprise Value} - \\text{Total Debt} + \\text{Cash} - \\text{Minority Interest}$$
    $$\\text{Implied Share Price} = \\frac{\\text{Equity Value}}{\\text{Diluted Shares Outstanding}}$$
    """)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096;'>ApexValuation Engine | Author: Aleksei Rogozin | Durham University | Open Source MIT</div>", unsafe_allow_html=True)
