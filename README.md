# Crypto AI Agent

Персональний AI-агент для аналізу криптовалютного та фондового ринку з використанням машинного навчання та великих мовних моделей (LLM).

**Дипломна робота** | Чередняк Ю.В. | 2026

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Зміст

- [Про проєкт](#про-проєкт)
- [Демонстрація](#демонстрація)
- [Технологічний стек](#технологічний-стек)
- [Структура репозиторію](#структура-репозиторію)
- [Встановлення та запуск](#встановлення-та-запуск)
- [API документація](#api-документація)
- [Releases](#releases)

---

## Про проєкт

Система поєднує:
- **ML-прогнозування цін** — ансамбль 13 моделей (Random Forest, XGBoost, LightGBM, SVM та ін.) з крос-валідацією
- **Технічний аналіз** — 59 індикаторів (RSI, MACD, Bollinger Bands, ATR та ін.)
- **NLP-аналіз новин** — FinBERT для визначення фінансової тональності
- **AI-чат агент** — каскадна fallback-стратегія між Claude, GPT-4o, Gemini, Llama 3
- **Бектестування** — перевірка ML-стратегій на історичних даних
- **Управління портфелем** — відстеження P&L у реальному часі

---

## Демонстрація

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Ринкові дані
![Market](screenshots/market.png)

### Технічний аналіз
![Analysis](screenshots/analysis.png)

### ML-прогнозування
![Predictions](screenshots/predictions.png)

### Бектестування стратегій
![Backtesting](screenshots/backtesting.png)

### Аналіз новин
![News](screenshots/news.png)

### AI-чат асистент
![Chat](screenshots/chat.png)

### Управління портфелем
![Portfolio](screenshots/portfolio.png)

### Дослідницький журнал
![Research](screenshots/research.png)

> Усі знімки екрана зроблені з локально запущеної системи. Папка [`screenshots/`](screenshots/) містить повний набір.

---

## Технологічний стек

| Шар | Технологія | Версія |
|-----|-----------|--------|
| Backend API | FastAPI + Uvicorn | 0.109 |
| ORM | SQLAlchemy (async) | 2.0 |
| ML | Scikit-learn, XGBoost, LightGBM | 1.4+ |
| NLP | FinBERT (HuggingFace Transformers) | 4.38 |
| LLM | Claude 3.5 / GPT-4o / Gemini / Llama 3 | — |
| Frontend | React + Vite + TypeScript | 18.2 |
| Styling | Tailwind CSS | 3.4 |
| Charts | Recharts | 2.10 |
| DB (main) | PostgreSQL | 15 |
| DB (research) | SQLite (aiosqlite) | — |
| Cache | Redis | 7 |
| Container | Docker + Docker Compose | 24 |

---

## Структура репозиторію

```
crypto-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/              # Маршрути API
│   │   │   ├── market.py     # Ринкові дані
│   │   │   ├── analysis.py   # Технічний аналіз
│   │   │   ├── predictions.py# ML-прогнозування
│   │   │   ├── news.py       # Аналіз новин
│   │   │   ├── ai_chat.py    # AI-чат (SSE)
│   │   │   ├── portfolio.py  # Портфель
│   │   │   ├── research.py   # Журнал досліджень
│   │   │   ├── users.py      # Авторизація
│   │   │   └── stocks.py     # Фондовий ринок
│   │   ├── core/
│   │   │   └── config.py     # Pydantic Settings
│   │   ├── db/
│   │   │   ├── database.py   # PostgreSQL (async)
│   │   │   └── research_db.py# SQLite (research)
│   │   ├── models/
│   │   │   └── models.py     # SQLAlchemy моделі
│   │   ├── schemas/
│   │   │   └── schemas.py    # Pydantic схеми
│   │   └── services/
│   │       ├── ml_service.py     # ML-прогнозування
│   │       ├── ai_service.py     # LLM fallback
│   │       ├── news_service.py   # FinBERT
│   │       ├── market_service.py # Binance/yfinance
│   │       └── backtest.py       # Бектестування
│   ├── main.py               # Точка входу FastAPI
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React-компоненти
│   │   ├── pages/            # Сторінки (Dashboard, Market …)
│   │   └── services/         # API-клієнти
│   ├── package.json
│   └── vite.config.ts
├── screenshots/              # Знімки екрана системи
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Встановлення та запуск

### Варіант 1 — Docker Compose (рекомендовано)

```bash
# 1. Клонувати репозиторій
git clone <repo-url>
cd crypto-ai-agent

# 2. Скопіювати конфігурацію
cp .env.example .env
# Відредагуйте .env: додайте ваші API-ключі

# 3. Запустити всі сервіси
docker-compose up -d

# 4. Перевірити статус
docker-compose ps
```

Відкрити у браузері:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

---

### Варіант 2 — Локальний запуск

#### Вимоги

| Інструмент | Версія |
|-----------|--------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ |
| Redis | 7+ |

#### Backend

```bash
cd backend

# Створити та активувати venv
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# Встановити залежності
pip install -r requirements.txt

# Налаштувати змінні середовища
cp ../.env.example ../.env
# Відредагуйте .env

# Запустити PostgreSQL і Redis (якщо не через Docker)
# postgres: psql -U postgres -c "CREATE DATABASE crypto_db;"

# Запуск
python main.py
# або: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Встановити залежності
npm install

# Запуск у режимі розробки
npm run dev
```

#### Змінні середовища (`.env`)

```env
# База даних
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/crypto_db
REDIS_URL=redis://localhost:6379

# LLM провайдери (хоча б один обов'язковий)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Ринкові дані
CRYPTOCOMPARE_API_KEY=...

# Безпека
SECRET_KEY=your-secret-key-here
```

---

## API документація

Інтерактивна документація доступна після запуску:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Ринкові дані — `/api/v1/market`

| Метод | Шлях | Опис |
|-------|------|------|
| GET | `/top` | Топ криптовалют за капіталізацією |
| GET | `/price/{symbol}` | Поточна ціна пари (напр. `BTC%2FUSDT`) |
| GET | `/quote/{symbol}` | Розширена цитата (ціна + зміна + обсяг) |
| GET | `/history/{symbol}` | OHLCV-дані за період |
| GET | `/search` | Пошук торгових пар |

**Приклад відповіді `GET /api/v1/market/price/BTC%2FUSDT`:**
```json
{
  "symbol": "BTC/USDT",
  "price": 97341.5,
  "change_24h": 2.34,
  "volume_24h": 28419503821.0,
  "timestamp": "2026-05-25T10:00:00Z"
}
```

---

### Технічний аналіз — `/api/v1/analysis`

| Метод | Шлях | Опис |
|-------|------|------|
| GET | `/indicators/{symbol}` | 59 технічних індикаторів |
| GET | `/signals/{symbol}` | Торгові сигнали (BUY/SELL/HOLD) |
| GET | `/trend/{symbol}` | Трендовий аналіз |
| GET | `/statistical/{symbol}` | Статистичні показники |
| POST | `/snapshot/{symbol}` | Зберегти знімок аналізу |

**Приклад відповіді `GET /api/v1/analysis/indicators/BTC%2FUSDT`:**
```json
{
  "symbol": "BTC/USDT",
  "indicators": {
    "rsi_14": 58.3,
    "macd": 234.5,
    "macd_signal": 198.2,
    "bb_upper": 101200.0,
    "bb_lower": 93400.0,
    "ema_20": 96800.0
  }
}
```

---

### ML-прогнозування — `/api/v1/predictions`

| Метод | Шлях | Опис |
|-------|------|------|
| GET | `/predict` | Прогноз ціни (параметри: symbol, periods, model) |
| POST | `/backtest` | Бектестування ML-стратегії |
| GET | `/compare/{symbol}` | Порівняння всіх 13 моделей |

**Запит `GET /api/v1/predictions/predict?symbol=BTC%2FUSDT&periods=7&model=ensemble`:**
```json
{
  "symbol": "BTC/USDT",
  "model": "ensemble",
  "periods": 7,
  "predictions": [97800, 98200, 97500, 99100, 100300, 98700, 101200],
  "metrics": {
    "mae": 1234.5,
    "rmse": 1876.3,
    "r2": 0.87,
    "mape": 1.23
  },
  "confidence": 0.73
}
```

---

### Аналіз новин — `/api/v1/news`

| Метод | Шлях | Опис |
|-------|------|------|
| POST | `/sentiment/{symbol}` | FinBERT-тональність новин |
| POST | `/insights` | AI-зведення новинного фону |

---

### AI-чат — `/api/v1/ai`

| Метод | Шлях | Опис |
|-------|------|------|
| POST | `/chat` | Синхронна відповідь |
| POST | `/chat/stream` | SSE-стримінг відповіді |

**Запит `POST /api/v1/ai/chat`:**
```json
{
  "message": "Проаналізуй BTC/USDT та дай торговий сигнал",
  "history": []
}
```

---

### Портфель — `/api/v1/portfolio`

| Метод | Шлях | Опис |
|-------|------|------|
| GET | `/` | Список активів портфеля |
| POST | `/` | Додати актив |
| GET | `/price-history/{symbol}` | Історія цін активу |

---

### Журнал досліджень — `/api/v1/research`

| Метод | Шлях | Опис |
|-------|------|------|
| POST | `/ml-run` | Зберегти результати ML-запуску |
| GET | `/ml-history` | Історія ML-досліджень |
| GET | `/ml-stats` | Агрегована статистика |
| POST | `/backtest-run` | Зберегти результат бектесту |
| GET | `/backtest-history` | Історія бектестів |
| GET/POST | `/notes` | Нотатки дослідника |
| GET/POST/DELETE | `/watchlist` | Список відстежуваних активів |

---

### Авторизація — `/api/v1/users`

| Метод | Шлях | Опис |
|-------|------|------|
| POST | `/register` | Реєстрація |
| POST | `/login` | Вхід (JWT) |
| GET | `/me` | Профіль поточного користувача |

---

## Releases

| Версія | Дата | Опис |
|--------|------|------|
| v1.0.0 | 2026-05-25 | Перший реліз — повна функціональна система |

### v1.0.0 — Що включено

- ML-прогнозування: ансамбль 13 моделей, TimeSeriesSplit крос-валідація
- Технічний аналіз: 59 індикаторів у реальному часі
- FinBERT NLP-аналіз новин
- AI-чат з каскадним fallback (Claude → GPT-4o → Gemini → Llama 3)
- SSE-стримінг відповідей чату
- Бектестування ML-стратегій vs Buy&Hold
- 9 сторінок інтерфейсу з 5 темами оформлення
- Docker Compose розгортання
- JWT-авторизація
- PostgreSQL + SQLite + Redis

---

## Troubleshooting

**Помилка підключення до PostgreSQL:**
```bash
docker-compose logs postgres
docker-compose restart postgres
```

**Помилка API-ключів LLM:**
```
Перевірте .env: хоча б один з ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY має бути дійсним.
Система автоматично перемикається між провайдерами.
```

**Порти вже зайняті:**
```bash
lsof -i :8000   # знайти процес
kill -9 <PID>   # зупинити
```

**Оновлення ML-моделей:**
```bash
# Перший запит до /api/v1/predictions/predict запускає навчання автоматично.
# Для примусового перенавчання: DELETE /api/v1/predictions/cache
```

---

## Ліцензія

MIT License — деталі у файлі [LICENSE](LICENSE).

---

## Автор

**Чередняк Юрій Васильович**
Дипломна робота — Кваліфікаційна робота магістра, 2026

> Проєкт призначений для освітніх цілей. Не є фінансовою порадою.
