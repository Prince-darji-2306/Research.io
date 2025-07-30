# Use slim Python image
FROM python:3.10-slim

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    curl ca-certificates libnss3 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
  && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy app code
COPY . .

# Expose port and start Uvicorn
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
