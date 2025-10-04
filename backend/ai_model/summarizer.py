import logging
from pathlib import Path
from typing import Optional

from .llm_client import llm_client
from .prompts.prompt_style_news import SYSTEM_PROMPT as NEWS_STYLE_PROMPT

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка промптов
PROMPTS_DIR = Path(__file__).parent / 'prompts'

try:
    # Импортируем системный промпт для стиля новостей
    logger.info("Промпт для стиля новостей успешно загружен")
except Exception as e:
    logger.error(f"Не удалось загрузить промпт для стиля новостей: {str(e)}")
    raise

# Используем глобальный экземпляр llm_client

# Максимальная длина текста для возврата в случае ошибки
MAX_FALLBACK_LENGTH = 400


async def summarize_text(text: str, max_summary_length: int = 512) -> Optional[str]:
    """Генерирует краткое саммари входного текста на русском языке.
    
    Использует языковую модель для создания сжатого пересказа основного содержания текста
    в соответствии с заданным стилем новостей. В случае ошибки возвращает усеченную версию 
    исходного текста.
    
    Args:
        text (str): Входной текст для суммаризации
        max_summary_length (int, optional): Максимальная длина саммари в токенах. 
                                          По умолчанию 512.
    
    Returns:
        str: Краткое саммари текста в стиле новостей или усеченный оригинальный текст 
             в случае ошибки.
        
    Примеры:
        text = "Вчера на фондовом рынке произошло значительное падение..."
        summary = summarize_text(text)
        print(summary)
        "Фондовый рынок обвалился на фоне роста инфляционных ожиданий..."
        
    Примечание:
        - Использует предустановленный стиль новостей из prompt_style_news.py
        - Для генерации используется языковая модель с пониженной температурой (0.3)
          для более фактологического вывода
        - В случае ошибки возвращается начало текста (до MAX_FALLBACK_LENGTH символов)
    """
    if not text or not isinstance(text, str):
        logger.warning("Получен пустой или неверный текст для суммаризации")
        return ""
    
    try:
        # Формируем промпт для суммаризации
        prompt = (
            f"Сократи следующий текст до {max_summary_length} токенов, сохраняя ключевые факты и смысл. "
            f"Используй формальный стиль новостей. Текст: {text}"
        )
        
        # Вызываем языковую модель асинхронно
        summary = await llm_client.generate_response(
            prompt=prompt,
            system_prompt=NEWS_STYLE_PROMPT,
            max_tokens=max_summary_length
        )
        
        # Проверяем результат
        if not summary or len(summary.strip()) == 0:
            logger.warning("Получен пустой ответ от языковой модели")
            return text[:MAX_FALLBACK_LENGTH] + "..." if len(text) > MAX_FALLBACK_LENGTH else text
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Ошибка при генерации саммари: {str(e)}", exc_info=True)
        # Возвращаем усеченный оригинальный текст в случае ошибки
        return text[:MAX_FALLBACK_LENGTH] + "..." if len(text) > MAX_FALLBACK_LENGTH else text