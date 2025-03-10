FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install required packages for Streamlit
RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly with pip
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
EXPOSE 8501

# Let docker-compose.yml override this
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]