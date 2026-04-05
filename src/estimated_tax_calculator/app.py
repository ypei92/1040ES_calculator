"""FastAPI web application for the 1040ES tax calculator."""

import math
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from estimated_tax_calculator.calculator import calculate
from estimated_tax_calculator.models import TaxInput
from estimated_tax_calculator.tax_brackets import FilingStatus

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="1040ES Calculator", version="0.1.0")

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def format_currency(value: float) -> str:
    """Format a float as a currency string.

    Args:
        value: The numeric value to format.

    Returns:
        Formatted string like '$1,234.56' or '-$1,234.56'.
    """
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_whole(value: float) -> str:
    """Format a float as a whole-dollar currency string.

    Args:
        value: The numeric value to format.

    Returns:
        Formatted string like '$1,235' (rounded up).
    """
    rounded = math.ceil(value)
    if rounded < 0:
        return f"-${abs(rounded):,}"
    return f"${rounded:,}"


# Register template filters
templates.env.filters["currency"] = format_currency
templates.env.filters["whole"] = format_whole


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the calculator input form.

    Args:
        request: The incoming HTTP request.

    Returns:
        HTML response with the input form.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {"result": None},
    )


@app.get("/calculate", response_class=RedirectResponse)
async def redirect_calculate() -> RedirectResponse:
    """Redirect GET requests on /calculate back to the home page."""
    return RedirectResponse(url="/", status_code=303)


@app.post("/calculate", response_class=HTMLResponse)
async def handle_calculate(
    request: Request,
    tax_year: int = Form(2026),
    filing_status: str = Form("single"),
    ytd_tax_withheld: float = Form(0.0),
    ytd_taxable_income: float = Form(0.0),
    remaining_paychecks: int = Form(0),
    estimated_income_per_paycheck: float = Form(0.0),
    estimated_withholding_per_paycheck: float = Form(0.0),
    remaining_unvested_shares: int = Form(0),
    estimated_share_price: float = Form(0.0),
    other_company_income: float = Form(0.0),
    miscellaneous_income: float = Form(0.0),
    short_term_capital_gains: float = Form(0.0),
    long_term_capital_gains: float = Form(0.0),
    previous_year_tax: float = Form(0.0),
    estimated_tax_already_paid: float = Form(0.0),
    remaining_quarters: int = Form(4),
) -> HTMLResponse:
    """Process the form submission and return results.

    Args:
        request: The incoming HTTP request.
        filing_status: Single or Married Filing Jointly.
        ytd_tax_withheld: Year-to-date tax withheld.
        ytd_taxable_income: Year-to-date taxable income.
        remaining_paychecks: Number of remaining paychecks.
        estimated_income_per_paycheck: Income per remaining paycheck.
        estimated_withholding_per_paycheck: Withholding per paycheck.
        remaining_unvested_shares: Unvested company shares remaining.
        estimated_share_price: Estimated share price.
        other_company_income: Other company income.
        short_term_capital_gains: Short-term capital gains.
        long_term_capital_gains: Long-term capital gains.
        previous_year_tax: Prior year tax liability.
        estimated_tax_already_paid: Estimated tax already paid.
        remaining_quarters: Remaining quarterly periods.

    Returns:
        HTML response with calculation results.
    """
    tax_input = TaxInput(
        tax_year=tax_year,
        filing_status=FilingStatus(filing_status),
        ytd_tax_withheld=ytd_tax_withheld,
        ytd_taxable_income=ytd_taxable_income,
        remaining_paychecks=remaining_paychecks,
        estimated_income_per_paycheck=estimated_income_per_paycheck,
        estimated_withholding_per_paycheck=estimated_withholding_per_paycheck,
        remaining_unvested_shares=remaining_unvested_shares,
        estimated_share_price=estimated_share_price,
        other_company_income=other_company_income,
        miscellaneous_income=miscellaneous_income,
        short_term_capital_gains=short_term_capital_gains,
        long_term_capital_gains=long_term_capital_gains,
        previous_year_tax=previous_year_tax,
        estimated_tax_already_paid=estimated_tax_already_paid,
        remaining_quarters=remaining_quarters,
    )

    result = calculate(tax_input)

    # Pass form values back for re-population
    form_values = {
        "tax_year": tax_year,
        "filing_status": filing_status,
        "ytd_tax_withheld": ytd_tax_withheld,
        "ytd_taxable_income": ytd_taxable_income,
        "remaining_paychecks": remaining_paychecks,
        "estimated_income_per_paycheck": estimated_income_per_paycheck,
        "estimated_withholding_per_paycheck": estimated_withholding_per_paycheck,
        "remaining_unvested_shares": remaining_unvested_shares,
        "estimated_share_price": estimated_share_price,
        "other_company_income": other_company_income,
        "miscellaneous_income": miscellaneous_income,
        "short_term_capital_gains": short_term_capital_gains,
        "long_term_capital_gains": long_term_capital_gains,
        "previous_year_tax": previous_year_tax,
        "estimated_tax_already_paid": estimated_tax_already_paid,
        "remaining_quarters": remaining_quarters,
    }

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": result,
            "form": form_values,
        },
    )
