# Use Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the ports
# Note: In production, you'll likely run these on different services.
# This combined file is for reference or specific setups.

EXPOSE 8000
EXPOSE 8501

# Default command (will be overridden by deployment platform)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
