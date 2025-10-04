from typing import List, Tuple, Any, Dict, Optional
import re
import logging
import numpy as np
from ai_model.embedder import Embedder

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация эмбеддера
try:
    embedder = Embedder()
    logger.info("Эмбеддер успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации эмбеддера: {str(e)}")
    raise


def chunk_text(text: str, max_words: int = 250) -> List[str]:
    """Разделяет текст на чанки по предложениям с ограничением по количеству слов.
    
    Args:
        text (str): Входной текст для разделения на чанки
        max_words (int, optional): Максимальное количество слов в одном чанке. По умолчанию 250.
        
    Returns:
        List[str]: Список текстовых чанков
        
    Пример:
        text = "Первое предложение. Второе предложение. Третье предложение."
        chunks = chunk_text(text, max_words=5)
        for chunk in chunks:
             print(f"Чанк: {chunk}")
    """
    if not text or not isinstance(text, str):
        logger.warning("Получен пустой или неверный текст для чанкинга")
        return []
    
    # Разделяем текст на предложения
    sents = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sents:
        word_count = len(sentence.split())
        # Если добавление нового предложения превысит лимит слов, сохраняем текущий чанк
        if current_length + word_count > max_words and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = word_count
        else:
            current_chunk.append(sentence)
            current_length += word_count
    
    # Добавляем последний чанк, если он не пустой
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    logger.debug(f"Текст разделен на {len(chunks)} чанков")
    return chunks


def build_rag_context(text: str, top_k: Optional[int] = None) -> List[Tuple[str, np.ndarray]]:
    """Преобразует текст в чанки с соответствующими эмбеддингами.
    
    Args:
        text (str): Входной текст для обработки
        top_k (Optional[int]): Количество возвращаемых чанков (пока не используется, оставлено для обратной совместимости)
        
    Returns:
        List[Tuple[str, np.ndarray]]: Список кортежей (текст_чанка, эмбеддинг)
        
    Примечание:
        Параметр top_k оставлен для обратной совместимости, но в текущей реализации не используется,
        так как возвращаются все сгенерированные чанки.
    """
    if not text:
        return []
        
    chunks = chunk_text(text)
    if not chunks:
        return []
        
    try:
        embs = embedder.embed(chunks)
        return list(zip(chunks, embs))
    except Exception as e:
        logger.error(f"Ошибка при создании эмбеддингов: {str(e)}")
        return []


def assemble_prompt_with_context(
    system_prompt: str, 
    user_prompt: str, 
    retrieved: List[Dict[str, Any]]
) -> str:
    """Собирает итоговый промпт с контекстом из RAG.
    
    Args:
        system_prompt (str): Системные инструкции/контекст
        user_prompt (str): Запрос пользователя
        retrieved (List[Dict[str, Any]]): Список извлеченных контекстных элементов с метаданными
        
    Returns:
        str: Отформатированная строка промпта с контекстом
        
    Пример возвращаемого значения:
        [системный промпт]
        
        --- Context snippets ---
        [источник] Текст первого релевантного фрагмента...
        
        [источник] Текст второго релевантного фрагмента...
        
        [промпт пользователя]
    """
    if not retrieved:
        logger.warning("Не переданы извлеченные данные для сборки промпта")
        return f"{system_prompt}\n\n{user_prompt}"
    
    # Формируем заголовок для контекстных фрагментов
    ctx = "\n\n--- Контекстные фрагменты ---\n"
    
    # Добавляем каждый фрагмент контекста
    for i, r in enumerate(retrieved, 1):
        meta = r.get('meta', {})
        snippet = meta.get('chunk') or meta.get('text', '')
        src = meta.get('source', 'неизвестный источник')
        score = r.get('score', 0.0)
        
        # Форматируем фрагмент с учетом доступных метаданных
        ctx += f"[{i}] Источник: {src} (сходство: {score:.3f})\n{snippet}\n\n"
    
    # Собираем итоговый промпт
    final_prompt = f"{system_prompt}{ctx}\n\n{user_prompt}"
    
    # Логируем длину сгенерированного промпта
    logger.debug(f"Сгенерирован промпт длиной {len(final_prompt)} символов")
    
    return final_prompt