FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir --upgrade pip uv

# Copy dependencies definitions
COPY pyproject.toml uv.lock* ./

# Install all production dependencies using uv directly into system env
RUN uv pip install --system .

# Copy application code
COPY src/ /app/src/

# Change ownership of the app directory to the new non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user for all subsequent commands
USER appuser

# Expose the standard port
EXPOSE 8765

# Command to run the application using Uvicorn
CMD ["uvicorn", "estimated_tax_calculator.app:app", "--host", "0.0.0.0", "--port", "8765"]
