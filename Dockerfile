# Use a full Debian-based Python image to ensure compatibility with Calibre's dependencies
FROM python:3.10-bullseye

# Set the working directory
WORKDIR /app

# Install system dependencies required for Calibre and other libraries
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libgl1 \
    libfontconfig1 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Download and install Calibre
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY bot/ ./bot/

# Command to run the bot as a module
CMD ["python3", "-m", "bot.bot"]
