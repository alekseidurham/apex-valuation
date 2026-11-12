"""
ApexValuation: Institutional M&A & DCF Engine with Monte Carlo Sensitivity Analysis
Author: Aleksei Rogozin (Durham University / DUFS M&A)
License: MIT
"""

from .models import (
    FinancialSnapshot,
    WACCInputs,
    WACCResult,
    DCFProjections,
    ValuationResult,
    MonteCarloResult,
    SensitivityMatrix,
)
from .data import FinancialDataManager
from .dcf import DCFValuationEngine
from .monte_carlo import MonteCarloValuationEngine
from .sensitivity import SensitivityAnalysisEngine
from .comps import ComparableCompanyEngine

__version__ = "1.0.0"
__author__ = "Aleksei Rogozin"

__all__ = [
    "FinancialSnapshot",
    "WACCInputs",
    "WACCResult",
    "DCFProjections",
    "ValuationResult",
    "MonteCarloResult",
    "SensitivityMatrix",
    "FinancialDataManager",
    "DCFValuationEngine",
    "MonteCarloValuationEngine",
    "SensitivityAnalysisEngine",
    "ComparableCompanyEngine",
]
