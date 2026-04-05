# 1040ES Calculator

A Python project to calculate quarterly 1040ES estimated tax payments.

## Privacy & Legal

**⚠️ Not Financial Advice:** This application is built for educational and estimation purposes only. The tax calculations provided do not constitute official financial, legal, or tax advice. Please consult a certified CPA for personalized tax advice.

**🔒 Data Privacy:** This application is entirely stateless. When you submit your financial numbers via the web form, they are held strictly in short-lived memory (RAM) just long enough to perform the math and return the results to your browser. Your financial inputs are **never** logged, never saved to any database, never written to the server's disk, and never transmitted to external telemetry or third-party services.

## Project Setup

This project uses `uv` for dependency management and requires a Conda environment.

1. Ensure you have the Conda environment activated:
   ```bash
   conda activate 1040es_py312
   ```

2. Install dependencies via `uv`:
   ```bash
   uv pip install -e .
   uv pip install -e ".[dev]"
   ```

3. Setup pre-commit:
   ```bash
   pre-commit install
   ```

## Testing
Run the tests using pytest:
```bash
pytest tests/
```
