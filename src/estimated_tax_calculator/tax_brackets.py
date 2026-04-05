"""Federal tax bracket data and constants for 2025 and 2026.

All bracket data sourced from IRS Rev. Proc. 2024-40 for tax year 2025,
and Rev. Proc. 2024-42 / 2026 projections for tax year 2026.
"""

from enum import Enum


class FilingStatus(str, Enum):
    """Tax filing status options."""

    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"


# Standard Deduction by Tax Year
STANDARD_DEDUCTION: dict[int, dict[FilingStatus, float]] = {
    2025: {
        FilingStatus.SINGLE: 15_750.0,
        FilingStatus.MARRIED_FILING_JOINTLY: 31_500.0,
    },
    2026: {
        FilingStatus.SINGLE: 16_100.0,
        FilingStatus.MARRIED_FILING_JOINTLY: 32_200.0,
    },
}

# Federal Ordinary Income Tax Brackets by Tax Year
# Each entry is (upper_bound, rate). The last entry uses float("inf").
ORDINARY_BRACKETS: dict[int, dict[FilingStatus, list[tuple[float, float]]]] = {
    2025: {
        FilingStatus.SINGLE: [
            (11_925.0, 0.10),
            (48_475.0, 0.12),
            (103_350.0, 0.22),
            (197_300.0, 0.24),
            (250_525.0, 0.32),
            (626_350.0, 0.35),
            (float("inf"), 0.37),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            (23_850.0, 0.10),
            (96_950.0, 0.12),
            (206_700.0, 0.22),
            (394_600.0, 0.24),
            (501_050.0, 0.32),
            (751_600.0, 0.35),
            (float("inf"), 0.37),
        ],
    },
    2026: {
        FilingStatus.SINGLE: [
            (12_400.0, 0.10),
            (50_400.0, 0.12),
            (105_700.0, 0.22),
            (201_775.0, 0.24),
            (256_225.0, 0.32),
            (640_600.0, 0.35),
            (float("inf"), 0.37),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            (24_800.0, 0.10),
            (100_800.0, 0.12),
            (211_400.0, 0.22),
            (403_550.0, 0.24),
            (512_450.0, 0.32),
            (768_700.0, 0.35),
            (float("inf"), 0.37),
        ],
    },
}

# Long-Term Capital Gains Tax Brackets by Tax Year
LTCG_BRACKETS: dict[int, dict[FilingStatus, list[tuple[float, float]]]] = {
    2025: {
        FilingStatus.SINGLE: [
            (48_350.0, 0.00),
            (533_400.0, 0.15),
            (float("inf"), 0.20),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            (96_700.0, 0.00),
            (600_050.0, 0.15),
            (float("inf"), 0.20),
        ],
    },
    2026: {
        # Using 2026 inflation projections for LTCG
        FilingStatus.SINGLE: [
            (49_500.0, 0.00),
            (545_600.0, 0.15),
            (float("inf"), 0.20),
        ],
        FilingStatus.MARRIED_FILING_JOINTLY: [
            (99_000.0, 0.00),
            (613_850.0, 0.15),
            (float("inf"), 0.20),
        ],
    },
}

# Net Investment Income Tax (NIIT)
# 3.8% surtax on the lesser of net investment income or
# the excess of MAGI over the threshold. (Not indexed for inflation)
NIIT_RATE: float = 0.038
NIIT_THRESHOLD: dict[FilingStatus, float] = {
    FilingStatus.SINGLE: 200_000.0,
    FilingStatus.MARRIED_FILING_JOINTLY: 250_000.0,
}

# Supplemental income withholding rates (federal)
SUPPLEMENTAL_WITHHOLDING_RATE: float = 0.22
SUPPLEMENTAL_WITHHOLDING_RATE_OVER_1M: float = 0.37
