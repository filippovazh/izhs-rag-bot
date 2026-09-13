import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"
import logging
from src.config import config
from src.bot.handlers import (
    start,
    start_button,
    land_question,
    land_selected,
    vri_selected,
    project_selected,
    demolition_selected,
    cancel,
    free_question,
    SELECTING_LAND,
    SELECTING_VRI,
    SELECTING_PROJECT,
    SELECTING_DEMOLITION
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Запускает Telegram бота."""

    # === ПРОВЕРКА ТОКЕНА ===
    if not config or not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в .env файле!")
        logger.error("Создайте файл .env с переменной BOT_TOKEN=ваш_токен")
        return

    logger.info("Запуск бота...")

    try:
        app = Application.builder().token(config.BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                MessageHandler(filters.Regex('^🏗️ Начать консультацию$'), start_button)
            ],
            states={
                SELECTING_LAND: [
                    CommandHandler('start', start),
                    MessageHandler(filters.Regex(r'^✅ Да, есть$'), land_selected),
                    MessageHandler(filters.Regex(r'^❌ Нет, пока нет$'), land_selected),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, land_question)
                ],
                SELECTING_VRI: [
                    CommandHandler('start', start),
                    MessageHandler(filters.Regex(r'^✅ Да, подходит$'), vri_selected),
                    MessageHandler(filters.Regex(r'^❌ Нет, не подходит$'), vri_selected),
                    MessageHandler(filters.Regex(r'^🤷 Не знаю$'), vri_selected),
                    MessageHandler(filters.Regex(r'^ℹ️ Подробнее про УРВИ$'), vri_selected),
                    MessageHandler(filters.Regex(r'^➡️ Продолжить$'), vri_selected),
                    MessageHandler(filters.Regex(r'^➡️ Продолжить без изменения ВРИ$'), vri_selected),
                    MessageHandler(filters.Regex(r'^🔙 Назад к вопросам$'), vri_selected),
                    MessageHandler(filters.Regex(r'^🔙 Написать другой ВРИ$'), vri_selected),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, vri_selected),
                ],
                SELECTING_PROJECT: [
                    CommandHandler('start', start),
                    MessageHandler(filters.Regex(r'^✅ Да, есть$'), project_selected),
                    MessageHandler(filters.Regex(r'^❌ Нет, ищу проект$'), project_selected),
                    MessageHandler(filters.Regex(r'^✅ Проект найден, продолжаем!$'), project_selected),
                ],
                SELECTING_DEMOLITION: [
                    CommandHandler('start', start),
                    MessageHandler(filters.Regex(r'^✅ Да, планируется снос$'), demolition_selected),
                    MessageHandler(filters.Regex(r'^❌ Нет, строю с нуля$'), demolition_selected),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel),
                CommandHandler('start', start)
            ]
        )

        # === РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ===
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_question))

        # === ЗАПУСК БОТА ===
        logger.info("Бот успешно запущен! Ожидаю сообщения...")
        app.run_polling(allowed_updates=["message"])

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()