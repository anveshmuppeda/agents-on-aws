# Lambda container image for the guide-005 agent
# Uses the official AWS Lambda Python 3.11 base image (ARM64)
FROM public.ecr.aws/lambda/python:3.11-arm64

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ${LAMBDA_TASK_ROOT}/app/

# Lambda handler: app/agent.py → handler() function
CMD ["app.agent.handler"]
