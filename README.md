# Universal Security & OSINT Assistant

Кроссплатформенное Python-приложение с графическим интерфейсом для легального аудита безопасности систем и OSINT-разведки.

![NeonRecon — вкладка OSINT](assets/screenshot.png)

**Скачать Android APK:** [Releases → NeonRecon.apk](https://github.com/bimpiRU/NeonRecon/releases/latest)

## ⚠️ Дисклеймер

См. [DISCLAIMER.md](DISCLAIMER.md). Использование ПО допускается только на собственных системах или с письменного разрешения владельца. Разработчик не несёт ответственности за неправомерное использование.

## Возможности

- **Дашборд (Maltego-style):** сводка о системе, матрица доступности инструментов, автоматическое извлечение сущностей из логов (IP, домены, e-mail, телефоны), быстрые действия.
- **OPSEC:** смена hostname/MAC, запуск Tor + proxychains.
- **Сетевой аудит:** тихий nmap, пассивный MITM-анализ (bettercap/tcpdump), аудит МФУ через PRET.
- **OSINT:** DNS history, DNS-записи через DoH, пассивные поддомены (crt.sh), Wayback Machine, сбор поддоменов (subfinder), IP-разведка, полный анализ номеров (libphonenumber), проверка e-mail по утечкам, поиск никнейма по 19 площадкам.
- **Экспорт:** локальный отчёт `FINAL_REPORT.txt`, подготовка git-синхронизации.

## Что нового в v0.6

- **Автоаудит цели**: вводите домен или IPv4 — приложение само выполняет полный цикл (разрешение DNS → IP-разведка → DNS-записи DoH → поддомены crt.sh → Wayback → nmap top-100 и subfinder, если доступны) с фазовым выводом и сводкой. Ручные проверки сохранены. Работает и на ПК, и на телефоне (пассивные фазы — везде, nmap/subfinder — где установлены).
- **Вкладка «Отчёты»**: сжатый архив результатов (gzip-9, до ~37× экономии), ротация 200 отчётов, метаданные из имён файлов без распаковки, просмотр в лог, сохранение текущего лога одной кнопкой, удаление и очистка.
- **Визуал**: плавное появление вкладок (fade-in), hover-подсветка пунктов меню на десктопе, неоновый индикатор активной вкладки в сайдбаре.

## Что нового в v0.5

- **Адаптивная мобильная раскладка**: на узких экранах и Android боковое меню заменяется нижней навигационной панелью, карточки занимают всю ширину экрана. На десктопе раскладка переключается автоматически при изменении размера окна.
- **Телефонная разведка (Phone Intelligence)**: валидация и форматы (E.164/международный/национальный), регион, оператор, часовой пояс, тип линии (libphonenumber — работает и на Android), ссылки для ручной проверки в мессенджерах (wa.me, t.me, Viber) и поисковые дорки.
- **E-mail разведка**: проверка по легальным публичным агрегаторам утечек (XposedOrNot, LeakCheck public API) + MX-проверка домена. Только свои адреса или с согласия владельца.
- **Username Search**: проверка публичных профилей на 19 площадках (GitHub, Telegram, VK, Reddit, Steam и др.) по HTTP-статусам — как обычный визит браузера.
- **IP-разведка**: гео, провайдер, ASN, флаги VPN/proxy/Tor через ipwho.is (без ключа).
- **Пассивные поддомены через crt.sh** (Certificate Transparency) и **DNS-записи через DoH** с резервными резолверами (dns.google → 8.8.8.8 → Cloudflare → 1.1.1.1) — работает даже там, где dns.google заблокирован.
- Все новые OSINT-функции — чистый Python (requests + phonenumbers), работают **на Android без root и внешних утилит**.

## Что нового в v0.4

- **Metasploit Framework**: карточка во вкладке «Сеть» — проверка установки, `db_nmap` vuln-scan по цели, запуск произвольного модуля с RHOSTS и опциями (валидация ввода против инъекций).
- **Root-запрос**: кнопка «Запросить root (sudo -v)» в OPSEC; функции, требующие root (stealth, MITM, SYN-скан, msf), автоматически работают через `sudo -n`, статус привилегий виден на дашборде.
- **Docker**: в образ добавлены `metasploit-framework` и `sudo`.

## Что нового в v0.3

- **Увеличенный современный UI** (~×1.25): окно 1360×860, крупная типографика, просторные карточки, разделители панелей.
- **Android-закалка**: `pillow` в зависимостях, убран неиспользуемый `python-whois`; `preexec_fn`/`killpg` отключены на Android (предотвращает падения); при ошибке запуска показывается экран с traceback вместо молчаливого закрытия, crash-лог пишется и на `/sdcard/neonrecon_crash.log`.

## Что нового в v0.2

- **5 языков интерфейса** (RU / EN / ES / DE / ZH) с переключением на лету и сохранением выбора.
- **Стабильность:** реестр фоновых задач, отмена всех задач одной кнопкой (kill всей группы процессов), таймауты, crash-handler с записью в `~/neonrecon_crash.log`.
- **Журнал операций:** цветные уровни, фильтры (ВСЕ/OK/INFO/WARN/ERROR), очистка и копирование в буфер.
- **Статус-бар:** счётчик активных задач, таймер сессии, кнопка «Стоп все».
- **UX:** дисклеймер показывается один раз (согласие сохраняется в `~/.usosint/config.json`).

## Поддерживаемые платформы

- **Kali Linux / Debian / Ubuntu** — полная функциональность (при наличии root и инструментов).
- **Windows** — ограниченная функциональность; внешние утилиты должны быть установлены отдельно.
- **Android** — полноценный OSINT (домены, IP, телефоны, e-mail, никнеймы) и адаптивный UI; сетевой аудит и OPSEC требуют внешних утилит (недоступны без root).

## Развёртывание на Kali Linux

### 1. Установка системных зависимостей

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git nmap tor proxychains4 bettercap tcpdump macchanger
```

### 2. Установка subfinder

```bash
sudo apt install -y subfinder
```

### 3. Установка PRET

```bash
cd /opt
sudo git clone https://github.com/RUB-NDS/PRET.git
sudo pip install -r PRET/requirements.txt
sudo ln -s /opt/PRET/pret.py /usr/local/bin/pret
```

### 4. Установка Python-зависимостей

```bash
cd UniversalSecurityOSINTAssistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Запуск

```bash
python main.py
```

Для полноценного использования функций смены MAC/hostname и SYN-сканирования запускайте с правами root:

```bash
sudo ./venv/bin/python main.py
```

## Сборка Android .apk через Buildozer

### 1. Установка зависимостей сборки

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip install buildozer cython
```

### 2. Сборка APK

```bash
cd UniversalSecurityOSINTAssistant
buildozer -v android debug
```

Готовый APK появится в директории `bin/`.

### 3. Установка на устройство

```bash
buildozer android deploy run
```

## Docker

Образ на базе Kali Linux со всеми инструментами (nmap, tor, proxychains4, tcpdump, macchanger, whois, subfinder, bettercap).

```bash
# сборка
docker build -t neonrecon .

# headless-запуск (GUI в виртуальном Xvfb — для тестов)
docker run --rm neonrecon

# с выводом GUI на хостовый X-сервер (Linux)
xhost +local:docker
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix neonrecon gui
```

Публикация в Docker Hub: `docker login && docker tag neonrecon <user>/neonrecon:0.3 && docker push <user>/neonrecon:0.3`.

## Тестирование и подключение реального Android-устройства

**Эмулятор:** приложение протестировано на Android Emulator (API 30, x86_64) — полный цикл: запуск, принятие дисклеймера, переключение всех вкладок, автоаудит `example.com`, сохранение отчёта gzip-9 и просмотр архива во вкладке «Отчёты».

**Реальный телефон по USB:**
1. Включи режим разработчика и **«Отладка по USB»**.
2. На HyperOS/Xiaomi/Redmi включи также **«Отладка по USB (настройки безопасности)**».
3. В шторке выбери режим **«Передача файлов»** (MTP), а не «Только зарядка».
4. Установи USB-драйвер производителя (например, **Xiaomi USB Driver** для HyperOS); иначе Windows не увидит ADB-интерфейс.
5. При первом подключении на телефоне появится диалог RSA — нажми **OK**.

```bash
adb devices -l
adb install -r NeonRecon.apk
```

**Реальный телефон по Wi-Fi (Android 11+):**
1. Настройки → Для разработчиков → **Wireless debugging** → ON.
2. «Pair with pairing code» → скопируй `IP:port` и 6-значный код.
3. На ПК:

```bash
adb pair <IP>:<port> <pairing_code>
adb connect <IP>:<port>
adb install -r NeonRecon.apk
```

## Структура проекта

```
UniversalSecurityOSINTAssistant/
├── main.py              # Точка входа
├── requirements.txt     # Python-зависимости
├── buildozer.spec       # Конфигурация сборки Android
├── DISCLAIMER.md        # Юридический дисклеймер
├── README.md            # Этот файл
├── usosint/
│   ├── app.py           # Корневой виджет
│   ├── ui/              # Компоненты интерфейса (дашборд, вкладки, журнал, виджеты)
│   ├── core/            # Логгер, executor, i18n, конфиг, буфер обмена, платформа
│   └── modules/         # Функциональные модули
```

## Лицензия

Проект распространяется как есть (AS IS) исключительно в образовательных целях.
