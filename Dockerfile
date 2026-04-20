# Dockerfile for property_maintenance backend
FROM alpine:3.13

# Install Chinese fonts for PDF generation
RUN apk add --update --no-cache \
    ca-certificates \
    tzdata \
    font-noto-cjk \
    python3 py3-pip py3-greenlet \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo Asia/Shanghai > /etc/timezone \
    && rm -rf /var/cache/apk/*

# Use Tencent mirror for pip
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
&& pip config set global.trusted-host mirrors.cloud.tencent.com \
&& pip install --upgrade pip \
&& pip install --user -r requirements.txt

WORKDIR /app
COPY . /app

EXPOSE 80

CMD ["python3", "run.py", "0.0.0.0", "80"]