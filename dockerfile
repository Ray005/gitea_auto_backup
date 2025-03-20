FROM python:3.10-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webhook_receiver.py .

# 设置环境变量
ENV PORT=5000

EXPOSE 5000
