# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Set the working directory
# Set the working directory
WORKDIR /app

# Install system dependencies, install Python dependencies, and clean up in one layer
# We explicitly install the CPU-only version of PyTorch first to avoid the massive 4GB+ GPU version
# that gets pulled in by sentence-transformers, then we install the rest of requirements.txt.
COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && pip install --upgrade pip \
    && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y gcc build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 8000

# Start the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips", "*"]
