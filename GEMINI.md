# 1040-ES Calculator - AI Guidelines

Welcome! This `GEMINI.md` file serves as the core instruction manual and context repository for AI assistants working on the 1040-ES Calculator.

## Project Overview

This is a local, privacy-focused web application designed to help individuals (particularly those with complex compensation like RSUs, bonuses, and capital gains) accurately estimate their quarterly federal 1040-ES tax payments and analyze Safe Harbor eligibility. 

It calculates:
- Progressive federal ordinary income tax
- Preferential long-term capital gains tax
- Net Investment Income Tax (NIIT)
- Total paycheck withholding (accounting for the 22% supplemental flat rate on RSUs and bonuses)
- Safe harbor payment thresholds (90% current year vs 110% prior year)

## Architecture

- **Backend:** Python 3.12+, FastAPI, Pydantic (for strictly typing input schemas in `models.py`).
- **Core Engine:** `calculator.py` houses isolated, pure-function math algorithms. `tax_brackets.py` stores the static IRS bracket numbers.
- **Frontend:** Jinja2 template (`index.html`), standard Vanilla CSS (`style.css`), and lightweight JS (`app.js`) for UI interactions like tooltips.
- **Testing:** `pytest` is used for automated integration tests against the core engine.

## 🔴 Critical Privacy Constraints

**ABSOLUTELY NO PERSONAL IDENTIFIABLE INFORMATION (PII) IS ALLOWED IN THIS CODEBASE.**
This project holds extremely sensitive logic. When adding or modifying code, tests, or documentation:
1. **Never** hardcode employer names, addresses, or specific real-world W-2/paystub figures.
2. The unit tests in `tests/test_calculator.py` MUST solely rely on rounded, hypothetical, and generic numbers.
3. System deployment configurations (like Systemd or Nginx setups in `/deploy/`) must ALWAYS use generic placeholders (e.g., `/path/to/project`, `your_username`) instead of absolute local system paths.

## Style & Standards
- **Python:** Use strong typing hints on all functions. Follow standard PEP-8 style formatting. Manage imports clearly.
- **Frontend:** Stick to the existing vanilla CSS/JS glassmorphism layout patterns. Avoid adding heavy frontend frameworks without explicit user consent. Do not use TailwindCSS.
