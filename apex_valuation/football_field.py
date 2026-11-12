"""
Investment Banking Football Field Valuation Chart Generator.
Synthesizes DCF, Comps, Monte Carlo, and 52-week ranges into a unified Plotly visual.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from typing import List, Dict, Any
import plotly.graph_objects as go
from .models import FinancialSnapshot, ValuationResult, MonteCarloResult
from .comps import ComparableCompanyEngine


class FootballFieldChartBuilder:
    """Constructs institutional horizontal range charts comparing valuation methodologies."""

    @classmethod
    def build_chart(
        cls,
        snapshot: FinancialSnapshot,
        valuation: ValuationResult,
        monte_carlo: MonteCarloResult
    ) -> go.Figure:
        """Generates the signature Investment Banking Football Field Chart."""
        cur_p = snapshot.current_price

        # Derive ranges
        # 1. 52-Week Range Proxy (or 82% to 118% of current price)
        p_52_low = cur_p * 0.82
        p_52_high = cur_p * 1.18

        # 2. DCF Gordon Growth (Conservative to Optimistic)
        dcf_g_low = valuation.implied_price_gordon * 0.88
        dcf_g_high = valuation.implied_price_gordon * 1.15

        # 3. DCF Exit Multiple
        dcf_m_low = valuation.implied_price_multiple * 0.90
        dcf_m_high = valuation.implied_price_multiple * 1.12

        # 4. Comps Multiples
        comps_list = ComparableCompanyEngine.calculate_comps_ranges(snapshot)
        ev_ebitda_comp = comps_list[0]
        pe_comp = comps_list[1]

        # 5. Monte Carlo 25th - 75th Percentile
        mc_low = monte_carlo.p25_price
        mc_high = monte_carlo.p75_price

        categories = [
            "52-Week Trading Range",
            "Comps: EV/EBITDA",
            "Comps: P/E Multiple",
            "DCF: Exit Multiple",
            "DCF: Gordon Growth",
            "Monte Carlo (25th-75th %ile)",
        ]

        lows = [p_52_low, ev_ebitda_comp.implied_price_low, pe_comp.implied_price_low, dcf_m_low, dcf_g_low, mc_low]
        highs = [p_52_high, ev_ebitda_comp.implied_price_high, pe_comp.implied_price_high, dcf_m_high, dcf_g_high, mc_high]
        widths = [max(h - l, 0.1) for l, h in zip(lows, highs)]

        colors = [
            "#718096",  # Gray for 52-week
            "#4299e1",  # Blue for Comps
            "#3182ce",  # Darker blue
            "#48bb78",  # Green for DCF Exit
            "#38a169",  # Green for DCF Gordon
            "#ed8936",  # Orange for Monte Carlo
        ]

        fig = go.Figure()

        # Add floating horizontal bars
        fig.add_trace(
            go.Bar(
                y=categories,
                x=widths,
                base=lows,
                orientation="h",
                marker=dict(
                    color=colors,
                    line=dict(color="#ffffff", width=1.5)
                ),
                text=[f"{snapshot.currency} {l:.1f} - {h:.1f}" for l, h in zip(lows, highs)],
                textposition="inside",
                insidetextanchor="middle",
                hoverinfo="text",
                hovertext=[
                    f"{cat}<br>Range: {snapshot.currency} {l:.2f} to {h:.2f}<br>Spread: {snapshot.currency} {w:.2f}"
                    for cat, l, h, w in zip(categories, lows, highs, widths)
                ]
            )
        )

        # Add vertical line for Current Market Price
        fig.add_vline(
            x=cur_p,
            line_width=2.5,
            line_dash="dash",
            line_color="#f56565",
            annotation_text=f"Current Price: {snapshot.currency} {cur_p:.2f}",
            annotation_position="top"
        )

        fig.update_layout(
            template="plotly_dark",
            height=460,
            title=dict(
                text=f"<b>{snapshot.company_name} ({snapshot.ticker}) — Valuation Football Field</b>",
                x=0.05,
                y=0.95
            ),
            xaxis=dict(
                title=f"Implied Equity Value Per Share ({snapshot.currency})",
                gridcolor="#2d3748"
            ),
            yaxis=dict(
                gridcolor="#2d3748"
            ),
            margin=dict(l=180, r=40, t=60, b=40),
            showlegend=False
        )

        return fig
