"""Comprehensive tests for the 1040ES tax calculator."""

import pytest

from estimated_tax_calculator.calculator import (
    calculate,
    calculate_agi,
    calculate_ltcg_tax,
    calculate_niit,
    calculate_ordinary_tax,
    calculate_progressive_tax,
    calculate_taxable_income,
    check_safe_harbor,
    estimate_withholding,
)
from estimated_tax_calculator.models import TaxInput
from estimated_tax_calculator.tax_brackets import (
    ORDINARY_BRACKETS,
    FilingStatus,
)


# ---- Progressive bracket calculation ----


class TestProgressiveTax:
    """Tests for the progressive bracket calculation engine."""

    def test_zero_income(self) -> None:
        """Zero income should produce zero tax."""
        brackets = ORDINARY_BRACKETS[2025][FilingStatus.SINGLE]
        assert calculate_progressive_tax(0.0, brackets) == 0.0

    def test_negative_income(self) -> None:
        """Negative income should produce zero tax."""
        brackets = ORDINARY_BRACKETS[2025][FilingStatus.SINGLE]
        assert calculate_progressive_tax(-1000.0, brackets) == 0.0

    def test_first_bracket_only_single(self) -> None:
        """Income within 10% bracket only."""
        brackets = ORDINARY_BRACKETS[2025][FilingStatus.SINGLE]
        tax = calculate_progressive_tax(10_000.0, brackets)
        assert tax == pytest.approx(10_000 * 0.10, abs=0.01)

    def test_two_brackets_single(self) -> None:
        """Income spanning 10% and 12% brackets."""
        brackets = ORDINARY_BRACKETS[2025][FilingStatus.SINGLE]
        income = 30_000.0
        expected = 11_925 * 0.10 + (30_000 - 11_925) * 0.12
        tax = calculate_progressive_tax(income, brackets)
        assert tax == pytest.approx(expected, abs=0.01)

    def test_exact_bracket_boundary(self) -> None:
        """Income exactly at a bracket boundary."""
        brackets = ORDINARY_BRACKETS[2025][FilingStatus.SINGLE]
        income = 11_925.0
        expected = 11_925 * 0.10
        tax = calculate_progressive_tax(income, brackets)
        assert tax == pytest.approx(expected, abs=0.01)


# ---- User's exact scenario ----


class TestGenericTechScenario:
    """Test a generic tech industry scenario with rounded numbers."""

    @pytest.fixture()
    def user_input(self) -> TaxInput:
        """Create a generic set of input values."""
        return TaxInput(
            tax_year=2025,
            filing_status=FilingStatus.SINGLE,
            ytd_tax_withheld=15_000.0,
            ytd_taxable_income=75_000.0,
            remaining_paychecks=18,
            estimated_income_per_paycheck=5_500.0,
            estimated_withholding_per_paycheck=500.0,
            remaining_unvested_shares=200,
            estimated_share_price=250.0,
            other_company_income=5_000.0,
            short_term_capital_gains=0.0,
            long_term_capital_gains=10_000.0,
            previous_year_tax=65_000.0,
            estimated_tax_already_paid=0.0,
            remaining_quarters=4,
        )

    def test_agi(self, user_input: TaxInput) -> None:
        """Verify AGI calculation."""
        agi, w2_income, rsu_income, current_w2, remaining_w2, remaining_base_salary, _ = calculate_agi(user_input)

        # RSU: 200 * 250 = 50,000
        assert rsu_income == pytest.approx(50_000.0, abs=0.01)

        # W2: 75,000 + (5,500 * 18) + 50,000 + 5,000 = 229,000
        assert w2_income == pytest.approx(229_000.0, abs=0.01)

        # AGI: 229,000 + 0 + 10,000 = 239,000
        assert agi == pytest.approx(239_000.0, abs=0.01)

    def test_taxable_income(self, user_input: TaxInput) -> None:
        """Verify taxable income after standard deduction."""
        agi, _, _, _, _, _, _ = calculate_agi(user_input)
        taxable, std_ded = calculate_taxable_income(
            agi, user_input.filing_status, user_input.tax_year
        )
        assert std_ded == pytest.approx(15_750.0, abs=0.01)
        assert taxable == pytest.approx(223_250.0, abs=0.01)

    def test_ordinary_tax(self, user_input: TaxInput) -> None:
        """Verify ordinary income tax computation.

        Ordinary income = 223,250 - 10,000 = 213,250
        Tax brackets (single 2025):
          10% on 11,925 = 1,192.50
          12% on 36,550 = 4,386.00
          22% on 54,875 = 12,072.50
          24% on 93,950 = 22,548.00
          32% on 15,950 = 5,104.00
        Total = 45,303.00
        """
        agi, _, _, _, _, _, _ = calculate_agi(user_input)
        taxable, _ = calculate_taxable_income(agi, user_input.filing_status, user_input.tax_year)
        tax, ordinary_income = calculate_ordinary_tax(
            taxable, 10_000.0, user_input.filing_status, user_input.tax_year
        )

        assert ordinary_income == pytest.approx(213_250.0, abs=0.01)
        assert tax == pytest.approx(45_303.00, abs=1.0)

    def test_ltcg_tax(self, user_input: TaxInput) -> None:
        """Verify LTCG tax: $10,000 at 15% = $1,500."""
        agi, _, _, _, _, _, _ = calculate_agi(user_input)
        taxable, _ = calculate_taxable_income(agi, user_input.filing_status, user_input.tax_year)
        ltcg_tax = calculate_ltcg_tax(
            taxable, 10_000.0, user_input.filing_status, user_input.tax_year
        )
        assert ltcg_tax == pytest.approx(1_500.0, abs=0.01)

    def test_niit(self, user_input: TaxInput) -> None:
        """Verify NIIT: 3.8% × min(10000, 239000 - 200000) = $380."""
        agi, _, _, _, _, _, _ = calculate_agi(user_input)
        niit = calculate_niit(agi, 10_000.0, user_input.filing_status)
        assert niit == pytest.approx(380.0, abs=0.01)

    def test_stcg_tax(self, user_input: TaxInput) -> None:
        """Verify STCG correctly adds to ordinary income and generates marginal STCG tax."""
        user_input.short_term_capital_gains = 5_000.0
        result = calculate(user_input)
        # Ordinary income should increase by 5_000 since baseline was 213,250
        assert result.tax_breakdown.short_term_capital_gains == 5_000.0
        # The STCG sits on top of ordinary income, which might cross tax brackets, but we ensure it is non-zero.
        assert result.tax_breakdown.stcg_tax > 1_000.0

    def test_miscellaneous_income(self, user_input: TaxInput) -> None:
        """Verify miscellaneous income behaves appropriately (adds to AGI, no withholding)."""
        user_input.miscellaneous_income = 10_000.0
        result = calculate(user_input)
        assert result.tax_breakdown.miscellaneous_income == 10_000.0
        assert result.tax_breakdown.agi == pytest.approx(249_000.0, abs=0.01)
        # Should not increase total withholding (remains 36,100.0)
        assert result.tax_breakdown.total_withholding == pytest.approx(36_100.0, abs=0.01)

    def test_total_tax(self, user_input: TaxInput) -> None:
        """Verify total tax ≈ $47,183."""
        result = calculate(user_input)
        assert result.tax_breakdown.total_tax == pytest.approx(
            47_183.00, abs=2.0
        )

    def test_withholding(self, user_input: TaxInput) -> None:
        """Verify withholding estimation."""
        total, ytd, paycheck, rsu, other = estimate_withholding(user_input)

        assert ytd == pytest.approx(15_000.0, abs=0.01)
        assert paycheck == pytest.approx(9_000.0, abs=0.01)
        # 200 * 250 * 0.22 = 11,000.00
        assert rsu == pytest.approx(11_000.00, abs=0.01)
        # 5000 * 0.22 = 1,100
        assert other == pytest.approx(1_100.0, abs=0.01)
        assert total == pytest.approx(36_100.0, abs=0.01)

    def test_safe_harbor_not_met(self, user_input: TaxInput) -> None:
        """Verify safe harbor is NOT met with withholding alone."""
        result = calculate(user_input)
        assert result.safe_harbor.meets_safe_harbor is False
        assert result.safe_harbor.meets_current_year_harbor is False
        assert result.safe_harbor.meets_prior_year_harbor is False

    def test_quarterly_payment_recommendation(
        self, user_input: TaxInput
    ) -> None:
        """Verify quarterly payment recommendation."""
        result = calculate(user_input)
        assert result.safe_harbor.meets_safe_harbor is False
        # (47183 * 0.9 - 36100) / 4 = 1591.17
        assert result.safe_harbor.current_year_quarterly == pytest.approx(
            1_591.17, abs=1.0
        )
        assert result.safe_harbor.recommended_route == "Current year × 90%"


# ---- Safe harbor edge cases ----


class TestSafeHarbor:
    """Test safe harbor determination logic."""

    def test_meets_current_year_harbor(self) -> None:
        """Withholding covers 90% of current year."""
        result = check_safe_harbor(
            total_tax=100_000.0,
            previous_year_tax=120_000.0,
            total_withholding=91_000.0,
            estimated_tax_already_paid=0.0,
            remaining_quarters=4,
        )
        assert result.meets_current_year_harbor is True
        assert result.meets_safe_harbor is True

    def test_meets_prior_year_harbor(self) -> None:
        """Withholding covers 110% of prior year."""
        result = check_safe_harbor(
            total_tax=200_000.0,
            previous_year_tax=80_000.0,
            total_withholding=90_000.0,
            estimated_tax_already_paid=0.0,
            remaining_quarters=4,
        )
        assert result.meets_prior_year_harbor is True
        assert result.meets_safe_harbor is True

    def test_with_estimated_payments(self) -> None:
        """Already-paid estimated tax counts towards safe harbor."""
        result = check_safe_harbor(
            total_tax=100_000.0,
            previous_year_tax=80_000.0,
            total_withholding=50_000.0,
            estimated_tax_already_paid=40_000.0,
            remaining_quarters=2,
        )
        # total_payments = 50k + 40k = 90k >= 90% of 100k = 90k
        assert result.meets_current_year_harbor is True
        assert result.meets_safe_harbor is True

    def test_remaining_quarters_division(self) -> None:
        """Shortfall split over remaining quarters only."""
        result = check_safe_harbor(
            total_tax=100_000.0,
            previous_year_tax=50_000.0,
            total_withholding=60_000.0,
            estimated_tax_already_paid=0.0,
            remaining_quarters=2,
        )
        # 90% current = 90k, shortfall = 30k, split over 2 = 15k
        assert result.current_year_quarterly == pytest.approx(
            15_000.0, abs=0.01
        )

    def test_recommends_cheaper_route(self) -> None:
        """Should recommend whichever route requires less per quarter."""
        result = check_safe_harbor(
            total_tax=100_000.0,
            previous_year_tax=80_000.0,
            total_withholding=50_000.0,
            estimated_tax_already_paid=0.0,
            remaining_quarters=4,
        )
        # Current: (90k - 50k) / 4 = 10k
        # Prior:   (88k - 50k) / 4 = 9.5k
        assert result.recommended_route == "Prior year × 110%"


# ---- LTCG tax edge cases ----


class TestLTCGTax:
    """Test LTCG tax at different income levels."""

    def test_zero_ltcg(self) -> None:
        """No LTCG means no LTCG tax."""
        tax = calculate_ltcg_tax(100_000.0, 0.0, FilingStatus.SINGLE, 2025)
        assert tax == 0.0

    def test_ltcg_in_zero_bracket(self) -> None:
        """Low-income LTCG taxed at 0%."""
        # Single: 0% up to $48,350. Ordinary = $20k, LTCG = $10k
        tax = calculate_ltcg_tax(30_000.0, 10_000.0, FilingStatus.SINGLE, 2025)
        assert tax == pytest.approx(0.0, abs=0.01)

    def test_ltcg_straddles_brackets(self) -> None:
        """LTCG that straddles the 0%/15% boundary."""
        # Ordinary = $45,000, LTCG = $10,000, total taxable = $55,000
        # 0% bracket up to $48,350: $3,350 at 0%
        # 15% bracket: $6,650 at 15% = $997.50
        tax = calculate_ltcg_tax(55_000.0, 10_000.0, FilingStatus.SINGLE, 2025)
        expected = 3_350 * 0.00 + 6_650 * 0.15
        assert tax == pytest.approx(expected, abs=1.0)


# ---- NIIT edge cases ----


class TestNIIT:
    """Test Net Investment Income Tax."""

    def test_below_threshold(self) -> None:
        """No NIIT when AGI below threshold."""
        niit = calculate_niit(150_000.0, 10_000.0, FilingStatus.SINGLE)
        assert niit == 0.0

    def test_investment_income_limits_niit(self) -> None:
        """NIIT limited to investment income when excess AGI is larger."""
        # AGI = 500k, threshold = 200k, excess = 300k
        # Investment = 5k. NIIT = 3.8% of min(5k, 300k) = 5k
        niit = calculate_niit(500_000.0, 5_000.0, FilingStatus.SINGLE)
        assert niit == pytest.approx(5_000 * 0.038, abs=0.01)

    def test_excess_agi_limits_niit(self) -> None:
        """NIIT limited to excess AGI when investment income is larger."""
        # AGI = 210k, threshold = 200k, excess = 10k
        # Investment = 50k. NIIT = 3.8% of min(50k, 10k) = 10k
        niit = calculate_niit(210_000.0, 50_000.0, FilingStatus.SINGLE)
        assert niit == pytest.approx(10_000 * 0.038, abs=0.01)

    def test_mfj_threshold(self) -> None:
        """MFJ uses $250k threshold."""
        # AGI = 260k, threshold = 250k, excess = 10k
        niit = calculate_niit(
            260_000.0, 10_000.0, FilingStatus.MARRIED_FILING_JOINTLY
        )
        assert niit == pytest.approx(10_000 * 0.038, abs=0.01)

    def test_zero_investment_income(self) -> None:
        """No NIIT when no investment income."""
        niit = calculate_niit(500_000.0, 0.0, FilingStatus.SINGLE)
        assert niit == 0.0


# ---- MFJ brackets ----


class TestMFJBrackets:
    """Test Married Filing Jointly bracket calculations."""

    def test_mfj_standard_deduction(self) -> None:
        """MFJ standard deduction is $31,500."""
        _, std_ded = calculate_taxable_income(
            100_000.0, FilingStatus.MARRIED_FILING_JOINTLY, 2025
        )
        assert std_ded == pytest.approx(31_500.0, abs=0.01)

    def test_mfj_ordinary_tax(self) -> None:
        """MFJ tax on $100,000 taxable income."""
        # 10% on 23,850 = 2,385
        # 12% on (96,950 - 23,850) = 73,100 * 0.12 = 8,772
        # 22% on (100,000 - 96,950) = 3,050 * 0.22 = 671
        expected = 2_385.0 + 8_772.0 + 671.0
        tax, _ = calculate_ordinary_tax(
            100_000.0, 0.0, FilingStatus.MARRIED_FILING_JOINTLY, 2025
        )
        assert tax == pytest.approx(expected, abs=1.0)
