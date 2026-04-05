"""Core tax calculation logic for 1040ES quarterly estimated payments."""

from estimated_tax_calculator.models import (
    SafeHarborResult,
    TaxBreakdown,
    TaxInput,
    TaxResult,
)
from estimated_tax_calculator.tax_brackets import (
    LTCG_BRACKETS,
    NIIT_RATE,
    NIIT_THRESHOLD,
    ORDINARY_BRACKETS,
    STANDARD_DEDUCTION,
    SUPPLEMENTAL_WITHHOLDING_RATE,
    FilingStatus,
)


def calculate_progressive_tax(
    income: float,
    brackets: list[tuple[float, float]],
) -> float:
    """Calculate tax using progressive brackets.

    Args:
        income: The taxable income to apply brackets to.
        brackets: List of (upper_bound, rate) tuples. Must be sorted
            by upper_bound ascending, with the last entry using
            float("inf").

    Returns:
        Total tax computed across all applicable brackets.
    """
    if income <= 0:
        return 0.0

    tax = 0.0
    prev_bound = 0.0

    for upper_bound, rate in brackets:
        if income <= prev_bound:
            break
        taxable_in_bracket = min(income, upper_bound) - prev_bound
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
        prev_bound = upper_bound

    return tax


def calculate_agi(tax_input: TaxInput) -> tuple[float, float, float, float, float, float]:
    """Calculate Adjusted Gross Income and W-2 breakdown components.

    Args:
        tax_input: User-provided tax inputs.

    Returns:
        Tuple of (agi, w2_income, rsu_income, current_w2, remaining_w2, remaining_base_salary, miscellaneous_income).
    """
    remaining_base_salary = (
        tax_input.estimated_income_per_paycheck
        * tax_input.remaining_paychecks
    )
    rsu_income = (
        tax_input.remaining_unvested_shares
        * tax_input.estimated_share_price
    )
    current_w2 = tax_input.ytd_taxable_income
    
    # We include other_company_income inside the remaining W-2 portion
    remaining_w2 = remaining_base_salary + rsu_income + tax_input.other_company_income
    
    w2_income = current_w2 + remaining_w2

    agi = (
        w2_income
        + tax_input.miscellaneous_income
        + tax_input.short_term_capital_gains
        + tax_input.long_term_capital_gains
    )

    return agi, w2_income, rsu_income, current_w2, remaining_w2, remaining_base_salary, tax_input.miscellaneous_income


def calculate_taxable_income(
    agi: float,
    filing_status: FilingStatus,
    tax_year: int,
) -> tuple[float, float]:
    """Calculate taxable income after standard deduction.

    Args:
        agi: Adjusted Gross Income.
        filing_status: Filing status for deduction lookup.
        tax_year: Year for lookup.

    Returns:
        Tuple of (taxable_income, standard_deduction).
    """
    std_ded = STANDARD_DEDUCTION[tax_year][filing_status]
    taxable = max(0.0, agi - std_ded)
    return taxable, std_ded


def calculate_ordinary_tax(
    taxable_income: float,
    ltcg: float,
    filing_status: FilingStatus,
    tax_year: int,
) -> tuple[float, float]:
    """Calculate tax on ordinary income (excluding LTCG).

    Short-term capital gains are taxed as ordinary income and are
    already included in the ordinary income base.

    Args:
        taxable_income: Total taxable income.
        ltcg: Long-term capital gains portion.
        filing_status: Filing status for bracket lookup.
        tax_year: Year for lookup.

    Returns:
        Tuple of (ordinary_tax, ordinary_income).
    """
    ordinary_income = max(0.0, taxable_income - ltcg)
    brackets = ORDINARY_BRACKETS[tax_year][filing_status]
    tax = calculate_progressive_tax(ordinary_income, brackets)
    return tax, ordinary_income


def calculate_ltcg_tax(
    taxable_income: float,
    ltcg: float,
    filing_status: FilingStatus,
    tax_year: int,
) -> float:
    """Calculate tax on long-term capital gains at preferential rates.

    LTCG is stacked on top of ordinary income to determine which
    LTCG bracket applies. The LTCG brackets use total taxable income
    thresholds, not just the gain amount.

    Args:
        taxable_income: Total taxable income (ordinary + LTCG).
        ltcg: Long-term capital gains amount.
        filing_status: Filing status for bracket lookup.
        tax_year: Year for lookup.

    Returns:
        Tax on the LTCG portion.
    """
    if ltcg <= 0:
        return 0.0

    ordinary_income = max(0.0, taxable_income - ltcg)
    brackets = LTCG_BRACKETS[tax_year][filing_status]

    # We need to figure out how much of the LTCG falls in each
    # LTCG bracket. The LTCG "starts" at the ordinary_income level
    # and extends up to taxable_income.
    tax = 0.0
    ltcg_bottom = ordinary_income
    ltcg_top = taxable_income
    prev_bound = 0.0

    for upper_bound, rate in brackets:
        if ltcg_bottom >= upper_bound:
            prev_bound = upper_bound
            continue
        bracket_bottom = max(ltcg_bottom, prev_bound)
        bracket_top = min(ltcg_top, upper_bound)
        if bracket_top > bracket_bottom:
            tax += (bracket_top - bracket_bottom) * rate
        if ltcg_top <= upper_bound:
            break
        prev_bound = upper_bound

    return tax


def calculate_niit(
    agi: float,
    net_investment_income: float,
    filing_status: FilingStatus,
) -> float:
    """Calculate Net Investment Income Tax (3.8% surtax).

    Applies to the lesser of:
    - Net investment income, or
    - The amount by which MAGI exceeds the threshold.

    Args:
        agi: Adjusted Gross Income (used as MAGI proxy).
        net_investment_income: Total investment income (LTCG + STCG +
            dividends, etc.).
        filing_status: Filing status for threshold lookup.

    Returns:
        NIIT amount.
    """
    if net_investment_income <= 0:
        return 0.0

    threshold = NIIT_THRESHOLD[filing_status]
    excess_agi = max(0.0, agi - threshold)

    if excess_agi <= 0:
        return 0.0

    taxable_amount = min(net_investment_income, excess_agi)
    return taxable_amount * NIIT_RATE


def estimate_withholding(
    tax_input: TaxInput,
) -> tuple[float, float, float, float, float]:
    """Estimate total federal withholding for the year.

    RSU and other supplemental income are withheld at the flat 22%
    supplemental rate.

    Args:
        tax_input: User-provided tax inputs.

    Returns:
        Tuple of (total, ytd, remaining_paycheck, rsu, other_income).
    """
    ytd = tax_input.ytd_tax_withheld

    remaining_paycheck = (
        tax_input.estimated_withholding_per_paycheck
        * tax_input.remaining_paychecks
    )

    rsu_income = (
        tax_input.remaining_unvested_shares
        * tax_input.estimated_share_price
    )
    rsu_withholding = rsu_income * SUPPLEMENTAL_WITHHOLDING_RATE

    other_withholding = (
        tax_input.other_company_income * SUPPLEMENTAL_WITHHOLDING_RATE
    )

    total = ytd + remaining_paycheck + rsu_withholding + other_withholding

    return total, ytd, remaining_paycheck, rsu_withholding, other_withholding


def check_safe_harbor(
    total_tax: float,
    previous_year_tax: float,
    total_withholding: float,
    estimated_tax_already_paid: float,
    remaining_quarters: int,
) -> SafeHarborResult:
    """Determine safe harbor status and quarterly payment amounts.

    Safe harbor is met if total payments (withholding + estimated)
    cover either:
    - 90% of current year tax, OR
    - 110% of prior year tax (for AGI > $150k)

    Args:
        total_tax: Estimated current year total federal tax.
        previous_year_tax: Prior year total tax liability.
        total_withholding: Estimated total withholding for the year.
        estimated_tax_already_paid: 1040ES payments already submitted.
        remaining_quarters: Number of remaining quarterly periods.

    Returns:
        SafeHarborResult with analysis and recommendations.
    """
    current_year_90 = total_tax * 0.90
    prior_year_110 = previous_year_tax * 1.10

    total_payments = total_withholding + estimated_tax_already_paid

    meets_current = total_payments >= current_year_90
    meets_prior = total_payments >= prior_year_110
    meets_harbor = meets_current or meets_prior

    # Calculate quarterly shortfall for each route
    current_shortfall = max(0.0, current_year_90 - total_payments)
    prior_shortfall = max(0.0, prior_year_110 - total_payments)

    current_quarterly = current_shortfall / remaining_quarters
    prior_quarterly = prior_shortfall / remaining_quarters

    # Recommend the cheaper route
    if current_quarterly <= prior_quarterly:
        recommended = current_quarterly
        route = "Current year × 90%"
    else:
        recommended = prior_quarterly
        route = "Prior year × 110%"

    return SafeHarborResult(
        current_year_90_pct=current_year_90,
        prior_year_110_pct=prior_year_110,
        total_payments=total_payments,
        meets_current_year_harbor=meets_current,
        meets_prior_year_harbor=meets_prior,
        meets_safe_harbor=meets_harbor,
        current_year_quarterly=current_quarterly,
        prior_year_quarterly=prior_quarterly,
        recommended_quarterly=recommended,
        recommended_route=route,
    )


def calculate(tax_input: TaxInput) -> TaxResult:
    """Run the complete 1040ES tax estimation.

    Orchestrates all calculation steps: AGI, taxable income,
    tax computation (ordinary + LTCG + NIIT), withholding
    estimation, and safe harbor analysis.

    Args:
        tax_input: All user-provided inputs.

    Returns:
        Complete TaxResult with breakdown and recommendations.
    """
    # Step 1: AGI
    agi, w2_income, rsu_income, current_w2, remaining_w2, remaining_base_salary, miscellaneous_income = calculate_agi(tax_input)

    # Step 2: Taxable income
    taxable_income, std_ded = calculate_taxable_income(
        agi, tax_input.filing_status, tax_input.tax_year
    )

    # Step 3: Tax computation
    ltcg = max(0.0, tax_input.long_term_capital_gains)
    # Ensure LTCG doesn't exceed taxable income
    ltcg_for_tax = min(ltcg, taxable_income)

    stcg = max(0.0, tax_input.short_term_capital_gains)
    ordinary_tax, ordinary_income = calculate_ordinary_tax(
        taxable_income, ltcg_for_tax, tax_input.filing_status, tax_input.tax_year
    )
    
    # Calculate marginal STCG tax impact
    base_taxable_income = max(0.0, taxable_income - stcg)
    base_ordinary_tax, _ = calculate_ordinary_tax(
        base_taxable_income, ltcg_for_tax, tax_input.filing_status, tax_input.tax_year
    )
    stcg_tax = max(0.0, ordinary_tax - base_ordinary_tax)

    ltcg_tax = calculate_ltcg_tax(
        taxable_income, ltcg_for_tax, tax_input.filing_status, tax_input.tax_year
    )

    # Net investment income for NIIT: LTCG + STCG
    net_investment_income = ltcg + max(
        0.0, tax_input.short_term_capital_gains
    )
    niit = calculate_niit(
        agi, net_investment_income, tax_input.filing_status
    )

    total_tax = ordinary_tax + ltcg_tax + niit

    # Step 4: Withholding
    (
        total_withholding,
        ytd_wh,
        remaining_paycheck_wh,
        rsu_wh,
        other_wh,
    ) = estimate_withholding(tax_input)

    # Step 5: Safe harbor
    safe_harbor = check_safe_harbor(
        total_tax=total_tax,
        previous_year_tax=tax_input.previous_year_tax,
        total_withholding=total_withholding,
        estimated_tax_already_paid=tax_input.estimated_tax_already_paid,
        remaining_quarters=tax_input.remaining_quarters,
    )

    breakdown = TaxBreakdown(
        w2_income=w2_income,
        current_w2=current_w2,
        remaining_w2=remaining_w2,
        remaining_base_salary=remaining_base_salary,
        rsu_income=rsu_income,
        other_company_income=tax_input.other_company_income,
        miscellaneous_income=miscellaneous_income,
        short_term_capital_gains=tax_input.short_term_capital_gains,
        long_term_capital_gains=ltcg,
        agi=agi,
        standard_deduction=std_ded,
        taxable_income=taxable_income,
        ordinary_income=ordinary_income,
        ordinary_tax=ordinary_tax,
        stcg_tax=stcg_tax,
        ltcg_tax=ltcg_tax,
        niit=niit,
        total_tax=total_tax,
        ytd_withholding=ytd_wh,
        remaining_paycheck_withholding=remaining_paycheck_wh,
        rsu_withholding=rsu_wh,
        other_income_withholding=other_wh,
        total_withholding=total_withholding,
    )

    return TaxResult(
        tax_breakdown=breakdown,
        safe_harbor=safe_harbor,
    )
