"""
Comparable Company Multiples (Comps) & Peer Valuation Range Engine.
Computes EV/EBITDA, P/E, and EV/Revenue implied valuation ranges for target companies.
Author: Aleksei Rogozin (Durham University / DUFS M&A)
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from .models import FinancialSnapshot


@dataclass
class PeerMultipleRange:
    multiple_name: str
    low_multiple: float
    high_multiple: float
    implied_price_low: float
    implied_price_high: float


class ComparableCompanyEngine:
    """Calculates relative valuation ranges based on industry peer multiples."""

    # Default industry multiple benchmarks
    SECTOR_MULTIPLES = {
        "TECH": {
            "EV_EBITDA": (14.0, 22.0),
            "PE": (22.0, 32.0),
            "EV_REV": (5.0, 9.0),
        },
        "ENERGY": {
            "EV_EBITDA": (4.5, 7.5),
            "PE": (8.0, 13.0),
            "EV_REV": (0.8, 1.6),
        },
        "FINANCIALS": {
            "EV_EBITDA": (6.0, 10.0),
            "PE": (9.0, 14.0),
            "EV_REV": (1.5, 3.0),
        },
        "GENERAL": {
            "EV_EBITDA": (8.0, 14.0),
            "PE": (15.0, 24.0),
            "EV_REV": (1.8, 3.5),
        }
    }

    @classmethod
    def infer_sector(cls, ticker: str) -> str:
        clean = ticker.upper()
        if clean in ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN"]:
            return "TECH"
        elif clean in ["SHEL.L", "BP.L", "XOM", "CVX", "TTE"]:
            return "ENERGY"
        elif clean in ["BARC.L", "LLOY.L", "HSBA.L", "JPM", "BAC"]:
            return "FINANCIALS"
        return "GENERAL"

    @classmethod
    def calculate_comps_ranges(
        cls,
        snapshot: FinancialSnapshot,
        sector: Optional[str] = None
    ) -> List[PeerMultipleRange]:
        """
        Derives implied share prices across EV/EBITDA, P/E, and EV/Revenue.
        """
        sec = sector or cls.infer_sector(snapshot.ticker)
        multiples = cls.SECTOR_MULTIPLES.get(sec, cls.SECTOR_MULTIPLES["GENERAL"])

        shares = max(snapshot.shares_outstanding, 1.0)
        net_debt = snapshot.net_debt

        results = []

        # 1. EV / EBITDA Multiples
        ev_ebitda_low, ev_ebitda_high = multiples["EV_EBITDA"]
        ebitda = max(snapshot.ebitda, 1.0)
        price_ebitda_low = max((ebitda * ev_ebitda_low - net_debt) / shares, 0.0)
        price_ebitda_high = max((ebitda * ev_ebitda_high - net_debt) / shares, 0.0)
        results.append(
            PeerMultipleRange(
                multiple_name="EV / EBITDA",
                low_multiple=ev_ebitda_low,
                high_multiple=ev_ebitda_high,
                implied_price_low=float(price_ebitda_low),
                implied_price_high=float(price_ebitda_high)
            )
        )

        # 2. Price / Earnings (P/E) Multiples
        pe_low, pe_high = multiples["PE"]
        eps = max(snapshot.net_income / shares, 0.01)
        price_pe_low = max(eps * pe_low, 0.0)
        price_pe_high = max(eps * pe_high, 0.0)
        results.append(
            PeerMultipleRange(
                multiple_name="P / E Multiple",
                low_multiple=pe_low,
                high_multiple=pe_high,
                implied_price_low=float(price_pe_low),
                implied_price_high=float(price_pe_high)
            )
        )

        # 3. EV / Revenue Multiples
        ev_rev_low, ev_rev_high = multiples["EV_REV"]
        rev = max(snapshot.revenue, 1.0)
        price_rev_low = max((rev * ev_rev_low - net_debt) / shares, 0.0)
        price_rev_high = max((rev * ev_rev_high - net_debt) / shares, 0.0)
        results.append(
            PeerMultipleRange(
                multiple_name="EV / Revenue",
                low_multiple=ev_rev_low,
                high_multiple=ev_rev_high,
                implied_price_low=float(price_rev_low),
                implied_price_high=float(price_rev_high)
            )
        )

        return results
