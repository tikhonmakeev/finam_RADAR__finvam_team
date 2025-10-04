import logging
from backend.ai_model.llm_client import LocalLLMClient
from backend.ai_model.prompts.prompt_tagger import SYSTEM_PROMPT_TAGGER

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация клиента языковой модели
try:
    llm = LocalLLMClient()
    logger.info("Клиент языковой модели для теггера успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации клиента языковой модели: {str(e)}")
    raise

class Tagger:
    """Класс для классификации новостей по тегам.
    
    Использует языковую модель для определения наиболее подходящего тега
    из предопределенного списка на основе содержания новости.
    """
    
    def __init__(self):
        logger.info("Tagger инициализирован")

    def tag(self, news_text: str) -> str:
        """Классифицирует новость по тегу.
        
        Args:
            news_text (str): Текст новости для классификации
            
        Returns:
            str: Название тега или 'None', если подходящий тег не найден
            
        Примеры:
            text = "Компания Apple представила новый чип M3"
            tag = tagger.tag(text)  # Вернёт "Информационные технологии"
        """
        if not news_text or not isinstance(news_text, str):
            logger.warning("Получен пустой или неверный текст для классификации")
            return "None"
            
        try:
            # Отправляем запрос к языковой модели с предустановленным системным промптом
            tag = llm.chat(
                prompt=news_text,  # Текст новости как пользовательский промпт
                system=SYSTEM_PROMPT_TAGGER,  # Используем загруженный системный промпт
                max_tokens=20,  # Нужно немного токенов, так как ответ короткий
                temperature=0.1  # Низкая температура для более детерминированного вывода
            )
            
            # Очищаем и форматируем ответ
            tag = tag.strip().strip('"\'')
            
            # Проверяем, что тег не пустой
            if not tag:
                return "None"
                
            logger.debug(f"Определён тег: {tag}")
            return tag
            
        except Exception as e:
            logger.error(f"Ошибка при классификации новости: {str(e)}")
            return "None"
