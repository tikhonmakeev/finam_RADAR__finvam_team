import os
import logging
import httpx
from backend.ai_model.prompts.prompt_comparison import SYSTEM_PROMPT as PROMPT_TEMPLATE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL локальной LLM (например, Ollama или vLLM)
LLM_URL = os.getenv("LLM_URL", "http://localhost:8001/v1/chat/completions")

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
        httpx.RequestError: При ошибке HTTP-запроса
    """
    prompt = PROMPT_TEMPLATE.format(
        news1=news1.strip(),
        news2=news2.strip()
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                LLM_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "model": "qwen2.5:7b",
                    "messages": [
                        {"role": "system", "content": "Ты эксперт по анализу новостей."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 10  # Уменьшаем, так как ответ теперь короче
                }
            )
            response.raise_for_status()
            
            data = response.json()
            output = data["choices"][0]["message"]["content"].strip().lower()
            
            if output == 'True':
                return True
            elif output == 'False':
                return False
            else:
                logger.warning(f"Неожиданный ответ от модели: '{output}'. Ожидалось 'Да' или 'Нет'.")
                # В случае неожиданного ответа считаем, что новости разные
                return False
                
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка HTTP при запросе к LLM: {e}")
        raise
    except (KeyError, IndexError) as e:
        logger.error(f"Не удалось разобрать ответ от модели: {e}")
        raise ValueError("Неверный формат ответа от модели") from e
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        raise

