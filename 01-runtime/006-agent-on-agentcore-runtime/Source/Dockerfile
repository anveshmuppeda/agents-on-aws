# AgentCore Runtime container image
#
# AgentCore Runtime requires:
#   - ARM64 architecture
#   - HTTP server listening on port 8080
#   - POST /invocations endpoint
#   - JSON request/response
#
# The bedrock_agentcore package's BedrockAgentCoreApp sets all this up.
FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# AgentCore Runtime calls: POST http://localhost:8080/invocations
# BedrockAgentCoreApp.run() starts uvicorn on that port/path.
EXPOSE 8080

CMD ["python3", "-m", "app.agent"]
