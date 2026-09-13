import logging
import os
import pickle
import shutil

import chromadb
import docx
from sentence_transformers import SentenceTransformer

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    doc_path = os.path.join(os.path.dirname(config.DATA_PATH), "законы_объединенные.docx")
    if not os.path.exists(doc_path):
        doc_path = "законы_объединенные.docx"

    logger.info(f"Читаю документ: {doc_path}")
    doc = docx.Document(doc_path)
    text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

    chunk_size = config.CHUNK_SIZE
    overlap = config.OVERLAP
    step = chunk_size - overlap

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), step)]
    chunks = [c for c in chunks if len(c) > 100]

    logger.info(f"Получено {len(chunks)} чанков")

    logger.info(f"Загружаю модель: {config.MODEL_NAME}")
    model = SentenceTransformer(config.MODEL_NAME)
    embeddings = model.encode(chunks, batch_size=config.EMBEDDING_BATCH_SIZE)

    if os.path.exists(config.DB_PATH):
        shutil.rmtree(config.DB_PATH)
        logger.info(f"Старая база удалена: {config.DB_PATH}")
    client = chromadb.PersistentClient(path=config.DB_PATH)
    collection = client.get_or_create_collection(name=config.COLLECTION_NAME)

    for i in range(0, len(chunks), 100):
        batch = chunks[i:i + 100]
        collection.add(
            documents=batch,
            embeddings=[e.tolist() for e in embeddings[i:i + 100]],
            ids=[str(j) for j in range(i, i + len(batch))],
            metadatas=[{"source": config.PRIORITY_SOURCE} for _ in batch]
        )

    with open(config.CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    logger.info(f"Индексация завершена: {len(chunks)} чанков")
    logger.info(f"БД: {config.DB_PATH}")
    logger.info(f"Чанки: {config.CHUNKS_PATH}")


if __name__ == "__main__":
    main()