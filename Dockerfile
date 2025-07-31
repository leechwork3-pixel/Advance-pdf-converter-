# Use a specific and stable Debian slim image as the base
FROM debian:12-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Calibre in a single layer to optimize image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # --- Core utilities ---
    python3 \
    python3-pip \
    wget \
    xz-utils \
    # --- Dependencies required by Calibre ---
    libglib2.0-0 \
    libegl1 \
    libopengl0 \
    libxcb-cursor0 \
    # --- THE FIX: Added the missing FreeType library ---
    libfreetype6 && \
    \
    # --- Download and install Calibre ---
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin && \
    \
    # --- Clean up to reduce final image size ---
    apt-get purge -y --auto-remove wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory for your application
WORKDIR /app

# Create a non-root user and group for better security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# --- TODO: CUSTOMIZE FROM HERE ---

# 1. Copy your application files into the container
# This copies all files from your current directory into the container's /app directory
COPY . .

# 2. (Optional) Install your Python application's dependencies if you have a requirements.txt
# UNCOMMENT the line below if you have a requirements.txt file
# RUN pip install --no-cache-dir -r requirements.txt

# 3. Expose the port your application will run on (e.g., 8080 for web apps)
EXPOSE 8080

# 4. The command to start your application
# Replace "app.py" with the name of your main script
CMD ["python3", "app.py"]
