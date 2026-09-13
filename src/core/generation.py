import re
import logging
import asyncio
import base64
from typing import Optional
import urllib3

import requests

from src.config import config
from src.utils.text_utils import clean_response, load_prompt
from src.core.retrieval import find_articles

logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 1. GIGACHAT
def get_gigachat_token() -> Optional[str]:
    if not config.GIGACHAT_CLIENT_ID or not config.GIGACHAT_SECRET:
        logger.warning("Нет credentials GigaChat в .env")
        return None

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_string = f"{config.GIGACHAT_CLIENT_ID}:{config.GIGACHAT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "123e4567-e89b-12d3-a456-426614174000"
    }
    data = {"scope": "GIGACHAT_API_PERS", "grant_type": "client_credentials"}

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10, verify=False)
        if response.status_code == 200:
            logger.info("Токен GigaChat получен")
            return response.json()["access_token"]
        else:
            logger.warning(f"Ошибка получения токена: {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Ошибка соединения с GigaChat: {e}")
        return None


def ask_gigachat(question: str, context: Optional[str] = None) -> Optional[str]:
    token = get_gigachat_token()
    if not token:
        return None

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": context or question}],
        "temperature": config.DEFAULT_TEMPERATURE,
        "max_tokens": config.MAX_TOKENS
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15, verify=False)
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            logger.info(f"GigaChat ответил ({len(result)} символов)")
            return result
        else:
            logger.warning(f" GigaChat ошибка {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        logger.warning(f"GigaChat исключение: {e}")
        return None


def remove_demolition_sections(text: str) -> str:
    lines = []
    skip = False
    for line in text.split('\n'):
        line_lower = line.lower()
        if 'снос' in line_lower and any(w in line_lower for w in ['шаг', 'часть', 'раздел', '1.']):
            skip = True
            continue
        if skip and any(w in line_lower for w in ['строительство', 'новый дом', 'возведение']):
            skip = False
        if not skip and 'снос' not in line_lower:
            lines.append(line)
    result = '\n'.join(lines)
    return re.sub(r'\n{3,}', '\n\n', result)


async def generate_instruction_from_codex(data: dict, demolition: Optional[str] = None) -> str:
    logger.info("Начинаю генерацию инструкции")
    role = "Физическое лицо"
    land = data.get('land', '')
    purpose = data.get('purpose', 'Для проживания')

    try:
        if demolition and "Да" in demolition:
            search_query = "индивидуальное жилищное строительство ИЖС уведомительный порядок снос ст. 55.30"
            demolition_text = "ДА (опиши и снос, и строительство!)"
        else:
            search_query = "индивидуальное жилищное строительство ИЖС уведомительный порядок"
            demolition_text = "НЕТ (ТОЛЬКО строительство нового дома!)"

        articles = find_articles(search_query, n=10)
        if not articles:
            return "Не удалось найти информацию по вашему запросу."

        context = "\n\n---\n\n".join(articles)
        prompt_template = load_prompt()
        if prompt_template is None:
            return "Техническая ошибка: не найден файл prompt.txt"

        prompt = prompt_template.format(
            role=role,
            land=land,
            purpose=purpose,
            demolition=demolition_text,
            context=context
        )

        answer = await asyncio.to_thread(ask_gigachat, "составь пошаговый план для ИЖС", prompt)
        if answer is None:
            return "Не удалось получить ответ от GigaChat. Проверьте настройки."

        if len(answer) < 50:
            logger.warning("Ответ слишком короткий")
            return answer

        if demolition and "Нет" in demolition:
            answer = remove_demolition_sections(answer)

        answer = answer.replace("разрешение на строительство", "уведомление о планируемом строительстве")
        answer = re.sub(r'(?<![а-яА-ЯёЁ])разрешение(?![а-яА-ЯёЁ])', 'уведомление', answer)
        answer = clean_response(answer)

        return answer

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return "Извините, произошла техническая ошибка."


async def generate_no_land_answer() -> str:
    prompt = """Ты — помощник по ИЖС. У пользователя нет участка. 
    Дай практические советы где искать участок для ИЖС и на что обратить внимание."""
    answer = await asyncio.to_thread(ask_gigachat, "совет по покупке участка", prompt)
    if answer is None:
        return "Не удалось получить ответ от GigaChat. Проверьте настройки."
    return clean_response(answer)