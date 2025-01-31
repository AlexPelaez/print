# Use the official Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application files to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Chrome and ChromeDriver
RUN apt-get update && apt-get install -y wget gnupg && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    wget -O /usr/local/bin/chromedriver https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for ChromeDriver
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Expose a port (if applicable, e.g., for a web API)
# EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]

