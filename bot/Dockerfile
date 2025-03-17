FROM python:3.9-slim

WORKDIR /weekscounter

ARG TZ=UTC  # Часовой пояс
ENV TZ=${TZ}

RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p db logs && \
    chmod -R 755 /weekscounter/db /weekscounter/logs

CMD ["python", "main.py"]
