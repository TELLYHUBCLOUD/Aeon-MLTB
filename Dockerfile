FROM shabbirmahmud/aimmlbot:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN uv venv
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

COPY . .
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
CMD ["bash", "start.sh"]