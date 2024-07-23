# Use a base image compatible with ARM architecture
FROM arm32v7/python:3.10-buster

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Bluetooth tools
RUN apt-get update && \
    apt-get install -y \
    libglib2.0-dev \
    libatlas-base-dev \
    libhdf5-dev \
    bluetooth \
    bluez \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port the app runs on
EXPOSE 9090

# Run the application
CMD ["python", "app.py"]
