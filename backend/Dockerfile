# Build context is the repo root (see docker-compose.yml), since
# requirements-dev.txt pulls in ../requirements.txt.
FROM python:3.11-slim

WORKDIR /srv

COPY requirements.txt ./requirements.txt
COPY backend/ ./backend/

WORKDIR /srv/backend
RUN pip install --no-cache-dir -r requirements-dev.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
