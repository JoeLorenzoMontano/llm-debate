FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt ./
COPY web/requirements.txt ./web/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r web/requirements.txt

# Copy application code
COPY llm_debate/ ./llm_debate/
COPY web/ ./web/
COPY setup.py ./

# Install the package
RUN pip install -e .

# Expose port
EXPOSE 8000

# Run the web server
CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
