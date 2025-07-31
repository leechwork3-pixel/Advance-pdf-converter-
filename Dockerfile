# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We also install git for potential dependencies, though not strictly needed by this list
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY bot/ ./bot/

# Command to run the application
CMD ["python3", "-m", "bot.bot"]
