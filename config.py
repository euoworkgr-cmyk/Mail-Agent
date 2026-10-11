"""Настройки Telegram-бота и моделей Polza.ai.

Впишите секреты ниже и ограничьте доступ к файлу: chmod 600 config.py
"""

TELEGRAM_BOT_TOKEN = "ВСТАВЬТЕ_ТОКЕН_ОТ_BOTFATHER"
POLZA_API_KEY = "ВСТАВЬТЕ_ЛИЧНЫЙ_КЛЮЧ_POLZA"

# Актуальные идентификаторы проверены в каталоге Polza.ai.
MODELS = {
    "haiku": {"name": "Claude Haiku 5.5", "id": "anthropic/claude-haiku-5.5"},
    "sonnet": {"name": "Claude Sonnet 5.5", "id": "anthropic/claude-sonnet-5.5"},
    "luna": {"name": "GPT-6 Luna", "id": "openai/gpt-6-luna"},
}

DEFAULT_MODEL = "haiku"
POLZA_BASE_URL = "https://polza.ai/api/v1"
MAX_CONTEXT_MESSAGES = 10  # user + assistant сообщений суммарно
MAX_OUTPUT_TOKENS = 800
SYSTEM_PROMPT = "Отвечай на языке пользователя. Будь полезным и кратким."
