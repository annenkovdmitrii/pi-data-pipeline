FROM python:3.9-slim

WORKDIR /app

# Install required packages for Sense HAT
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    python3-smbus \
    libopenjp2-7 \
    libatlas-base-dev \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install RTIMULib
RUN git clone https://github.com/RPi-Distro/RTIMULib.git && \
    cd RTIMULib/Linux/python && \
    python setup.py build && \
    python setup.py install && \
    cd ../../.. && \
    rm -rf RTIMULib

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sensor_collector_host.py .

CMD ["python", "sensor_collector_host.py"]
