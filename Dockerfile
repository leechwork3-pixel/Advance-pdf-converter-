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

# Create a non-root user and group for better security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup

# --- THE FIX IS HERE ---
# Copy your dependency file first.
# Corrected the filename to "requirements.txt" (with an 's').
COPY requirements.txt .

# Install your Python dependencies from the corrected file name.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application files (bot.py, config.py, etc.)
COPY . .

# Switch to the non-root user
USER appuser

# Expose a port if your bot needs it (e.g., for a web dashboard)
# You can remove this if your bot doesn't listen on a port.
EXPOSE 8080

# The command to start your bot
CMD ["python3", "bot.py"]

