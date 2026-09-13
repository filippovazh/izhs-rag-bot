import logging

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from src.core.generation import (
    generate_instruction_from_codex,
    generate_no_land_answer,
    ask_gigachat
)
from src.core.retrieval import find_articles
from src.utils.text_utils import clean_response, load_prompt

# НАСТРОЙКА ЛОГГЕРА
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# СОСТОЯНИЯ ДИАЛОГА
SELECTING_LAND, SELECTING_VRI, SELECTING_PROJECT, SELECTING_DEMOLITION = range(4)

# === КЛЮЧЕВЫЕ СЛОВА ДЛЯ FREE_QUESTION ===
IZHS_KEYWORDS = [
    "ижс", "дом", "частный", "строительство", "участок",
    "уведомление", "этаж", "высота", "регистрация",
    "земля", "купить", "ипотека", "кредит", "гпзу", "снос"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приветствие и кнопка 'Начать консультацию'."""
    user_id = update.effective_user.id
    context.user_data[user_id] = {}

    await update.message.reply_text(
        "👋 Здравствуйте! Я консультант по индивидуальному жилищному строительству (ИЖС).\n\n"
        "📌 **Как я работаю:**\n"
        "• Нажмите 'Начать консультацию' — я задам 4 вопроса и дам пошаговую инструкцию.\n"
        "• Если хотите задать свой вопрос — напишите его в чат.\n"
        "• Если вы в диалоге и хотите задать вопрос — напишите /cancel, затем вопрос.\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🏗️ Начать консультацию")]
        ], resize_keyboard=True)
    )
    return SELECTING_LAND


async def start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки 'Начать консультацию'"""
    return await start(update, context)


async def land_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает первый вопрос."""
    user_id = update.effective_user.id
    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    await update.message.reply_text(
        "📌 Вопрос 1 из 4\n\n"
        "Есть ли у вас земельный участок?\n\n"
        "ℹ️ Хотите задать свой вопрос? Напишите /cancel, затем вопрос.",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✅ Да, есть")],
            [KeyboardButton("❌ Нет, пока нет")]
        ], resize_keyboard=True)
    )
    return SELECTING_LAND

async def land_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответ на первый вопрос."""
    user_id = update.effective_user.id
    answer = update.message.text

    if "Да, есть" in answer:
        context.user_data[user_id]['land'] = "Да, есть"
        await update.message.reply_text(
            "📌 Вопрос 2 из 4\n\n"
            "Подходит ли вид использования вашего участка под строительство ИЖС?\n\n"
            "Подходящие ВРИ: ИЖС (2.1), ЛПХ (2.2), блокированная застройка (2.3)",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, подходит")],
                [KeyboardButton("❌ Нет, не подходит")],
                [KeyboardButton("🤷 Не знаю")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Нет, пока нет" in answer:
        context.user_data[user_id]['land'] = "Нет, пока нет"
        answer_text = await generate_no_land_answer()
        await update.message.reply_text(answer_text)
        await update.message.reply_text(
            "📌 Если у вас есть ещё вопросы, просто напишите их — я отвечу!\n\n"
            "Или отправьте /start, чтобы начать заново.",
            reply_markup=None
        )
        return ConversationHandler.END

    # Если ответ не распознан
    await update.message.reply_text(
        "Пожалуйста, выберите один из вариантов:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✅ Да, есть")],
            [KeyboardButton("❌ Нет, пока нет")]
        ], resize_keyboard=True)
    )
    return SELECTING_LAND

async def vri_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответ на второй вопрос (ВРИ)"""
    user_id = update.effective_user.id
    answer = update.message.text

    context.user_data[user_id]['vri'] = answer

    if "Подробнее про УРВИ" in answer or "ℹ️ Подробнее про УРВИ" in answer:
        urvi_prompt = load_prompt("urvi")
        if urvi_prompt:
            answer_text = ask_gigachat("объясни процедуру УРВИ", urvi_prompt)
            answer_text = clean_response(answer_text)
        else:
            answer_text = "📌 Для получения подробной информации об УРВИ обратитесь в МФЦ."

        await update.message.reply_text(
            answer_text,
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("➡️ Продолжить")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Продолжить" in answer or "➡️ Продолжить" in answer:
        await update.message.reply_text(
            "📌 Вопрос 3 из 4\n\n"
            "Есть ли у вас готовый проект будущего дома?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, есть")],
                [KeyboardButton("❌ Нет, ищу проект")]
            ], resize_keyboard=True)
        )
        return SELECTING_PROJECT

    if "Продолжить без изменения ВРИ" in answer or "➡️ Продолжить без изменения ВРИ" in answer:
        await update.message.reply_text(
            "📌 Вопрос 3 из 4\n\n"
            "Есть ли у вас готовый проект будущего дома?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, есть")],
                [KeyboardButton("❌ Нет, ищу проект")]
            ], resize_keyboard=True)
        )
        return SELECTING_PROJECT

    if "Назад к вопросам" in answer or "🔙 Назад к вопросам" in answer:
        await update.message.reply_text(
            "📌 Вопрос 2 из 4\n\n"
            "Подходит ли вид использования вашего участка под строительство ИЖС?\n\n"
            "Подходящие ВРИ: ИЖС (2.1), ЛПХ (2.2), блокированная застройка (2.3)",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, подходит")],
                [KeyboardButton("❌ Нет, не подходит")],
                [KeyboardButton("🤷 Не знаю")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Написать другой ВРИ" in answer or "🔙 Написать другой ВРИ" in answer:
        await update.message.reply_text(
            "✏️ Напишите ВРИ вашего участка (например: ИЖС, ЛПХ, СНТ).",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("🔙 Назад к вопросам")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Нет, не подходит" in answer:
        await update.message.reply_text(
            "⚠️ Если ваш ВРИ не подходит под ИЖС, вы можете изменить его через процедуру УРВИ.\n\n"
            "Алгоритм действий:\n"
            "1. Обратиться в Комиссию по землепользованию и застройке\n"
            "2. Провести публичные слушания (30 дней)\n"
            "3. Получить разрешение главы администрации (15 дней)\n"
            "4. Внести изменения в ЕГРН\n\n"
            "📌 Хотите узнать больше про УРВИ или продолжить без изменения ВРИ?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("ℹ️ Подробнее про УРВИ")],
                [KeyboardButton("➡️ Продолжить без изменения ВРИ")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Не знаю" in answer:
        await update.message.reply_text(
            "📌 Чтобы узнать точный ВРИ вашего участка:\n"
            "1. Закажите выписку из ЕГРН на Госуслугах\n"
            "2. Обратитесь в МФЦ\n"
            "3. Посмотрите на публичной кадастровой карте\n\n"
            "Когда узнаете ВРИ, напишите его мне (например: 'ИЖС', 'ЛПХ', 'СНТ').\n\n"
            "Или нажмите кнопку, чтобы вернуться:",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("🔙 Назад к вопросам")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI

    if "Да, подходит" in answer:
        await update.message.reply_text(
            "✅ Отлично! Ваш ВРИ подходит для строительства ИЖС.\n\n"
            "📌 Вопрос 3 из 4\n\n"
            "Есть ли у вас готовый проект будущего дома?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, есть")],
                [KeyboardButton("❌ Нет, ищу проект")]
            ], resize_keyboard=True)
        )
        return SELECTING_PROJECT

    vri_text = answer.lower()
    suitable_vri = ["ижс", "лпх", "личное подсобное", "блокированная", "2.1", "2.2", "2.3"]

    if any(word in vri_text for word in suitable_vri):
        await update.message.reply_text(
            "✅ Отлично! Ваш ВРИ подходит для строительства ИЖС.\n\n"
            "📌 Вопрос 3 из 4\n\n"
            "Есть ли у вас готовый проект будущего дома?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, есть")],
                [KeyboardButton("❌ Нет, ищу проект")]
            ], resize_keyboard=True)
        )
        return SELECTING_PROJECT

    else:
        await update.message.reply_text(
            "⚠️ ВРИ, который вы указали, не подходит для строительства ИЖС.\n\n"
            "Вы можете:\n"
            "1️⃣ Изменить ВРИ через процедуру УРВИ\n"
            "2️⃣ Если вы ошиблись — напишите правильный ВРИ (например: ИЖС, ЛПХ)",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("ℹ️ Подробнее про УРВИ")],
                [KeyboardButton("🔙 Написать другой ВРИ")]
            ], resize_keyboard=True)
        )
        return SELECTING_VRI


async def project_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответ на третий вопрос (проект)"""
    user_id = update.effective_user.id
    answer = update.message.text

    context.user_data[user_id]['project'] = answer

    if "Проект найден, продолжаем" in answer or "✅ Проект найден, продолжаем!" in answer:
        await update.message.reply_text(
            "✅ Спасибо! Последний вопрос:\n\n"
            "🏚️ Планируется ли снос существующего дома на участке?",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Да, планируется снос")],
                [KeyboardButton("❌ Нет, строю с нуля")]
            ], resize_keyboard=True)
        )
        return SELECTING_DEMOLITION

    if "Нет, ищу проект" in answer:
        await update.message.reply_text(
            "🏠 Где посмотреть готовые проекты домов:\n"
            "• ДОМ.РФ — https://дом.рф/проекты\n"
            "• Минстрой РФ — каталог проектов повторного применения\n"
            "• Архитектурные бюро — через Госуслуги\n\n"
            "Найдите подходящий проект и возвращайтесь!",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("✅ Проект найден, продолжаем!")]
            ], resize_keyboard=True)
        )
        return SELECTING_PROJECT

    await update.message.reply_text(
        "✅ Спасибо! Последний вопрос:\n\n"
        "🏚️ Планируется ли снос существующего дома на участке?",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✅ Да, планируется снос")],
            [KeyboardButton("❌ Нет, строю с нуля")]
        ], resize_keyboard=True)
    )
    return SELECTING_DEMOLITION


async def demolition_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает четвёртый вопрос (снос) и генерирует финальный ответ"""
    user_id = update.effective_user.id
    answer = update.message.text

    context.user_data[user_id]['demolition'] = answer
    await update.message.reply_text("✅ Принято! Сейчас я подготовлю для вас ответ...", reply_markup=None)

    try:
        logger.info(f"Начинаю генерацию ответа для пользователя {user_id}")
        logger.info(f"Данные пользователя: {context.user_data[user_id]}")

        answer = await generate_instruction_from_codex(
            context.user_data[user_id],
            demolition=context.user_data[user_id].get('demolition', '')
        )

        logger.info(f"Ответ сгенерирован, длина: {len(answer)} символов")

        # ✅ РАЗБИВАЕМ НА ЧАСТИ, ЕСЛИ ДЛИННЫЙ
        if len(answer) > 4000:
            parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode="Markdown")
        else:
            await update.message.reply_text(answer, parse_mode="Markdown")

        await update.message.reply_text(
            "📌 Если у вас есть ещё вопросы, просто напишите их — я отвечу!\n\n"
            "Или отправьте /start, чтобы начать заново.",
            reply_markup=None
        )
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            f"❌ Произошла ошибка при генерации ответа: {str(e)}\n\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            reply_markup=None
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прерывает диалог"""
    await update.message.reply_text(
        "❌ Диалог прерван.\n\n"
        "Теперь вы можете задать любой вопрос в чат, и я отвечу!\n"
        "Или отправьте /start, чтобы начать консультацию заново."
    )
    return ConversationHandler.END


async def free_question(update: Update, context: ContextTypes.DEFAULT_TYPE)  -> None:
    """Обрабатывает свободные вопросы пользователя"""
    question = update.message.text.lower()
    if question.startswith('/'):
        return

    keywords = ["ижс", "дом", "частный", "строительство", "участок", "уведомление",
                "этаж", "высота", "регистрация", "земля", "купить", "ипотека", "кредит", "гпзу", "снос"]

    if not any(word in question for word in keywords):
        await update.message.reply_text(
            "🏠 Я специализируюсь на вопросах индивидуального жилищного строительства (ИЖС).\n\n"
            "Нажмите 'Начать консультацию' для пошаговой инструкции."
        )
        return

    await update.message.reply_text("🔍 Ищу информацию по ИЖС...")
    try:
        articles = find_articles(question, n=7)
        context_text = "\n\n---\n\n".join(articles)
        prompt = f"""Ты — помощник по ИЖС. На основе выдержек из законов дай ответ на вопрос.

Вопрос: {question}

Выдержки из законов:
{context_text}

Ответь понятно и по делу. Если точного ответа нет — честно скажи об этом. Ссылайся на статьи."""
        answer = ask_gigachat(question, prompt)
        answer = answer.replace("разрешение на строительство", "уведомление о планируемом строительстве")
        answer = answer.replace("разрешение", "уведомление")
        answer = answer.replace("ввод в эксплуатацию", "уведомление об окончании строительства")
        answer = answer.replace("Разрешение", "Уведомление")
        answer = clean_response(answer)
        if len(answer) > 4000:
            answer = answer[:3997] + "..."
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}\n\nПопробуйте переформулировать вопрос.")