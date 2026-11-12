"""
Monte Carlo Probabilistic Valuation Engine for ApexValuation.
Simulates thousands of macroeconomic and operational scenarios to generate
a probability density distribution of intrinsic equity value.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from typing import Optional, List
import numpy as np
from .models import FinancialSnapshot, WACCInputs, MonteCarloResult
from .dcf import DCFValuationEngine


class MonteCarloValuationEngine:
    """Executes stochastic simulations across WACC, terminal growth, and margins."""

    def __init__(self, trials: int = 2_000, seed: int = 42):
        self.trials = trials
        self.seed = seed

    def run(
        self,
        snapshot: FinancialSnapshot,
        wacc_inputs: Optional[WACCInputs] = None,
        base_terminal_growth: float = 0.025,
        base_growth_rates: Optional[List[float]] = None,
        tax_rate: float = 0.25
    ) -> MonteCarloResult:
        """
        Runs N Monte Carlo simulation trials to generate an empirical valuation distribution.
        """
        np.random.seed(self.seed)

        inputs = wacc_inputs or WACCInputs(beta=snapshot.beta)
        base_wacc_res = DCFValuationEngine.calculate_wacc(snapshot, inputs)
        base_wacc = base_wacc_res.wacc

        if base_growth_rates is None:
            base_growth_rates = [0.08, 0.07, 0.06, 0.05, 0.04]

        hist_margin = snapshot.ebit / max(snapshot.revenue, 1.0)
        shares = max(snapshot.shares_outstanding, 1.0)
        net_debt = snapshot.net_debt

        # 1. Stochastic Parameter Sampling
        # WACC: Normal distribution around base WACC (std = 0.75%)
        wacc_samples = np.random.normal(base_wacc, 0.0075, self.trials)
        wacc_samples = np.clip(wacc_samples, 0.055, 0.16)

        # Terminal growth: Normal distribution around base_g (std = 0.4%)
        g_samples = np.random.normal(base_terminal_growth, 0.004, self.trials)
        g_samples = np.clip(g_samples, 0.010, 0.038)

        # Ensure WACC > g by at least 1.0% to avoid division singularity
        g_samples = np.minimum(g_samples, wacc_samples - 0.010)

        # Revenue growth multiplier: lognormal shock around baseline
        growth_multipliers = np.random.normal(1.0, 0.15, self.trials)
        growth_multipliers = np.clip(growth_multipliers, 0.60, 1.50)

        # Margin multiplier: shock to historical operating margin
        margin_multipliers = np.random.normal(1.0, 0.08, self.trials)
        margin_multipliers = np.clip(margin_multipliers, 0.75, 1.25)

        prices = np.zeros(self.trials)

        for i in range(self.trials):
            sim_wacc = wacc_samples[i]
            sim_g = g_samples[i]
            sim_growth_rates = [r * growth_multipliers[i] for r in base_growth_rates]
            sim_margin = hist_margin * margin_multipliers[i]

            projections = DCFValuationEngine.project_free_cash_flows(
                snapshot=snapshot,
                wacc=sim_wacc,
                growth_rates=sim_growth_rates,
                target_ebit_margin=sim_margin,
                tax_rate=tax_rate,
                terminal_growth_rate=sim_g
            )

            sim_ev = projections.sum_pv_ufcf + projections.pv_terminal_value_gordon
            sim_equity = sim_ev - net_debt
            sim_price = sim_equity / shares
            # Disallow negative equity prices
            prices[i] = max(sim_price, 0.01)

        # Statistical analysis
        mean_p = float(np.mean(prices))
        median_p = float(np.median(prices))
        p10 = float(np.percentile(prices, 10))
        p25 = float(np.percentile(prices, 25))
        p75 = float(np.percentile(prices, 75))
        p90 = float(np.percentile(prices, 90))
        std_p = float(np.std(prices))

        undervalued_count = np.sum(prices > snapshot.current_price)
        undervalued_prob = float((undervalued_count / self.trials) * 100.0)

        return MonteCarloResult(
            trials=self.trials,
            prices=prices,
            mean_price=mean_p,
            median_price=median_p,
            p10_price=p10,
            p25_price=p25,
            p75_price=p75,
            p90_price=p90,
            std_price=std_p,
            undervalued_probability_pct=undervalued_prob
        )
