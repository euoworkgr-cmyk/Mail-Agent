"""Telegram-бот, передающий текстовые запросы в Polza.ai."""

import logging
from collections import defaultdict, deque

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, OpenAIError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)
from telegram.request import HTTPXRequest

import config

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.POLZA_API_KEY, base_url=config.POLZA_BASE_URL,
                     timeout=60.0, max_retries=2)

# История хранится только в памяти процесса и отдельно для каждого пользователя.
histories = defaultdict(lambda: deque(maxlen=config.MAX_CONTEXT_MESSAGES))


def model_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(item["name"], callback_data=f"model:{key}")]
            for key, item in config.MODELS.items()]
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = context.user_data.get("model", config.DEFAULT_MODEL)
    await update.message.reply_text(
        "Привет! Отправьте текстовый запрос — я передам его выбранной модели Polza.ai.\n"
        f"Сейчас выбрана: {config.MODELS[current]['name']}\n"
        "Команды: /model — выбрать модель, /clear — очистить контекст."
    )


async def choose_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Выберите модель:", reply_markup=model_keyboard())


async def model_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    key = query.data.partition(":")[2]
    if key not in config.MODELS:
        await query.edit_message_text("Неизвестная модель. Вызовите /model ещё раз.")
        return
    context.user_data["model"] = key
    # Не смешиваем контекст запросов к разным моделям.
    histories[query.from_user.id].clear()
    await query.edit_message_text(f"Выбрана модель: {config.MODELS[key]['name']}. Контекст очищен.")


async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    histories[update.effective_user.id].clear()
    await update.message.reply_text("Контекст очищен.")


async def send_long_message(update: Update, text: str) -> None:
    # Telegram ограничивает длину текстового сообщения примерно 4096 символами.
    for start_at in range(0, len(text), 4000):
        await update.message.reply_text(text[start_at:start_at + 4000])


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    history = histories[user_id]
    model_key = context.user_data.get("model", config.DEFAULT_MODEL)
    history.append({"role": "user", "content": update.message.text})
    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}, *list(history)]

    await update.effective_chat.send_action(ChatAction.TYPING)
    try:
        response = await client.chat.completions.create(
            model=config.MODELS[model_key]["id"],
            messages=messages,
            max_tokens=config.MAX_OUTPUT_TOKENS,
        )
        answer = response.choices[0].message.content
        if not answer:
            answer = "Модель вернула пустой ответ. Попробуйте изменить запрос."
        history.append({"role": "assistant", "content": answer})
        await send_long_message(update, answer)
    except APITimeoutError:
        history.pop()
        await update.message.reply_text("Polza.ai не ответила вовремя. Повторите запрос чуть позже.")
    except APIConnectionError:
        history.pop()
        await update.message.reply_text("Не удалось подключиться к Polza.ai. Проверьте сеть и повторите позже.")
    except APIStatusError as exc:
        history.pop()
        logger.warning("Polza API returned HTTP %s", exc.status_code)
        if exc.status_code in (401, 403):
            note = "Проверьте POLZA_API_KEY в config.py."
        elif exc.status_code == 429:
            note = "Слишком много запросов или исчерпан лимит. Повторите позже и проверьте баланс Polza.ai."
        elif exc.status_code == 400:
            note = "Polza.ai отклонила запрос. Проверьте доступность модели и параметры."
        else:
            note = "Попробуйте позже. Подробности записаны в журнал сервиса."
        await update.message.reply_text(f"Ошибка Polza.ai (HTTP {exc.status_code}). {note}")
    except OpenAIError:
        history.pop()
        logger.exception("Polza API client error")
        await update.message.reply_text("Ошибка клиента API. Подробности записаны в журнал сервиса.")
    except Exception:
        history.pop()
        logger.exception("Unexpected error handling Telegram message")
        await update.message.reply_text("Внутренняя ошибка бота. Попробуйте позже.")


async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Пока поддерживаются только текстовые сообщения.")


def main() -> None:
    if "ВСТАВЬТЕ_" in config.TELEGRAM_BOT_TOKEN or "ВСТАВЬТЕ_" in config.POLZA_API_KEY:
        raise SystemExit("Заполните TELEGRAM_BOT_TOKEN и POLZA_API_KEY в config.py")
    builder = Application.builder().token(config.TELEGRAM_BOT_TOKEN)
    if config.TELEGRAM_PROXY:
        # Telegram использует отдельные HTTP-клиенты для API-запросов и polling.
        api_request = HTTPXRequest(proxy=config.TELEGRAM_PROXY, connect_timeout=30)
        updates_request = HTTPXRequest(
            proxy=config.TELEGRAM_PROXY,
            connect_timeout=30,
            read_timeout=30,
        )
        builder = builder.request(api_request).get_updates_request(updates_request)
    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", choose_model))
    app.add_handler(CommandHandler("clear", clear_context))
    app.add_handler(CallbackQueryHandler(model_selected, pattern=r"^model:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
