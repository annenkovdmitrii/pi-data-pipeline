FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

# Let docker-compose.yml override this
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]