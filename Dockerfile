FROM python:3.13-slim

WORKDIR /app

# Install system dependencies required by Playwright and basic utilities
RUN apt-get update && apt-get install -y \
    wget gnupg curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser & OS dependencies
RUN playwright install --with-deps chromium

COPY . .

# In an EKS Job context, we don't start a web server.
# We run a specific python script based on the command passed by Step Functions.
# Example: CMD ["python", "agents/tier1_discovery.py"]
CMD ["python", "backend.py"]
