# ApexValuation

A Python tool for 2-stage Discounted Cash Flow (DCF) valuation and Monte Carlo sensitivity analysis.

Most DCF models built in Excel produce a single point estimate for fair value, which makes it easy to overlook how sensitive equity valuations are to small shifts in discount rates or perpetual growth. I built this tool to automate unlevered DCF modeling for public equities (focusing on FTSE 100 and US large-cap names) and run Monte Carlo simulations to generate a probability distribution of fair value rather than relying on one static price.

---

## What It Does

1. **2-Stage Unlevered DCF**:
   - Forecasts 5-year Unlevered Free Cash Flows (UFCF / Free Cash Flow to Firm).
   - Uses mid-year convention discounting to account for continuous cash generation through the fiscal year.
   - Calculates WACC via CAPM ($r_e = r_f + \beta \times \text{ERP}$) using historical equity beta and tax-adjusted cost of debt.
   - Values terminal value via both Perpetual Growth (Gordon Growth) and Exit Multiples (EV/EBITDA).
   - Bridges Enterprise Value to Equity Value by accounting for net debt.

2. **Monte Carlo Sensitivity Analysis**:
   - Instead of a single DCF price, the engine runs 1,500 random simulation trials.
   - WACC, terminal growth ($g$), and revenue growth rates are shocked simultaneously using normal distributions.
   - Outputs a probability distribution curve showing the median fair value, 10th-90th percentile ranges, and the probability that the stock is undervalued at current market prices.

3. **Investment Banking Valuation Synthesis**:
   - Plots a horizontal "Football Field" chart comparing 52-week trading ranges, Gordon Growth DCF, Exit Multiple DCF, Comps (EV/EBITDA, P/E), and Monte Carlo interquartile ranges.
   - Generates a 5x5 WACC vs terminal growth sensitivity matrix.

4. **Interactive Dashboard**:
   - Built with Streamlit and Plotly to make it easy to tweak inputs (revenue growth, margins, discount rates) and watch the valuation distribution update in real time.

---

## Installation & Usage

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/alekseidurham/apex-valuation.git
cd apex-valuation

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
This opens an interactive dashboard in your browser where you can pick any ticker (e.g. `SHEL.L`, `AAPL`, `MSFT`, `BP.L`) or input custom financial assumptions.

### 3. Run via CLI
You can also run a quick valuation directly from the terminal:
```bash
python run_valuation.py --ticker SHEL.L
```

---

## Valuation Logic & Assumptions

* **Free Cash Flow to Firm (UFCF):**
  $$\text{UFCF} = \text{EBIT} \times (1 - t) + \text{D\&A} - \text{CapEx} - \Delta\text{NWC}$$
* **WACC (CAPM):**
  $$\text{Cost of Equity} = r_f + \beta \times \text{ERP}$$
  Default parameters: $r_f = 4.2\%$, $\text{ERP} = 5.5\%$, corporate tax rate $t = 25\%$.
* **Gordon Growth Terminal Value:**
  $$TV = \frac{\text{UFCF}_5 \times (1 + g)}{\text{WACC} - g}$$
  Terminal growth rate $g$ is conservatively bounded by long-term GDP growth (default 2.0%–2.5%).
* **Enterprise to Equity Value Bridge:**
  $$\text{Equity Value} = \text{Enterprise Value} - \text{Total Debt} + \text{Cash}$$
  $$\text{Fair Value Per Share} = \frac{\text{Equity Value}}{\text{Shares Outstanding}}$$

---

## Project Structure

```
apex-valuation/
├── apex_valuation/
│   ├── data.py             # Statement extraction and offline fallback data
│   ├── dcf.py              # 2-stage DCF valuation and WACC engine
│   ├── monte_carlo.py      # Stochastic Monte Carlo simulation
│   ├── sensitivity.py      # 5x5 WACC vs growth sensitivity matrix
│   ├── comps.py            # Peer multiples (EV/EBITDA, P/E)
│   └── football_field.py   # Plotly football field chart builder
├── tests/
│   └── test_valuation.py   # Unit tests (pytest)
├── app.py                  # Streamlit web app
├── run_valuation.py        # Command-line runner
└── requirements.txt
```

---

## Running Tests
To verify all calculations and simulation routines:
```bash
pytest tests/ -v
```

---

## Author
**Aleksei Rogozin**  
BSc Finance, Durham University  
M&A Researcher at Durham University Finance Society (DUFS)  
Contact: aleksei.rogozin@durham.ac.uk
