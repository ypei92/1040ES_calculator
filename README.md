# 1040ES Calculator

A Python project to calculate quarterly 1040ES estimated tax payments.

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
