FROM python:3.11-slim

WORKDIR /app

# Copy dependency list
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./

# 暴露 FastAPI port
EXPOSE 8080

# 啟動命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
