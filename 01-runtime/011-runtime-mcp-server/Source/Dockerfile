# MCP Server container for AgentCore Runtime
# AgentCore expects MCP servers at: 0.0.0.0:8000/mcp
FROM python:3.11-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["python3", "app/agent.py"]
