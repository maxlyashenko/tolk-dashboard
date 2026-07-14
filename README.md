# Tolk Sales Dashboard

Веб-приложение для Head of Sales агентства Tolk.  
Flask + SQLite бэкенд, авторизация по паролю.

---

## Быстрый старт (локально)

```bash
pip install flask gunicorn
python start.py
# Открой http://localhost:5000
# Пароль: tolk2026
```

---

## Деплой на Railway (бесплатно, 5 минут)

1. Зайди на [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Загрузи папку на GitHub (или используй Railway CLI)
3. Railway сам определит Python и запустит через Procfile
4. В разделе **Variables** добавь переменные:

| Переменная | Значение |
|---|---|
| `APP_PASSWORD` | твой пароль |
| `SECRET_KEY` | любая случайная строка |
| `DB_PATH` | `/data/tolk.db` (или оставь по умолчанию) |

5. Готово — Railway даст тебе URL вида `https://tolk-xxx.up.railway.app`

> ⚠️ На бесплатном Railway база данных хранится в ephemeral storage и сбрасывается при рестарте.  
> Для постоянного хранения добавь **Railway Volume** или используй Render/VPS.

---

## Деплой на Render (бесплатно, постоянная база)

1. [render.com](https://render.com) → New Web Service → подключи GitHub
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Environment Variables:
   - `APP_PASSWORD` = твой пароль
   - `SECRET_KEY` = случайная строка
5. Добавь **Disk** (в разделе настроек): Mount Path `/data`, размер 1GB
6. Поставь `DB_PATH=/data/tolk.db` в переменных

---

## Деплой на VPS (Hetzner/DigitalOcean, ~€4/мес)

```bash
# На сервере Ubuntu 22.04
git clone <твой репо> /var/www/tolk
cd /var/www/tolk

pip install -r requirements.txt

# Создай .env
cat > .env << EOF
APP_PASSWORD=мой_пароль_здесь
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DB_PATH=/var/www/tolk/tolk.db
PORT=8000
EOF

# Запусти через systemd или screen
gunicorn app:app --bind 127.0.0.1:8000 --workers 2

# Nginx конфиг (опционально)
# proxy_pass http://127.0.0.1:8000;
```

Первый запуск инициализирует базу и засеет все исторические данные автоматически.

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_PASSWORD` | `tolk2026` | Пароль для входа |
| `SECRET_KEY` | `tolk-change-me-in-production` | Секрет сессии Flask |
| `DB_PATH` | `tolk.db` | Путь к файлу SQLite |
| `PORT` | `5000` | Порт сервера |

---

## Структура

```
tolk-dashboard/
├── app.py              ← Flask бэкенд + REST API
├── start.py            ← Локальный запуск
├── requirements.txt    ← Flask + Gunicorn
├── Procfile            ← Для Railway/Render
├── README.md
└── templates/
    ├── login.html      ← Страница входа
    └── index.html      ← Дашборд
```

## API эндпоинты

```
GET/POST        /api/pays
PUT/DELETE      /api/pays/<id>

GET/POST        /api/months
PUT/DELETE      /api/months/<key>

GET/POST        /api/expenses
PUT/DELETE      /api/expenses/<id>

GET/POST        /api/pipeline
PUT/DELETE      /api/pipeline/<id>

POST            /api/reset   ← сброс к начальным данным
```
