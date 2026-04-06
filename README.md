# 1040ES Calculator

A Python project to calculate quarterly 1040ES estimated tax payments.

## Privacy & Legal

**⚠️ Not Financial Advice:** This application is built for educational and estimation
purposes only. The tax calculations provided do not constitute official financial,
legal, or tax advice. Please consult a certified CPA for personalized tax advice.

**🔒 Data Privacy:** This application is entirely stateless. When you submit your
financial numbers via the web form, they are held strictly in short-lived memory (RAM)
just long enough to perform the math and return the results to your browser. Your
financial inputs are **never** logged, never saved to any database, never written to
the server's disk, and never transmitted to external telemetry or third-party
services.

## Deployment (Docker)

The easiest way to host this application is using Docker. The image is automatically
built and hosted on Docker Hub.

1. Create a `docker-compose.yml` file on your server or local machine:

   ```yaml
   services:
     tax-calculator:
       image: ypei92/1040es-calculator:latest
       container_name: 1040es-calculator
       restart: unless-stopped
       ports:
         - "8765:8765"
   ```

2. Start the container in the background:

   ```bash
   docker compose up -d
   ```

3. The application will be immediately available at `http://localhost:8765`.

## Local Development Setup

1. Set up the Python virtual environment using e.g. `uv`, `conda` or `venv`.
2. Install dependencies (including development tools):

   ```bash
   pip install -e ".[dev]"
   pre-commit install
   ```

## Testing & Running Manually

To manually run the development server locally without Docker:

```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run tests
pytest tests/

# Start local server
python -m uvicorn estimated_tax_calculator.app:app --host 127.0.0.1 --port 8765
```
