import os
import logging
import httpx
from openai import OpenAI
from backend.ai_model.prompts.prompt_comparison import SYSTEM_PROMPT_COMPARISON as PROMPT_TEMPLATE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки OpenRouter
OPENROUTER_API_KEY = os.getenv("MARSH_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

# Инициализация клиента OpenRouter
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

async def compare_news(news1: str, news2: str) -> bool:
    """
    Сравнение двух новостей через LLM и prompt_comparison.
    
    Args:
        news1: Первый текст новости
        news2: Второй текст новости
        
    Returns:
        bool: True если новости об одном и том же событии, иначе False
        
    Raises:
        ValueError: Если не удалось разобрать ответ от модели
        Exception: При других ошибках
    """
    prompt = PROMPT_TEMPLATE.format(
        news1=news1.strip(),
        news2=news2.strip()
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу новостей."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=10,
            extra_headers={
                "HTTP-Referer": "https://github.com/tikhonmakeev/finam_RADAR__finvam_team",
                "X-Title": "Finam RADAR"
            }
        )
        
        output = response.choices[0].message.content.strip().lower()
        
        if output == 'true':
            return True
        elif output == 'false':
            return False
        else:
            logger.warning(f"Unexpected model output: {output}")
            return False
                
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenRouter: {str(e)}")
        raise

