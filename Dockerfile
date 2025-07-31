# Dockerfile

# Use a newer Debian image that has the required libraries for Calibre
FROM debian:bookworm-slim

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /app

# Install system dependencies, Python, pip, and Calibre
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    wget \
    xz-utils \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxrandr2 \
    libglib2.0-0 && \
    # Download and install Calibre
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin && \
    # Clean up to reduce image size
    apt-get purge -y --auto-remove wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define the command to run the bot
CMD ["python3", "bot.py"]
