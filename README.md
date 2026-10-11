# Telegram-бот для Polza.ai

Бот принимает текстовые сообщения в Telegram, вызывает выбранную модель через совместимый с OpenAI API Polza.ai и отвечает в чате. API-ключи хранятся отдельно в `config.py`.

## Проверенные модели и API

Каталог Polza.ai указывает следующие ID:

| Название | ID |
| --- | --- |
| Claude Haiku 5.5 | `anthropic/claude-haiku-5.5` |
| Claude Sonnet 5.5 | `anthropic/claude-sonnet-5.5` |
| GPT-6 Luna | `openai/gpt-6-luna` |

Официальный сайт Polza.ai показывает базовый URL `https://polza.ai/api/v1` и запросы чата через `/chat/completions`. Ссылки: [API и каталог Claude](https://polza.ai/providers/anthropic), [Haiku 5.5](https://polza.ai/models/anthropic/claude-haiku-5.5), [Sonnet 5.5](https://polza.ai/models/anthropic/claude-sonnet-5.5), [GPT-6 Luna](https://polza.ai/models/openai/gpt-6-luna). Ссылка на отдельный домен документации `docs.polza.ai` при проверке ответила 503; endpoint и ID сверены по официальным страницам Polza.ai.

## Возможности и расход контекста

- `/model` — выбор модели кнопками. При смене модели история очищается.
- `/clear` — удалить историю текущего пользователя.
- История хранит не более 10 сообщений пользователя и ассистента суммарно (до пяти последних пар). Системное сообщение короткое и всегда добавляется отдельно.
- История хранится только в оперативной памяти процесса: после перезапуска она сбрасывается.
- `max_tokens` ограничивает ответ 800 токенами. Уменьшите `MAX_OUTPUT_TOKENS` в `config.py`, если хотите снизить верхний предел расхода; задайте больше, если ответы обрезаются.
- Файлы, фото, аудио и другие нетекстовые сообщения не отправляются модели.

## Установка на Linux

Пример для Debian/Ubuntu. Команды запускайте от пользователя с правами sudo.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
sudo useradd --system --home /opt/telegram-polza-bot --shell /usr/sbin/nologin telegrambot
sudo mkdir -p /opt/telegram-polza-bot
sudo cp bot.py config.py requirements.txt /opt/telegram-polza-bot/
sudo chown -R telegrambot:telegrambot /opt/telegram-polza-bot
sudo -u telegrambot python3 -m venv /opt/telegram-polza-bot/.venv
sudo -u telegrambot /opt/telegram-polza-bot/.venv/bin/pip install -r /opt/telegram-polza-bot/requirements.txt
sudo chmod 600 /opt/telegram-polza-bot/config.py
```

Перед запуском откройте `/opt/telegram-polza-bot/config.py` и укажите:

1. `TELEGRAM_BOT_TOKEN` — токен бота, созданного через `@BotFather`.
2. `POLZA_API_KEY` — личный API-ключ из кабинета Polza.ai.

Секреты не публикуйте и не добавляйте в общедоступный репозиторий. Владелец `telegrambot` должен иметь возможность прочитать `config.py`.

### Проверка вручную

```bash
sudo -u telegrambot /opt/telegram-polza-bot/.venv/bin/python /opt/telegram-polza-bot/bot.py
```

Откройте бота в Telegram и отправьте `/start`. Остановите ручной процесс `Ctrl+C` перед включением systemd.

### Запуск через systemd

```bash
sudo cp telegram-polza-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-polza-bot
sudo systemctl status telegram-polza-bot
```

Журнал ошибок и работы:

```bash
sudo journalctl -u telegram-polza-bot -f
```

После правки конфигурации перезапустите сервис:

```bash
sudo systemctl restart telegram-polza-bot
```

Для обновления кода замените файлы в `/opt/telegram-polza-bot` с сохранением `config.py`, затем перезапустите сервис.
