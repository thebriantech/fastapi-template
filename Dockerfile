# ---- Base stage ----
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies + ODBC driver for MSSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gnupg2 \
        unixodbc-dev && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# ---- Dependencies stage ----
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Development stage ----
FROM dependencies AS development

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p app/logs/logs_data

EXPOSE 8000

# Hot-reload enabled for development
CMD ["uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- Production stage ----
FROM dependencies AS production

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p app/logs/logs_data

EXPOSE 8000

CMD ["uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000"]
