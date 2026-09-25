FROM python:3.12-slim
WORKDIR /app
COPY backend /app/backend
COPY config /app/config
RUN pip install --no-cache-dir -e /app/backend
ENV PYTHONPATH=/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
