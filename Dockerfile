FROM 5hojib/aeon:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

# Install mega-cmd
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://mega.nz/linux/repo/Debian_11/amd64/megacmd-Debian_11_amd64.deb && \
    apt-get install -y ./megacmd-Debian_11_amd64.deb && \
    rm megacmd-Debian_11_amd64.deb && \
    apt-get clean

RUN uv venv
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["bash", "start.sh"]
