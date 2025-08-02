FROM python:3.10-slim

# Install system dependencies for Chrome & Selenium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libnss3 \
    libxshmfence1 \
    libxext6 \
    libxi6 \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Set environment for Chromium path (important for undetected_chromedriver)
ENV CHROME_BIN=/usr/bin/chromium

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
