"""
2-Stage Unlevered Discounted Cash Flow (DCF) & CAPM WACC Valuation Engine.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from typing import List, Optional, Tuple
import numpy as np
from .models import (
    FinancialSnapshot,
    WACCInputs,
    WACCResult,
    DCFProjections,
    ValuationResult,
)


class DCFValuationEngine:
    """Computes WACC, 5-year cash flow projections, and dual-method terminal valuations."""

    @staticmethod
    def calculate_wacc(
        snapshot: FinancialSnapshot,
        inputs: WACCInputs
    ) -> WACCResult:
        """
        Calculates WACC using the Capital Asset Pricing Model (CAPM).
        Cost of Equity: r_e = r_f + beta * ERP
        Cost of Debt after tax: r_d * (1 - t)
        """
        # CAPM Cost of Equity
        beta = inputs.beta if inputs.beta > 0 else snapshot.beta
        cost_of_equity = inputs.risk_free_rate + (beta * inputs.equity_risk_premium)

        # After-Tax Cost of Debt
        cost_of_debt_after_tax = inputs.cost_of_debt_pre_tax * (1.0 - inputs.effective_tax_rate)

        # Capital Structure Weights
        equity_val = max(snapshot.market_cap, 1.0)
        debt_val = max(snapshot.total_debt, 0.0)
        total_cap = equity_val + debt_val

        weight_equity = equity_val / total_cap
        weight_debt = debt_val / total_cap

        wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt_after_tax)

        return WACCResult(
            cost_of_equity=float(cost_of_equity),
            cost_of_debt_after_tax=float(cost_of_debt_after_tax),
            weight_equity=float(weight_equity),
            weight_debt=float(weight_debt),
            wacc=float(wacc),
        )

    @classmethod
    def project_free_cash_flows(
        cls,
        snapshot: FinancialSnapshot,
        wacc: float,
        growth_rates: Optional[List[float]] = None,
        target_ebit_margin: Optional[float] = None,
        tax_rate: float = 0.25,
        terminal_growth_rate: float = 0.025,
        exit_multiple: float = 11.0,
        projection_years: int = 5
    ) -> DCFProjections:
        """
        Projects 5-Year Unlevered Free Cash Flows (UFCF) and discounts to Present Value.
        UFCF = EBIT*(1-t) + D&A - CapEx - ChangeInNWC
        """
        if growth_rates is None:
            # Conservative default revenue trajectory tapering down
            growth_rates = [0.08, 0.07, 0.06, 0.05, 0.04]

        # Historical structural ratios
        hist_rev = snapshot.revenue
        hist_margin = snapshot.ebit / max(hist_rev, 1.0)
        ebit_margin = target_ebit_margin if target_ebit_margin is not None else hist_margin
        ebit_margin = max(0.05, min(ebit_margin, 0.65))

        da_ratio = snapshot.d_and_a / max(hist_rev, 1.0)
        capex_ratio = snapshot.capex / max(hist_rev, 1.0)
        nwc_ratio = snapshot.nwc / max(hist_rev, 1.0)

        revenues = []
        ebits = []
        nopats = []
        ufcfs = []
        discount_factors = []
        pv_ufcfs = []

        cur_rev = hist_rev
        years = list(range(1, projection_years + 1))

        for yr_idx in range(projection_years):
            g = growth_rates[yr_idx] if yr_idx < len(growth_rates) else growth_rates[-1]
            prev_rev = cur_rev
            cur_rev = cur_rev * (1.0 + g)
            delta_rev = cur_rev - prev_rev

            ebit_t = cur_rev * ebit_margin
            nopat_t = ebit_t * (1.0 - tax_rate)
            da_t = cur_rev * da_ratio
            capex_t = cur_rev * capex_ratio
            delta_nwc_t = delta_rev * nwc_ratio

            ufcf_t = nopat_t + da_t - capex_t - delta_nwc_t

            # Mid-year convention discounting: (t - 0.5)
            t = yr_idx + 0.5
            df_t = 1.0 / ((1.0 + wacc) ** t)
            pv_t = ufcf_t * df_t

            revenues.append(cur_rev)
            ebits.append(ebit_t)
            nopats.append(nopat_t)
            ufcfs.append(ufcf_t)
            discount_factors.append(df_t)
            pv_ufcfs.append(pv_t)

        sum_pv_ufcf = float(np.sum(pv_ufcfs))

        # Terminal Value - Method 1: Perpetual Growth (Gordon Growth)
        # TV = UFCF_5 * (1 + g) / (WACC - g)
        last_ufcf = ufcfs[-1]
        denom = max(wacc - terminal_growth_rate, 0.005)
        tv_gordon = (last_ufcf * (1.0 + terminal_growth_rate)) / denom
        # Discount from end of year 5
        pv_tv_gordon = tv_gordon / ((1.0 + wacc) ** projection_years)

        # Terminal Value - Method 2: Exit Multiple (EV/EBITDA)
        last_ebit = ebits[-1]
        last_da = revenues[-1] * da_ratio
        last_ebitda = last_ebit + last_da
        tv_multiple = last_ebitda * exit_multiple
        pv_tv_multiple = tv_multiple / ((1.0 + wacc) ** projection_years)

        return DCFProjections(
            years=years,
            revenues=revenues,
            ebit=ebits,
            nopat=nopats,
            ufcf=ufcfs,
            discount_factors=discount_factors,
            pv_ufcf=pv_ufcfs,
            sum_pv_ufcf=sum_pv_ufcf,
            terminal_value_gordon=float(tv_gordon),
            pv_terminal_value_gordon=float(pv_tv_gordon),
            terminal_value_multiple=float(tv_multiple),
            pv_terminal_value_multiple=float(pv_tv_multiple),
        )

    @classmethod
    def value(
        cls,
        snapshot: FinancialSnapshot,
        wacc_inputs: Optional[WACCInputs] = None,
        growth_rates: Optional[List[float]] = None,
        target_ebit_margin: Optional[float] = None,
        terminal_growth_rate: float = 0.025,
        exit_multiple: float = 11.0,
        tax_rate: float = 0.25
    ) -> ValuationResult:
        """
        Executes end-to-end DCF valuation and bridges Enterprise Value to Equity Value.
        Enterprise Value = PV(Cash Flows) + PV(Terminal Value)
        Equity Value = Enterprise Value - Total Debt + Cash
        Implied Share Price = Equity Value / Shares Outstanding
        """
        inputs = wacc_inputs or WACCInputs(beta=snapshot.beta)
        wacc_res = cls.calculate_wacc(snapshot, inputs)
        wacc = wacc_res.wacc

        projections = cls.project_free_cash_flows(
            snapshot=snapshot,
            wacc=wacc,
            growth_rates=growth_rates,
            target_ebit_margin=target_ebit_margin,
            tax_rate=tax_rate,
            terminal_growth_rate=terminal_growth_rate,
            exit_multiple=exit_multiple
        )

        shares = max(snapshot.shares_outstanding, 1.0)
        net_debt = snapshot.net_debt

        # 1. Gordon Growth Model Valuation Bridge
        ev_gordon = projections.sum_pv_ufcf + projections.pv_terminal_value_gordon
        equity_gordon = ev_gordon - net_debt
        price_gordon = equity_gordon / shares
        upside_gordon = ((price_gordon - snapshot.current_price) / snapshot.current_price) * 100.0

        # 2. Exit Multiple Model Valuation Bridge
        ev_multiple = projections.sum_pv_ufcf + projections.pv_terminal_value_multiple
        equity_multiple = ev_multiple - net_debt
        price_multiple = equity_multiple / shares
        upside_multiple = ((price_multiple - snapshot.current_price) / snapshot.current_price) * 100.0

        return ValuationResult(
            ticker=snapshot.ticker,
            company_name=snapshot.company_name,
            current_price=snapshot.current_price,
            wacc=float(wacc),
            terminal_growth_rate=float(terminal_growth_rate),
            exit_multiple=float(exit_multiple),
            enterprise_value_gordon=float(ev_gordon),
            equity_value_gordon=float(equity_gordon),
            implied_price_gordon=float(price_gordon),
            upside_gordon_pct=float(upside_gordon),
            enterprise_value_multiple=float(ev_multiple),
            equity_value_multiple=float(equity_multiple),
            implied_price_multiple=float(price_multiple),
            upside_multiple_pct=float(upside_multiple),
            projections=projections,
        )
