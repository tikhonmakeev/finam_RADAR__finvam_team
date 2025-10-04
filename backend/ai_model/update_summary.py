import logging
from backend.ai_model.llm_client import LocalLLMClient
from backend.ai_model.prompts.prompt_update_summary import SYSTEM_PROMPT as UPDATE_PROMPT
from backend.ai_model.summarizer import summarize_text
from backend.ai_model.compare import compare_news

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация клиента
try:
    llm = LocalLLMClient()
    logger.info("Клиент языковой модели для update_summary успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации клиента языковой модели: {str(e)}")
    raise


async def update_summary(old_summary: str, new_text: str, max_length: int = 512) -> str:
    """
    Обновляет существующее саммари новости, если появилась новая версия той же новости.
    Если это другая новость, создаёт новое саммари.

    Args:
        old_summary (str): предыдущее саммари
        new_text (str): новый текст новости
        max_length (int): ограничение на длину генерации

    Returns:
        str: обновленное или новое саммари
    """

    if not new_text or not isinstance(new_text, str):
        logger.warning("Пустой или некорректный текст для обновления саммари")
        return old_summary

    try:
        # 1. Проверяем — та же ли это новость?
        is_same = await compare_news(old_summary, new_text)
        logger.info(f"Результат сравнения новостей: {is_same}")

        if is_same:
            # 2. Обновляем саммари с помощью модели
            prompt_input = f"Старое саммари: {old_summary}\nНовая новость: {new_text}"
            updated_summary = llm.chat(
                prompt=prompt_input,
                system=UPDATE_PROMPT,
                max_tokens=max_length,
                temperature=0.3
            ).strip()
            logger.info("Саммари обновлено")
            return updated_summary

        else:
            # 3. Если это другая новость → делаем новое саммари
            new_summary = summarize_text(new_text, max_summary_length=max_length)
            logger.info("Сформировано новое саммари, так как новость отличается")
            return new_summary

    except Exception as e:
        logger.error(f"Ошибка при обновлении саммари: {str(e)}")
        return old_summary
