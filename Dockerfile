# 使用Python 3.9或更高版本
FROM python:3.9-slim-bullseye

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖文件（优先复制 requirements.txt，利用 Docker 缓存）
COPY requirements.txt .
	


# 使用阿里云镜像源（bullseye版本）
RUN echo "deb http://mirrors.aliyun.com/debian/ bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 5. 安装Python依赖（使用阿里云镜像加速）
RUN pip install --no-cache-dir \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt



# 6. 复制项目代码（最后复制，避免频繁缓存失效）
COPY . .

# 创建日志目录
RUN mkdir -p /var/log/gitlab/nginx

# 暴露端口
EXPOSE 5000

# 设置环境变量（用户可以通过docker run -e覆盖）
ENV LOG_DIR=/var/log/gitlab/nginx
ENV BIN_INDEX_PATH=map/dbip_index.bin
ENV GEO_TEXT_PATH=map/dbip_geo.txt
ENV TOP_N=20

# 启动应用
CMD ["python", "nginx_ip_geo_stats.py"]
