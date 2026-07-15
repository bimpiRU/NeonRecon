# NeonRecon — Universal Security & OSINT Assistant
# Образ на базе Kali Linux со всеми инструментами аудита.
#
# Сборка:   docker build -t neonrecon .
# Headless: docker run --rm neonrecon            (GUI в виртуальном Xvfb)
# С GUI:    xhost +local:docker && \
#           docker run --rm -e DISPLAY=$DISPLAY \
#             -v /tmp/.X11-unix:/tmp/.X11-unix neonrecon gui

FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

# Инструменты аудита + графические зависимости Kivy (SDL2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    git curl ca-certificates \
    nmap tor proxychains4 tcpdump macchanger whois subfinder bettercap \
    xvfb xauth \
    libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
    libgl1 libglib2.0-0 libx11-6 libxext6 libxrender1 libsm6 libice6 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-зависимости (кэшируемый слой)
COPY requirements.txt ./
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH="/opt/venv/bin:$PATH"

# По умолчанию — headless запуск через Xvfb; "gui" — на хостовый X-сервер
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["xvfb-run -a python main.py"]
