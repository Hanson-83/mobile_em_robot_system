FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .
ENV MER_DATABASE_URL=sqlite:////data/mer.db \
    MER_REPORTS_DIR=/data/reports \
    MER_BACKUP_DIR=/data/backups \
    MER_CONFIG_DIR=/config
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
