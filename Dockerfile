FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /data/uploads

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV UPLOAD_DIR=/data/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
