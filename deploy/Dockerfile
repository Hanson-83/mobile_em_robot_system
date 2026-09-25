FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml /tmp/pyproject.toml
# 安装依赖：复制 backend 后再 editable 安装
COPY backend /app
RUN pip install --no-cache-dir -e ".[dev]"
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
