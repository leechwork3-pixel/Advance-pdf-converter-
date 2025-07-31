# Use a specific and stable Debian slim image as the base
FROM debian:12-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Calibre in a single layer to optimize image size
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
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Copy your application files into the container
COPY . .

# (Optional) Install your Python application's dependencies
# UNCOMMENT the line below if you have a requirements.txt file
# RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your application will run on
EXPOSE 8080

# --- CHANGE THIS LINE ---
# Replace "your_main_script.py" with the actual name of your file (e.g., bot.py)
CMD ["python3", "your_main_script.py"]
