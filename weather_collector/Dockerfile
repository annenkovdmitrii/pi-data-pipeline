FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install uv directly with pip
RUN pip install --no-cache-dir uv

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY weather_collector.py .

# Command to run on container start
CMD ["python", "weather_collector.py"]
