"""
Text utilities for the IZhS RAG Bot.

Provides functions for:
- Loading prompts from files
- Cleaning and formatting responses
"""

import re
from typing import Optional
from pathlib import Path
from src.config import Config

# Кеш для промптов
_prompt_cache: dict = {}
PROMPT_PATH = Path(Config.PROMPT_PATH) if Config.PROMPT_PATH else None


class PromptType:
    """Константы типов промптов"""
    INSTRUCTION = "instruction"
    URVI = "urvi"


def load_prompt(prompt_type: str = PromptType.INSTRUCTION) -> Optional[str]:
    """
    Загружает промпт из файла по секции.

    Args:
        prompt_type: Тип промпта ("instruction" или "urvi")

    Returns:
        Текст промпта или None если не найден

    Example:
        >>> prompt = load_prompt("instruction")
        >>> print(prompt[:50])
        "Ты — консультант по ИЖС..."
    """
    # Проверяем кеш
    if prompt_type in _prompt_cache:
        return _prompt_cache[prompt_type]

    # Проверяем путь
    if not PROMPT_PATH or not PROMPT_PATH.exists():
        print(f"❌ Файл prompt.txt не найден по пути: {PROMPT_PATH}")
        return None

    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        if not content:
            print("❌ prompt.txt пуст")
            return None

        # Определяем секцию
        section_start = f"[PROMPT_{prompt_type.upper()}]"
        section_end = f"[/PROMPT_{prompt_type.upper()}]"

        pattern = rf'{section_start}(.*?){section_end}'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            result = match.group(1).strip()
            _prompt_cache[prompt_type] = result
            return result
        else:
            print(f"⚠️ Секция {section_start} не найдена в prompt.txt")
            return None

    except Exception as e:
        print(f"❌ Ошибка загрузки промпта: {e}")
        return None


def clean_response(text: str) -> str:
    """
    Очищает текст ответа от лишних символов.

    Сохраняет Markdown разметку (**жирный**, __подчеркнутый__).
    Убирает:
    - Множественные заголовки (### и более)
    - Множественные переносы строк
    - Множественные пробелы

    Args:
        text: Исходный текст

    Returns:
        Очищенный текст

    Example:
        >>> clean_response("### Заголовок\\n\\n\\nТекст")
        "### Заголовок\\n\\nТекст"
    """
    if not text:
        return ""

    # Убираем множественные # (оставляем ## и #)
    text = re.sub(r'#{3,}\s*', '', text)

    # Убираем множественные переносы (оставляем максимум 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Убираем множественные пробелы
    text = re.sub(r' {2,}', ' ', text)

    # Убираем пробелы в конце строк
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    return text.strip()


def split_long_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Разбивает длинное сообщение на части для Telegram.

    Args:
        text: Текст для разбиения
        max_length: Максимальная длина одной части

    Returns:
        Список частей сообщения
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    for paragraph in text.split('\n\n'):
        if len(current_part) + len(paragraph) + 2 <= max_length:
            current_part += paragraph + '\n\n'
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = paragraph + '\n\n'

    if current_part:
        parts.append(current_part.strip())

    return parts


def truncate_text(text: str, max_length: int = 4096) -> str:
    """
    Обрезает текст до максимальной длины, добавляя '...'

    Args:
        text: Исходный текст
        max_length: Максимальная длина

    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."