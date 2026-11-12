"""
ApexValuation: Interactive CLI Valuation Runner.
Executes an institutional 2-Stage Unlevered DCF, Monte Carlo probabilistic simulation,
and peer multiples analysis on any public or private corporate target.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

import sys
import os
import argparse

# Add package root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apex_valuation.data import FinancialDataManager
from apex_valuation.models import WACCInputs
from apex_valuation.dcf import DCFValuationEngine
from apex_valuation.monte_carlo import MonteCarloValuationEngine
from apex_valuation.sensitivity import SensitivityAnalysisEngine
from apex_valuation.comps import ComparableCompanyEngine


def run_cli_valuation(
    ticker: str = "SHEL.L",
    force_offline: bool = False,
    trials: int = 1_500,
    terminal_growth: float = 0.025,
    exit_multiple: float = 11.0
):
    print("=" * 78)
    print("      APEX VALUATION: INSTITUTIONAL M&A & DCF ENGINE (MONTE CARLO)")
    print("      Research by: Aleksei Rogozin | Durham University (BSc Finance)")
    print("=" * 78)

    print(f"\n[1/4] Ingesting Corporate Financials for Target: {ticker}...")
    snapshot, is_fallback = FinancialDataManager.get_financial_snapshot(ticker, force_offline=force_offline)
    feed_label = "Calibrated Institutional Offline Profile" if is_fallback else "Live yfinance Corporate Feed"
    print(f"      -> Company Name:    {snapshot.company_name}")
    print(f"      -> Current Price:   {snapshot.currency} {snapshot.current_price:.2f}")
    print(f"      -> Market Cap:      {snapshot.currency} {snapshot.market_cap / 1e9:.2f}B")
    print(f"      -> Revenue (LTM):   {snapshot.currency} {snapshot.revenue / 1e9:.2f}B")
    print(f"      -> Operating EBIT:  {snapshot.currency} {snapshot.ebit / 1e9:.2f}B")
    print(f"      -> Total Net Debt:  {snapshot.currency} {snapshot.net_debt / 1e9:.2f}B")
    print(f"      -> Data Ingestion:  {feed_label}")

    print("\n[2/4] Executing 2-Stage DCF Valuation (CAPM WACC & 5-Year UFCF)...")
    val_res = DCFValuationEngine.value(
        snapshot=snapshot,
        terminal_growth_rate=terminal_growth,
        exit_multiple=exit_multiple
    )
    print(f"      -> Calculated WACC:         {val_res.wacc * 100:.2f}%")
    print(f"      -> Sum PV of 5-Yr UFCF:     {snapshot.currency} {val_res.projections.sum_pv_ufcf / 1e9:.2f}B")
    print(f"      -> PV of Terminal Value (g):{snapshot.currency} {val_res.projections.pv_terminal_value_gordon / 1e9:.2f}B")
    print(f"      -> Implied Price (Gordon):  {snapshot.currency} {val_res.implied_price_gordon:.2f} ({val_res.upside_gordon_pct:+.1f}%)")
    print(f"      -> Implied Price (Multiple):{snapshot.currency} {val_res.implied_price_multiple:.2f} ({val_res.upside_multiple_pct:+.1f}%)")

    print(f"\n[3/4] Running Monte Carlo Probabilistic Simulation ({trials:,} trials)...")
    mc_engine = MonteCarloValuationEngine(trials=trials, seed=42)
    mc_res = mc_engine.run(snapshot, base_terminal_growth=terminal_growth)
    print(f"      -> Median Value:            {snapshot.currency} {mc_res.median_price:.2f}")
    print(f"      -> 25th - 75th %ile Range:  {snapshot.currency} {mc_res.p25_price:.2f} - {snapshot.currency} {mc_res.p75_price:.2f}")
    print(f"      -> 10th - 90th %ile Range:  {snapshot.currency} {mc_res.p10_price:.2f} - {snapshot.currency} {mc_res.p90_price:.2f}")
    print(f"      -> Undervaluation Odds:     {mc_res.undervalued_probability_pct:.1f}%")

    print("\n[4/4] Calculating Comparable Peer Multiples (Comps)...")
    comps = ComparableCompanyEngine.calculate_comps_ranges(snapshot)
    for c in comps:
        print(f"      -> {c.multiple_name:<16} ({c.low_multiple:.1f}x - {c.high_multiple:.1f}x): {snapshot.currency} {c.implied_price_low:.2f} - {snapshot.currency} {c.implied_price_high:.2f}")

    print("\n" + "=" * 78)
    print("                    EXECUTIVE M&A VALUATION SUMMARY")
    print("=" * 78)
    print(f"  Target Company:             {snapshot.company_name} ({snapshot.ticker})")
    print(f"  Current Market Price:       {snapshot.currency} {snapshot.current_price:.2f}")
    print(f"  DCF Fair Value (Gordon):    {snapshot.currency} {val_res.implied_price_gordon:.2f}  | Upside: {val_res.upside_gordon_pct:>+6.1f}%")
    print(f"  DCF Fair Value (Multiple):  {snapshot.currency} {val_res.implied_price_multiple:.2f}  | Upside: {val_res.upside_multiple_pct:>+6.1f}%")
    print(f"  Monte Carlo Median Price:   {snapshot.currency} {mc_res.median_price:.2f}  | Odds of Undervaluation: {mc_res.undervalued_probability_pct:.1f}%")
    
    verdict = "ATTRACTIVE ENTRY (UNDERVALUED)" if mc_res.undervalued_probability_pct >= 60 else "FAIRLY VALUED / PREMIUM"
    print(f"  Strategic M&A Assessment:   {verdict}")
    print("=" * 78)
    print("\n[SUCCESS] Valuation complete. Launch interactive UI: 'streamlit run app.py'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ApexValuation CLI Engine")
    parser.add_argument("--ticker", type=str, default="SHEL.L", help="Corporate ticker symbol (e.g. SHEL.L, AAPL, BP.L, MSFT)")
    parser.add_argument("--offline", action="store_true", help="Force offline benchmark mode (100% resilient)")
    parser.add_argument("--trials", type=int, default=1500, help="Number of Monte Carlo trials")
    args = parser.parse_args()

    run_cli_valuation(ticker=args.ticker, force_offline=args.offline, trials=args.trials)
