"""
Core Data Models and Type Definitions for ApexValuation Engine.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class FinancialSnapshot:
    """Historical and current balance sheet / income statement items."""
    ticker: str
    company_name: str
    currency: str
    current_price: float
    shares_outstanding: float
    revenue: float
    ebit: float
    ebitda: float
    net_income: float
    d_and_a: float
    capex: float
    nwc: float
    total_debt: float
    cash_and_equivalents: float
    beta: float

    @property
    def market_cap(self) -> float:
        return self.current_price * self.shares_outstanding

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash_and_equivalents

    @property
    def enterprise_value_market(self) -> float:
        return self.market_cap + self.net_debt


@dataclass
class WACCInputs:
    """Parameters used to compute Weighted Average Cost of Capital via CAPM."""
    risk_free_rate: float = 0.042       # 10-Year Benchmark Yield
    equity_risk_premium: float = 0.055  # Long-term ERP (Damodaran consensus)
    beta: float = 1.05
    cost_of_debt_pre_tax: float = 0.052 # Corporate borrowing rate
    effective_tax_rate: float = 0.25    # Corporate income tax rate


@dataclass
class WACCResult:
    """Calculated components of WACC."""
    cost_of_equity: float
    cost_of_debt_after_tax: float
    weight_equity: float
    weight_debt: float
    wacc: float


@dataclass
class DCFProjections:
    """5-Year Unlevered Free Cash Flow (UFCF) projections and discount breakdown."""
    years: List[int]
    revenues: List[float]
    ebit: List[float]
    nopat: List[float]
    ufcf: List[float]
    discount_factors: List[float]
    pv_ufcf: List[float]
    sum_pv_ufcf: float
    terminal_value_gordon: float
    pv_terminal_value_gordon: float
    terminal_value_multiple: float
    pv_terminal_value_multiple: float


@dataclass
class ValuationResult:
    """Final intrinsic valuation metrics and comparison to market price."""
    ticker: str
    company_name: str
    current_price: float
    wacc: float
    terminal_growth_rate: float
    exit_multiple: float
    # Gordon Growth Model Outputs
    enterprise_value_gordon: float
    equity_value_gordon: float
    implied_price_gordon: float
    upside_gordon_pct: float
    # Exit Multiple Outputs
    enterprise_value_multiple: float
    equity_value_multiple: float
    implied_price_multiple: float
    upside_multiple_pct: float
    projections: DCFProjections


@dataclass
class MonteCarloResult:
    """Probabilistic valuation distribution generated from N random simulations."""
    trials: int
    prices: np.ndarray
    mean_price: float
    median_price: float
    p10_price: float
    p25_price: float
    p75_price: float
    p90_price: float
    std_price: float
    undervalued_probability_pct: float


@dataclass
class SensitivityMatrix:
    """2D Grid of Implied Share Prices across WACC and Terminal Growth Rate."""
    wacc_rates: List[float]
    growth_rates: List[float]
    price_grid: np.ndarray  # Shape: (len(wacc_rates), len(growth_rates))
