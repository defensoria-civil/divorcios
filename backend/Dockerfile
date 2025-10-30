FROM python:3.12-slim

# Ensure Python/pip do not buffer and disable pip cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Add corporate root CA and point OpenSSL/Requests to system bundle
COPY certs/fortinet_corporate_root.crt /usr/local/share/ca-certificates/fortinet_corporate_root.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app/backend
COPY requirements.txt /app/backend/requirements.txt

# Install required packages, register the corporate CA, then install Python deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        build-essential \
    && update-ca-certificates \
    && pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org -r /app/backend/requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY src /app/backend/src
ENV PYTHONPATH=/app/backend/src
EXPOSE 8000
CMD ["uvicorn", "presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
