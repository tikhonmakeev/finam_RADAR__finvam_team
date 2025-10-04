import logging
from pathlib import Path
from backend.ai_model.llm_client import LocalLLMClient
from backend.ai_model.prompts.prompt_style_news import SYSTEM_PROMPT as NEWS_STYLE_PROMPT

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

# Инициализация клиента языковой модели
try:
    llm = LocalLLMClient()
    logger.info("Клиент языковой модели успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации клиента языковой модели: {str(e)}")
    raise

# Максимальная длина текста для возврата в случае ошибки
MAX_FALLBACK_LENGTH = 400


def summarize_text(text: str, max_summary_length: int = 512) -> str:
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
        # Отправляем запрос к языковой модели с предустановленным системным промптом
        summary = llm.chat(
            prompt=text,  # Сам текст новости как пользовательский промпт
            system=NEWS_STYLE_PROMPT,  # Используем загруженный системный промпт
            max_tokens=max_summary_length,
            temperature=0.3  # Низкая температура для более детерминированного вывода
        )
        
        # Удаляем лишние пробелы и переносы строк
        summary = summary.strip()
        
        # Логируем длину сгенерированного саммари
        logger.debug(f"Сгенерировано саммари длиной {len(summary)} символов")
        
        return summary
        
    except Exception as e:
        # В случае ошибки логируем и возвращаем усеченный оригинальный текст
        logger.error(f"Ошибка при генерации саммари: {str(e)}")
        
        # Возвращаем усеченный текст, разбивая по последнему пробелу перед лимитом
        text = text.strip()
        if len(text) > MAX_FALLBACK_LENGTH:
            return text[:MAX_FALLBACK_LENGTH].rsplit(' ', 1)[0] + '...'
        return text