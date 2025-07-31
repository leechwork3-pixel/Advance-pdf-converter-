# Use an official Debian image that supports Calibre's dependencies
FROM debian:bullseye-slim

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, including Python and Calibre from the repository.
# This is much faster and more cache-friendly than the previous installer script.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    calibre && \
    # Clean up apt caches to reduce image size
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements first to leverage Docker's build cache.
# This layer will only be re-built if your requirements.txt file changes.
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container.
# This is the last step, so changes to your bot's code will be fast to build.
COPY . .

# Define the command to run the bot when the container starts
CMD ["python3", "bot.py"]
