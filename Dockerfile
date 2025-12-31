FROM 5hojib/aeon:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

# Install mega-cmd (updated method)
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -qO - https://mega.nz/linux/repo/Debian_12/Release.key | apt-key add - && \
    echo "deb https://mega.nz/linux/repo/Debian_12/ ./" > /etc/apt/sources.list.d/megasync.list && \
    apt-get update && \
    apt-get install -y megacmd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN uv venv
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["bash", "start.sh"]
