# Use an official Python image, which is cleaner and includes Python/pip.
FROM python:3.11-slim-bookworm

# Set recommended environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system-level dependencies required by Calibre
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    xz-utils \
    libglib2.0-0 \
    libegl1 \
    libopengl0 \
    libxcb-cursor0 \
    libfreetype6 && \
    # Download and install Calibre
    wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin && \
    # Clean up to reduce image size
    apt-get purge -y --auto-remove wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- THE FIX: Create and activate a virtual environment ---
ENV VENV_PATH=/opt/venv
RUN python3 -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Set the working directory
WORKDIR /app

# Create a non-root user for better security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy the requirements file and set correct ownership
COPY --chown=appuser:appgroup requirements.txt .

# Install Python dependencies into the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code and set ownership
COPY --chown=appuser:appgroup . .

# Switch to the non-root user
USER appuser

# Expose a port if your bot needs it
EXPOSE 8080

# The command to start your bot
CMD ["python", "bot.py"]
