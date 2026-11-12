"""
Unit & Integration Test Suite for ApexValuation Engine.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

import pytest
import numpy as np
import pandas as pd

from apex_valuation.data import FinancialDataManager
from apex_valuation.models import WACCInputs
from apex_valuation.dcf import DCFValuationEngine
from apex_valuation.monte_carlo import MonteCarloValuationEngine
from apex_valuation.sensitivity import SensitivityAnalysisEngine
from apex_valuation.comps import ComparableCompanyEngine
from apex_valuation.football_field import FootballFieldChartBuilder


def test_data_manager_fallback():
    snapshot, is_fallback = FinancialDataManager.get_financial_snapshot("SHEL.L", force_offline=True)
    assert snapshot.ticker == "SHEL.L"
    assert snapshot.company_name == "Shell plc"
    assert snapshot.current_price > 0
    assert snapshot.revenue > 0
    assert snapshot.shares_outstanding > 0
    assert snapshot.ebit > 0
    assert is_fallback is True


def test_wacc_calculation():
    snapshot, _ = FinancialDataManager.get_financial_snapshot("AAPL", force_offline=True)
    inputs = WACCInputs(
        risk_free_rate=0.040,
        equity_risk_premium=0.055,
        beta=1.10,
        cost_of_debt_pre_tax=0.050,
        effective_tax_rate=0.25
    )
    res = DCFValuationEngine.calculate_wacc(snapshot, inputs)
    
    # Expected cost of equity: 0.04 + 1.10 * 0.055 = 0.1005 (10.05%)
    assert pytest.approx(res.cost_of_equity, 0.001) == 0.1005
    # Cost of debt after tax: 0.05 * 0.75 = 0.0375 (3.75%)
    assert pytest.approx(res.cost_of_debt_after_tax, 0.001) == 0.0375
    # WACC should be bounded between 6% and 12%
    assert 0.06 < res.wacc < 0.12


def test_dcf_projections_and_valuation():
    snapshot, _ = FinancialDataManager.get_financial_snapshot("MSFT", force_offline=True)
    val_res = DCFValuationEngine.value(
        snapshot=snapshot,
        terminal_growth_rate=0.025,
        exit_multiple=12.0
    )
    assert val_res.wacc > 0
    assert val_res.enterprise_value_gordon > 0
    assert val_res.implied_price_gordon > 0
    assert val_res.implied_price_multiple > 0
    assert len(val_res.projections.years) == 5
    assert val_res.projections.sum_pv_ufcf > 0


def test_monte_carlo_simulation():
    snapshot, _ = FinancialDataManager.get_financial_snapshot("SHEL.L", force_offline=True)
    mc_engine = MonteCarloValuationEngine(trials=300, seed=123)
    mc_res = mc_engine.run(snapshot)

    assert mc_res.trials == 300
    assert len(mc_res.prices) == 300
    assert mc_res.p10_price <= mc_res.p25_price <= mc_res.median_price <= mc_res.p75_price <= mc_res.p90_price
    assert 0.0 <= mc_res.undervalued_probability_pct <= 100.0


def test_sensitivity_matrix():
    snapshot, _ = FinancialDataManager.get_financial_snapshot("BP.L", force_offline=True)
    matrix = SensitivityAnalysisEngine.generate_matrix(
        snapshot=snapshot,
        base_wacc=0.09,
        base_growth=0.025,
        grid_size=5
    )
    df = SensitivityAnalysisEngine.to_dataframe(matrix)
    assert df.shape == (5, 5)
    # Higher WACC should result in lower valuation (inverse relationship)
    # Compare top-left vs bottom-left
    assert matrix.price_grid[0, 2] > matrix.price_grid[4, 2]


def test_comps_and_football_field():
    snapshot, _ = FinancialDataManager.get_financial_snapshot("NVDA", force_offline=True)
    comps = ComparableCompanyEngine.calculate_comps_ranges(snapshot)
    assert len(comps) >= 2
    assert comps[0].implied_price_high >= comps[0].implied_price_low

    val_res = DCFValuationEngine.value(snapshot)
    mc_res = MonteCarloValuationEngine(trials=100, seed=42).run(snapshot)
    fig = FootballFieldChartBuilder.build_chart(snapshot, val_res, mc_res)
    assert fig is not None
    assert len(fig.data) >= 1
