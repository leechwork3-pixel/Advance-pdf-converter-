# Use a specific and stable Debian slim image as the base
FROM debian:12-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Python, and Calibre in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip wget xz-utils \
    libglib2.0-0 libegl1 libopengl0 libxcb-cursor0 libfreetype6 && \
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin && \
    apt-get purge -y --auto-remove wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory for your application
WORKDIR /app

# --- THE FIX IS HERE ---
# Create a non-root user and group for better security.
# The username 'appuser' was added to the end of the command.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy your dependency file first.
COPY requirements.txt .

# Install your Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files (bot.py, config.py, etc.)
COPY . .

# Switch to the non-root user
USER appuser

# Expose a port if your bot needs it
EXPOSE 8080

# The command to start your bot
CMD ["python3", "bot.py"]
