FROM python:3.11-slim

WORKDIR /app

# Install system deps for Flet web
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgstreamer1.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8550

CMD ["python", "-m", "lang_mastering.main"]
