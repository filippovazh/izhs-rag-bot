import pickle
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import config

logger = logging.getLogger(__name__)

_model = None
_client = None
_collection = None
_chunks = None


def get_model():
    """Загружает модель эмбеддингов с кешированием."""
    global _model
    if _model is None:
        logger.info(f"Загрузка модели: {config.MODEL_NAME}")
        _model = SentenceTransformer(config.MODEL_NAME)
    return _model


def get_collection():
    """Подключается к векторной БД с кешированием."""
    global _client, _collection
    if _collection is None:
        logger.info(f"Подключение к БД: {config.DB_PATH}")
        _client = chromadb.PersistentClient(path=config.DB_PATH)
        _collection = _client.get_collection(name=config.COLLECTION_NAME)
        logger.info("Подключение к БД установлено")
    return _collection


def get_chunks():
    """Загружает чанки с кешированием."""
    global _chunks
    if _chunks is None:
        chunks_path = Path(config.CHUNKS_PATH)
        if not chunks_path.exists():
            logger.error(f"Файл чанков не найден: {chunks_path}")
            return []
        with open(chunks_path, "rb") as f:
            _chunks = pickle.load(f)
        logger.info(f"Загружено {len(_chunks)} чанков")
    return _chunks


@lru_cache(maxsize=100)
def encode_text(question: str) -> List[float]:
    """
    Кодирует текст в вектор эмбеддинга.
    Использует lru_cache для кеширования повторяющихся запросов.
    """
    model = get_model()
    return model.encode([question]).tolist()[0]


def find_articles(
        question: str,
        n: int = 5,
        priority_source: Optional[str] = None
) -> List[str]:
    """
    Находит релевантные чанки законов с приоритетным источником.

    Args:
        question: Вопрос пользователя
        n: Количество чанков для возврата
        priority_source: Название источника с приоритетом

    Returns:
        Список текстов чанков
    """
    start_time = time.time()

    if priority_source is None:
        priority_source = config.PRIORITY_SOURCE
    try:
        collection = get_collection()
        vec = [encode_text(question)]

        priority_results = collection.query(
            query_embeddings=vec,
            n_results=n,
            where={"source": priority_source} if priority_source else None
        )
        priority_docs = priority_results.get('documents', [[]])[0]

        if len(priority_docs) < n:
            remaining = n - len(priority_docs)
            general_results = collection.query(
                query_embeddings=vec,
                n_results=remaining * 2 + 5
            )
            general_docs = general_results.get('documents', [[]])[0]

            seen = set(priority_docs)
            for doc in general_docs:
                if doc not in seen and len(priority_docs) < n:
                    priority_docs.append(doc)
                    seen.add(doc)

        result = priority_docs[:n]
        elapsed = time.time() - start_time
        logger.info(f"Поиск занял {elapsed:.3f}с, найдено {len(result)} чанков")

        if not result:
            logger.warning("Поиск не вернул ни одного чанка")
            return []

        return result

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return []


def get_chunks_metadata() -> Dict:
    """Возвращает метаданные о чанках."""
    try:
        chunks = get_chunks()
        if not chunks:
            return {"total": 0, "avg_length": 0}
        return {
            "total": len(chunks),
            "avg_length": round(sum(len(c) for c in chunks) / len(chunks), 2)
        }
    except Exception as e:
        logger.error(f"Ошибка получения метаданных: {e}")
        return {"total": 0, "avg_length": 0}


def clear_cache():
    """Очищает кеш эмбеддингов."""
    encode_text.cache_clear()
    logger.info("Кеш эмбеддингов очищен")