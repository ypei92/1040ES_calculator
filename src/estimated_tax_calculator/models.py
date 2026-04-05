"""Pydantic models for tax calculation inputs and outputs."""

from pydantic import BaseModel, Field

from estimated_tax_calculator.tax_brackets import FilingStatus


class TaxInput(BaseModel):
    """All user-provided inputs for the 1040ES calculation."""

    tax_year: int = Field(
        default=2026,
        description="Tax year for calculation",
    )
    filing_status: FilingStatus = Field(
        default=FilingStatus.SINGLE,
        description="Tax filing status",
    )

    # Income (YTD + projections)
    ytd_tax_withheld: float = Field(
        ge=0,
        description="Year-to-date federal tax already withheld",
    )
    ytd_taxable_income: float = Field(
        ge=0,
        description="Year-to-date taxable income from paystubs",
    )
    remaining_paychecks: int = Field(
        ge=0,
        description="Number of remaining paychecks this year",
    )
    estimated_income_per_paycheck: float = Field(
        ge=0,
        description="Estimated taxable income per remaining paycheck",
    )
    estimated_withholding_per_paycheck: float = Field(
        ge=0,
        description="Estimated federal withholding per remaining paycheck",
    )

    # RSU / Company equity
    remaining_unvested_shares: int = Field(
        default=0,
        ge=0,
        description="Number of remaining unvested company shares (RSUs)",
    )
    estimated_share_price: float = Field(
        default=0.0,
        ge=0,
        description="Estimated average company share price for remaining vests",
    )

    # Other Company income
    other_company_income: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Other company income (peer bonus, spot bonus, etc.)"
        ),
    )

    miscellaneous_income: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Miscellaneous income (freelance, interest, dividends, etc.)"
        ),
    )

    # Capital gains
    short_term_capital_gains: float = Field(
        default=0.0,
        description="Short-term capital gains (held <= 1 year)",
    )
    long_term_capital_gains: float = Field(
        default=0.0,
        description="Long-term capital gains (held > 1 year)",
    )

    # Prior year
    previous_year_tax: float = Field(
        ge=0,
        description="Total federal tax liability from prior year return",
    )

    # Estimated payments already made
    estimated_tax_already_paid: float = Field(
        default=0.0,
        ge=0,
        description="1040ES estimated tax payments already submitted",
    )
    remaining_quarters: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Number of remaining quarterly payment periods",
    )


class TaxBreakdown(BaseModel):
    """Detailed breakdown of the tax computation."""

    # Income components
    w2_income: float
    current_w2: float
    remaining_w2: float
    remaining_base_salary: float
    rsu_income: float
    other_company_income: float
    miscellaneous_income: float
    short_term_capital_gains: float
    long_term_capital_gains: float
    agi: float
    standard_deduction: float
    taxable_income: float

    # Tax components
    ordinary_income: float
    ordinary_tax: float
    stcg_tax: float
    ltcg_tax: float
    niit: float
    total_tax: float

    # Withholding components
    ytd_withholding: float
    remaining_paycheck_withholding: float
    rsu_withholding: float
    other_income_withholding: float
    total_withholding: float


class SafeHarborResult(BaseModel):
    """Safe harbor analysis results."""

    # Thresholds
    current_year_90_pct: float
    prior_year_110_pct: float

    # Total payments (withholding + estimated tax already paid)
    total_payments: float

    # Can meet safe harbor with current payments?
    meets_current_year_harbor: bool
    meets_prior_year_harbor: bool
    meets_safe_harbor: bool

    # Quarterly payment recommendations
    current_year_quarterly: float
    prior_year_quarterly: float
    recommended_quarterly: float
    recommended_route: str


class TaxResult(BaseModel):
    """Complete calculation output."""

    tax_breakdown: TaxBreakdown
    safe_harbor: SafeHarborResult
