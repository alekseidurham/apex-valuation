# ApexValuation

A quantitative corporate valuation and risk modeling toolkit implementing 2-stage Unlevered DCF (FCFF), stochastic Monte Carlo uncertainty distributions, and peer trading multiples.

---

## Overview

Traditional Discounted Cash Flow (DCF) models in corporate finance typically suffer from *point-estimate fragility*: a single deterministic equity value that masks extreme sensitivity to discount rates ($WACC$) and terminal growth rates ($g$). In live transactions, a 50 bps shift in cost of capital can alter fair value by 20% to 35%.

**ApexValuation** bridges institutional 2-stage Free Cash Flow to Firm (FCFF) modeling with probabilistic Monte Carlo simulation, peer trading multiples (Comps), and investment banking Football Field synthesis. It allows analysts and researchers to evaluate not just a single fair price, but an entire probability density distribution of valuation outcomes and margin-of-safety metrics.

---

## Key Capabilities

* **2-Stage Unlevered DCF Engine**: 
  * Forecasts discrete 5-year Unlevered Free Cash Flows (UFCF) with automated NOPAT, CapEx, D&A, and net working capital ($\Delta\text{NWC}$) reconciliation.
  * Implements **mid-year convention discounting** to reflect continuous cash flow generation throughout the fiscal year.
  * Calculates capital structure weights using current market enterprise values.
* **CAPM WACC Module**:
  * Derives cost of equity via the Capital Asset Pricing Model ($r_e = r_f + \beta \times \text{ERP}$).
  * Applies after-tax corporate debt shielding: $r_d \times (1 - t)$.
* **Dual Terminal Value Methodology**:
  * **Perpetual Growth Model (Gordon Growth)**: Conservatively bounded by long-term macroeconomic GDP growth rates.
  * **Exit Multiple Model**: Based on normalized terminal EV/EBITDA multiples.
* **Stochastic Monte Carlo Risk Engine**:
  * Executes 1,500+ simulation trials subjecting WACC, terminal growth, revenue trajectory, and operating margins to simultaneous Gaussian shocks.
  * Calculates interquartile valuation bands (10th, 25th, 50th, 75th, 90th percentiles) and empirical probability of undervaluation: $\mathbb{P}(\text{Fair Value} > \text{Market Price})$.
* **Investment Banking Football Field & Sensitivity Analysis**:
  * Synthesizes 52-week market trading ranges, DCF Gordon Growth, DCF Exit Multiples, Comps (EV/EBITDA, P/E), and Monte Carlo ranges into an interactive Plotly horizontal float chart.
  * Generates a 2D 5x5 WACC vs. terminal growth rate sensitivity heatmap.
* **Interactive Web Interface & CLI Runner**:
  * Dark-mode Streamlit dashboard for dynamic scenario analysis and executive presentations.
  * Standalone CLI runner with formatted terminal reporting.

---

## Python API Usage

```python
from apex_valuation import FinancialDataManager, DCFValuationEngine, MonteCarloValuationEngine

# 1. Ingest corporate balance sheet & cash flow data
snapshot, is_fallback = FinancialDataManager.get_financial_snapshot("SHEL.L")

# 2. Compute 2-Stage Unlevered DCF
valuation = DCFValuationEngine.value(
    snapshot=snapshot,
    terminal_growth_rate=0.025,
    exit_multiple=11.0
)

print(f"Target: {snapshot.company_name} ({snapshot.ticker})")
print(f"Calculated WACC: {valuation.wacc * 100:.2f}%")
print(f"Implied Share Price (Gordon): {snapshot.currency} {valuation.implied_price_gordon:.2f}")
print(f"Implied Share Price (Multiple): {snapshot.currency} {valuation.implied_price_multiple:.2f}")

# 3. Run Monte Carlo stochastic simulation (1,500 trials)
mc = MonteCarloValuationEngine(trials=1500, seed=42).run(snapshot)
print(f"Monte Carlo Median Value: {snapshot.currency} {mc.median_price:.2f}")
print(f"25th - 75th Percentile Range: {snapshot.currency} {mc.p25_price:.2f} - {mc.p75_price:.2f}")
print(f"Probability of Undervaluation: {mc.undervalued_probability_pct:.1f}%")
```

---

## Command Line Interface (CLI)

Run an immediate valuation on any corporate target:

```bash
python run_valuation.py --ticker SHEL.L
```

### Sample Terminal Output:

```text
==============================================================================
      APEX VALUATION: INSTITUTIONAL M&A & DCF ENGINE (MONTE CARLO)
      Research by: Aleksei Rogozin | Durham University (BSc Finance)
==============================================================================

[1/4] Ingesting Corporate Financials for Target: SHEL.L...
      -> Company Name:    Shell plc
      -> Current Price:   GBP 26.80
      -> Market Cap:      GBP 167.23B
      -> Revenue (LTM):   GBP 242.10B
      -> Operating EBIT:  GBP 36.40B
      -> Total Net Debt:  GBP 25.50B
      -> Data Ingestion:  Live yfinance Corporate Feed

[2/4] Executing 2-Stage DCF Valuation (CAPM WACC & 5-Year UFCF)...
      -> Calculated WACC:         7.22%
      -> Sum PV of 5-Yr UFCF:     GBP 131.69B
      -> PV of Terminal Value (g):GBP 530.04B
      -> Implied Price (Gordon):  GBP 101.96 (+280.5%)
      -> Implied Price (Multiple):GBP 107.21 (+300.0%)

[3/4] Running Monte Carlo Probabilistic Simulation (1,500 trials)...
      -> Median Value:            GBP 101.45
      -> 25th - 75th %ile Range:  GBP 88.57 - GBP 116.08
      -> 10th - 90th %ile Range:  GBP 78.39 - GBP 132.81
      -> Undervaluation Odds:     100.0%

[4/4] Calculating Comparable Peer Multiples (Comps)...
      -> EV / EBITDA      (4.5x - 7.5x):  GBP 35.00 - GBP 61.06
      -> P / E Multiple   (8.0x - 13.0x): GBP 36.22 - GBP 58.85
      -> EV / Revenue     (0.8x - 1.6x):  GBP 26.95 - GBP 57.99

==============================================================================
                    EXECUTIVE M&A VALUATION SUMMARY
==============================================================================
  Target Company:             Shell plc (SHEL.L)
  Current Market Price:       GBP 26.80
  DCF Fair Value (Gordon):    GBP 101.96  | Upside: +280.5%
  DCF Fair Value (Multiple):  GBP 107.21  | Upside: +300.0%
  Monte Carlo Median Price:   GBP 101.45  | Odds of Undervaluation: 100.0%
  Strategic M&A Assessment:   ATTRACTIVE ENTRY (UNDERVALUED)
==============================================================================
```

---

## Interactive Streamlit Dashboard

To launch the dark-mode interactive web dashboard:

```bash
streamlit run app.py
```

The application provides:
* Dynamic input sliders for cost of capital, growth rates, margins, and tax assumptions.
* Plotly Football Field valuation range visual.
* Monte Carlo probability density histogram with current price overlay.
* 5x5 WACC vs. Perpetual Growth sensitivity heatmap.
* 5-year projected financial statements and an Enterprise Value to Equity Value bridge table.

---

## Mathematical Specification

### 1. Unlevered Free Cash Flow (FCFF)
$$\text{UFCF}_t = \text{EBIT}_t \times (1 - t) + \text{D\&A}_t - \text{CapEx}_t - \Delta\text{NWC}_t$$

Discounted via the mid-year convention:
$$PV(\text{UFCF}_t) = \frac{\text{UFCF}_t}{(1 + WACC)^{t - 0.5}}$$

### 2. Weighted Average Cost of Capital (WACC)
$$WACC = \left(\frac{E}{E + D} \times r_e\right) + \left(\frac{D}{E + D} \times r_d \times (1 - t)\right)$$

where cost of equity $r_e$ is derived via the Capital Asset Pricing Model:
$$r_e = r_f + \beta \times \text{ERP}$$
*(Baseline assumptions: $r_f = 4.2\%$, $\text{ERP} = 5.5\%$, $t = 25\%$)*.

### 3. Dual-Method Terminal Value (TV)
* **Gordon Growth Model:**
  $$TV_{Gordon} = \frac{\text{UFCF}_5 \times (1 + g)}{WACC - g}, \quad g \le 2.5\%$$
* **Exit Multiple Model:**
  $$TV_{Multiple} = \text{EBITDA}_5 \times \text{EV/EBITDA Multiple}$$
* **Discounted Terminal Value:**
  $$PV(TV) = \frac{TV}{(1 + WACC)^5}$$

### 4. Enterprise Value to Equity Value Bridge
$$\text{Enterprise Value (EV)} = \sum_{t=1}^5 PV(\text{UFCF}_t) + PV(TV)$$
$$\text{Equity Value} = \text{Enterprise Value} - \text{Total Debt} + \text{Cash \& Equivalents}$$
$$\text{Implied Fair Value Per Share} = \frac{\text{Equity Value}}{\text{Diluted Shares Outstanding}}$$

---

## Empirical Benchmark Comparisons

| Target Company | Ticker | Current Price | Calculated WACC | DCF Gordon Fair Value | Monte Carlo Median | Undervaluation Odds |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Shell plc** | `SHEL.L` | GBP 26.80 | 7.22% | **GBP 101.96** (+280%) | GBP 101.45 | **100.0%** (Deep Value) |
| **BP p.l.c.** | `BP.L` | GBP 4.15 | 7.64% | **GBP 14.82** (+257%) | GBP 14.65 | **100.0%** (Value Play) |
| **Apple Inc.** | `AAPL` | USD 225.50 | 10.05% | **USD 87.25** (-61%) | USD 86.77 | **0.0%** (Growth Premium) |
| **Microsoft Corp** | `MSFT` | USD 420.00 | 9.60% | **USD 385.10** (-8%) | USD 382.50 | **42.5%** (Fair Value) |

---

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/alekseidurham/apex-valuation.git
cd apex-valuation

# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest tests/ -v
```

---

## Project Structure

```
apex-valuation/
├── apex_valuation/
│   ├── __init__.py           # Package exports & public API
│   ├── models.py             # Strongly-typed financial dataclasses
│   ├── data.py               # Statement normalization & offline benchmark database
│   ├── dcf.py                # 2-stage DCF valuation and CAPM WACC engine
│   ├── monte_carlo.py        # 1,500-trial stochastic valuation simulator
│   ├── sensitivity.py        # 2D WACC vs. growth sensitivity matrix
│   ├── comps.py              # Comparable company multiples (EV/EBITDA, P/E)
│   └── football_field.py     # Plotly horizontal range chart builder
├── tests/
│   └── test_valuation.py     # Unit test suite (pytest)
├── app.py                    # Dark-mode Streamlit dashboard
├── run_valuation.py          # Command-line execution entry point
├── pyproject.toml            # Project packaging specification
├── requirements.txt          # Pinned dependency requirements
└── README.md
```

---

## Author

**Aleksei Rogozin**  
BSc Finance, Durham University  
M&A Researcher at Durham University Finance Society (DUFS)  
Contact: [aleksei.rogozin@durham.ac.uk](mailto:aleksei.rogozin@durham.ac.uk) | [LinkedIn](https://www.linkedin.com/in/aleksei-rogozin/)
