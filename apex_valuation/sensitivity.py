"""
Sensitivity Analysis Matrix Engine for M&A Valuation Tables.
Generates institutional 2D sensitivity grids (WACC vs Terminal Growth Rate).
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from .models import FinancialSnapshot, WACCInputs, SensitivityMatrix
from .dcf import DCFValuationEngine


class SensitivityAnalysisEngine:
    """Builds two-way data tables for WACC and Terminal Growth rate sensitivities."""

    @classmethod
    def generate_matrix(
        cls,
        snapshot: FinancialSnapshot,
        base_wacc: float,
        base_growth: float = 0.025,
        wacc_step: float = 0.005,      # 0.5% steps
        growth_step: float = 0.0025,   # 0.25% steps
        grid_size: int = 5,
        tax_rate: float = 0.25
    ) -> SensitivityMatrix:
        """
        Calculates an N x N matrix of implied share prices.
        """
        half = grid_size // 2
        wacc_rates = [base_wacc + (i - half) * wacc_step for i in range(grid_size)]
        growth_rates = [base_growth + (j - half) * growth_step for j in range(grid_size)]

        shares = max(snapshot.shares_outstanding, 1.0)
        net_debt = snapshot.net_debt

        price_grid = np.zeros((grid_size, grid_size))

        for i, w in enumerate(wacc_rates):
            for j, g in enumerate(growth_rates):
                if w <= g + 0.005:
                    # Guard against non-convergent perpetual growth
                    price_grid[i, j] = np.nan
                    continue

                projections = DCFValuationEngine.project_free_cash_flows(
                    snapshot=snapshot,
                    wacc=w,
                    terminal_growth_rate=g,
                    tax_rate=tax_rate
                )

                ev = projections.sum_pv_ufcf + projections.pv_terminal_value_gordon
                equity = ev - net_debt
                implied_price = max(equity / shares, 0.0)
                price_grid[i, j] = float(implied_price)

        return SensitivityMatrix(
            wacc_rates=wacc_rates,
            growth_rates=growth_rates,
            price_grid=price_grid
        )

    @classmethod
    def to_dataframe(cls, matrix: SensitivityMatrix) -> pd.DataFrame:
        """Formats the SensitivityMatrix into a clean formatted pandas DataFrame."""
        wacc_labels = [f"WACC: {w * 100:.2f}%" for w in matrix.wacc_rates]
        growth_labels = [f"g: {g * 100:.2f}%" for g in matrix.growth_rates]

        df = pd.DataFrame(
            matrix.price_grid,
            index=wacc_labels,
            columns=growth_labels
        )
        return df
