import logging
from backend.ai_model.llm_client import LocalLLMClient
from backend.ai_model.prompts.prompt_market_impact import SYSTEM_PROMPT as MARKET_IMPACT_PROMPT

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация LLM клиента
try:
    llm = LocalLLMClient()
    logger.info("Клиент языковой модели для market_impact успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации клиента языковой модели: {str(e)}")
    raise


def analyze_market_impact(text: str, max_length: int = 128) -> bool:
    """
    Прогнозирует реакцию рынка на новость.

    Args:
        text (str): текст новости
        max_length (int): максимальная длина ответа модели

    Returns:
        bool: True — акции вырастут, False — упадут
    """
    if not text or not isinstance(text, str):
        logger.warning("Пустой или некорректный текст для анализа")
        return False

    try:
        response = llm.chat(
            prompt=text,
            system=MARKET_IMPACT_PROMPT,
            max_tokens=max_length,
            temperature=0.2
        )
        result = response.strip()
        logger.debug(f"Результат от модели: {result}")

        if result == "True":
            return True
        elif result == "False":
            return False
        else:
            raise ValueError(f"Модель вернула неожиданный ответ: {result}")

    except Exception as e:
        logger.error(f"Ошибка при анализе market impact: {str(e)}")
        return False
