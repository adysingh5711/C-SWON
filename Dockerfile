FROM python:3.11-slim

LABEL maintainer="C-SWON Team"
LABEL description="C-SWON executor image — sandboxed workflow execution (readme §4.8 step 3)"

WORKDIR /app

# Install system deps needed for pycodestyle and subprocess execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pycodestyle>=2.11

# Copy the entire codebase
COPY . .
RUN pip install --no-cache-dir -e .

# Healthcheck: verify the entrypoint can be imported
RUN python -c "from cswon.validator.executor_entrypoint import main; print('import OK')"

# Entry point invoked by docker_sandbox.py:
#   docker run --env CSWON_WORKFLOW_PAYLOAD=... cswon-executor:latest
CMD ["python", "-m", "cswon.validator.executor_entrypoint"]
