FROM python:3.13-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Set link mode to copy (prevents hardlink warning)
ENV UV_LINK_MODE=copy

COPY . ./

RUN uv pip install --system .
RUN chmod +x entrypoint.py

ENV PYTHONPATH=/app/src:$PYTHONPATH

ENTRYPOINT ["python", "/app/entrypoint.py"]
