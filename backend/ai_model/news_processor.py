"""
Модуль для обработки новостей через цепочку промптов с интеграцией RAG.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .llm_client import LocalLLMClient
from .rag_utils import build_rag_context, assemble_prompt_with_context
from .prompts import (
    prompt_style_news as style_prompt,
    prompt_tagger as tagger_prompt,
    prompt_market_impact as market_impact_prompt,
    prompt_comparison as comparison_prompt,
    prompt_update_summary as update_summary_prompt
)
import asyncio
from functools import wraps

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timeout(seconds=30):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Функция {func.__name__} превысила таймаут {seconds} секунд")
                return None
        return wrapper
    return decorator

class NewsProcessor:
    """Класс для обработки новостей через цепочку промптов с RAG."""
    
    def __init__(self, llm_client: Optional[LocalLLMClient] = None):
        """Инициализация процессора новостей.
        
        Args:
            llm_client: Клиент для работы с LLM. Если не указан, будет создан новый.
        """
        self.llm = llm_client or LocalLLMClient()
        self.news_history = []
    
    def _call_llm(self, system_prompt: str, user_prompt: str, context: str = "") -> str:
        """Вызов LLM с промптом и контекстом.
        
        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            context: Дополнительный контекст для RAG
            
        Returns:
            Ответ от LLM
        """
        # Собираем финальный промпт с контекстом
        if context:
            full_prompt = assemble_prompt_with_context(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                retrieved=[{"text": context, "metadata": {}}]
            )
        else:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            response = self.llm.chat(
                prompt=full_prompt,
                system=system_prompt,
                max_tokens=1024,
                temperature=0.3
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Ошибка при вызове LLM: {e}")
            return ""
    
    def process_style(self, news_text: str) -> str:
        """Обработка стиля новости."""
        logger.info("Применяем нормализацию стиля...")
        return self._call_llm(
            system_prompt=style_prompt.SYSTEM_PROMPT,
            user_prompt=news_text
        ) or news_text  # Возвращаем оригинальный текст в случае ошибки
    
    def process_tags(self, news_text: str) -> List[str]:
        """Извлечение тегов из новости."""
        logger.info("Извлекаем теги...")
        result = self._call_llm(
            system_prompt=tagger_prompt.SYSTEM_PROMPT_TAGGER,
            user_prompt=news_text
        )
        # Парсим ответ в виде списка тегов
        try:
            return [tag.strip() for tag in result.split(",") if tag.strip()]
        except:
            return []
    
    def analyze_market_impact(self, news_text: str) -> Dict[str, Any]:
        """Анализ рыночного влияния новости."""
        logger.info("Анализируем рыночное влияние...")
        result = self._call_llm(
            system_prompt=market_impact_prompt.SYSTEM_PROMPT,
            user_prompt=news_text
        )
        # Парсим JSON-ответ
        try:
            return json.loads(result)
        except:
            return {"impact_level": "unknown", "affected_sectors": []}
    
    def compare_with_previous(self, current_news: str, previous_news: List[str]) -> List[Dict[str, Any]]:
        """Сравнение новости с предыдущими."""
        if not previous_news:
            return []
            
        logger.info(f"Сравниваем с {len(previous_news)} предыдущими новостями...")
        results = []
        
        for i, prev_news in enumerate(previous_news):
            comparison_result = self._call_llm(
                system_prompt=comparison_prompt.SYSTEM_PROMPT,
                user_prompt=f"Текст 1: {prev_news}\n\nТекст 2: {current_news}"
            )
            results.append({
                "previous_news_index": i,
                "is_same_event": "true" in comparison_result.lower(),
                "analysis": comparison_result
            })
        
        return results
    
    def update_summary(self, existing_summary: str, new_info: str) -> str:
        """Обновление сводки на основе новой информации."""
        logger.info("Обновляем сводку...")
        return self._call_llm(
            system_prompt=update_summary_prompt.SYSTEM_PROMPT,
            user_prompt=f"Существующая сводка: {existing_summary}\n\nНовая информация: {new_info}"
        ) or existing_summary

    @timeout(30)
    def process_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка одной новости через всю цепочку промптов."""
        logger.info(f"\n{'='*80}")
        logger.info(f"ОБРАБОТКА НОВОСТИ: {news_item.get('title', 'Без названия')}")
        logger.info("-" * 80)
        
        result = {
            'original_news': news_item,
            'timestamp': datetime.now().isoformat(),
            'processing_steps': []
        }
        
        # 1. Нормализация стиля
        normalized_text = self.process_style(news_item.get('text', ''))
        result['style_normalized'] = normalized_text
        
        # 2. Извлечение тегов
        tags = self.process_tags(normalized_text)
        result['tags'] = tags
        
        # 3. Анализ рыночного влияния
        market_impact = self.analyze_market_impact(normalized_text)
        result['market_impact'] = market_impact
        
        # 4. Сравнение с предыдущими новостями
        previous_news = [item['style_normalized'] for item in self.news_history[-3:]]
        comparison_results = self.compare_with_previous(normalized_text, previous_news)
        result['comparison'] = comparison_results
        
        # 5. Обновление сводки
        last_summary = self.news_history[-1]['summary'] if self.news_history else ""
        updated_summary = self.update_summary(last_summary, normalized_text)
        result['summary'] = updated_summary
        
        # Сохраняем в историю
        self.news_history.append(result)
        
        return result

# Синглтон для использования в других модулях
news_processor = NewsProcessor()

@timeout(60)
def process_news_batch(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Обработка пакета новостей."""
    processor = NewsProcessor()
    results = []
    
    for item in news_items:
        try:
            result = processor.process_news_item(item)
            results.append(result)
        except Exception as e:
            logger.error(f"Ошибка при обработке новости: {e}")
    
    return results
