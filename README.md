# ИЖС RAG-бот

Telegram-бот для навигации по строительному законодательству (ИЖС) на базе RAG (Retrieval-Augmented Generation).

## Проблема

Люди, планирующие строительство дома на участке ИЖС, сталкиваются с юридическими сложностями: уведомительный порядок, сроки, документы, требования к ВРИ. Обычный поиск в законах занимает часы. Бот решает эту задачу: задаёт несколько вопросов и выдаёт персональную пошаговую инструкцию.

## Что делает

- Ведёт диалог с пользователем через кнопки и свободные вопросы.
- Ищет релевантные статьи законов в векторной базе (ChromaDB).
- Формирует понятный ответ на основе найденных фрагментов и GigaChat.

## Стек

- **Python 3.13**
- **python-telegram-bot** — Telegram API
- **ChromaDB** — векторная база данных
- **sentence-transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) — эмбеддинги
- **GigaChat API** — генерация ответов
- **python-docx** — чтение исходных законов

## Структура проекта

```
izhs-rag-bot/
├── src/
│   ├── bot/           # Telegram-хендлеры и логика диалога
│   ├── core/          # retrieval (поиск) и generation (GigaChat)
│   ├── utils/         # вспомогательные функции
│   └── config.py      # конфигурация из .env
├── main.py            # точка входа, запуск бота
├── indexer.py         # индексация законов в ChromaDB
├── merge_laws.py      # сборка исходных документов в один .docx
├── prompt.txt         # шаблон промпта для GigaChat
├── requirements.txt
└── .env.example
```

## Установка и запуск

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/filippovazh/izhs-rag-bot.git
   cd izhs-rag-bot
   ```

2. Создай виртуальное окружение и установи зависимости:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

3. Создай `.env` на основе `.env.example` и заполни:
   ```
   BOT_TOKEN=твой_токен_от_BotFather
   GIGACHAT_CLIENT_ID=твой_client_id
   GIGACHAT_SECRET=твой_secret
   ```

4. Запусти индексацию (выполнять один раз):
   ```bash
   python indexer.py
   ```

5. Запусти бота:
   ```bash
   python main.py
   ```

## Запуск в России

Telegram API заблокирован. Для работы бота нужен VPN или прокси. В `main.py` предусмотрена настройка через переменные окружения `HTTP_PROXY` / `HTTPS_PROXY` — укажи там адрес своего локального прокси.

## Автор

Филиппова Евгения — [GitHub](https://github.com/filippovazh)