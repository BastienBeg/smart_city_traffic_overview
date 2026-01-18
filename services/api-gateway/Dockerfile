FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for building some python packages if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy common lib
COPY ./services/common_lib /app/services/common_lib

# Copy service dependencies
COPY ./services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY ./services/api-gateway/src /app/src

# Set python path to include common_lib
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
