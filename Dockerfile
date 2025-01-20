# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Git (needed to pull updates)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone your GitHub repository into the container
RUN git clone https://github.com/danielhkuo/walpurgisbot.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint to our script
ENTRYPOINT ["/entrypoint.sh"]
