FROM python:3.11-slim

# 安装字体（文泉驿微米黑 + DejaVu 矢量音标）与时区工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fonts-dejavu-core \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ /app/

VOLUME ["/app/data"]

EXPOSE 8085

CMD ["python3", "server.py", "8085"]