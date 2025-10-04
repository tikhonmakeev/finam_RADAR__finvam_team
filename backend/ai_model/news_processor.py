"""
Модуль для обработки новостей через цепочку промптов с интеграцией RAG.
"""
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
from functools import wraps

from .llm_client import llm_client
from .rag_utils import build_rag_context, assemble_prompt_with_context
from .prompts import (
    prompt_style_news as style_prompt,
    prompt_tagger as tagger_prompt,
    prompt_market_impact as market_impact_prompt,
    prompt_comparison as comparison_prompt,
    prompt_update_summary as update_summary_prompt
)

# Настройка логирования
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
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
    
    def __init__(self, llm_client=None):
        """Инициализация процессора новостей.
        
        Args:
            llm_client: Клиент для работы с LLM. Если не указан, будет использован глобальный llm_client.
        """
        from .llm_client import llm_client as global_llm_client
        self.llm = llm_client or global_llm_client
        self.news_history = []
    
    async def _call_llm(self, system_prompt: str, user_prompt: str, context: str = "") -> str:
        """Асинхронный вызов LLM с промптом и контекстом.
        
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
            full_prompt = user_prompt
        
        try:
            response = await self.llm.generate_response(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.3
            )
            return response.strip() if response else ""
        except Exception as e:
            logger.error(f"Ошибка при вызове LLM: {e}", exc_info=True)
            return ""
    
    async def process_style(self, news_text: str) -> str:
        """Обработка стиля новости."""
        logger.info("Применяем нормализацию стиля...")
        result = await self._call_llm(
            system_prompt=style_prompt.SYSTEM_PROMPT,
            user_prompt=news_text
        )
        return result or news_text  # Возвращаем оригинальный текст в случае ошибки
    
    async def process_tags(self, news_text: str) -> List[str]:
        """Извлечение тегов из новости."""
        logger.info("Извлекаем теги...")
        result = await self._call_llm(
            system_prompt=tagger_prompt.SYSTEM_PROMPT_TAGGER,
            user_prompt=news_text
        )
        # Парсим ответ в виде списка тегов
        try:
            return [tag.strip() for tag in result.split(",") if tag.strip()]
        except Exception as e:
            logger.error(f"Ошибка при обработке тегов: {e}")
            return []
    
    async def analyze_market_impact(self, news_text: str) -> Dict[str, Any]:
        """Анализ рыночного влияния новости."""
        logger.info("Анализируем рыночное влияние...")
        result = await self._call_llm(
            system_prompt=market_impact_prompt.SYSTEM_PROMPT_MARKET_IMPACT,
            user_prompt=news_text
        )
        # Парсим JSON-ответ
        try:
            if result and isinstance(result, str):
                return json.loads(result)
            return result or {"impact_level": "unknown", "affected_sectors": []}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON: {e}")
            return {"impact_level": "error", "affected_sectors": [], "error": str(e)}
    
    async def compare_with_previous(self, current_news: str, previous_news: List[str]) -> List[Dict[str, Any]]:
        """Сравнение новости с предыдущими."""
        if not previous_news:
            return []
            
        logger.info(f"Сравниваем с {len(previous_news)} предыдущими новостями...")
        results = []
        
        for i, prev_news in enumerate(previous_news):
            comparison_result = await self._call_llm(
                system_prompt=comparison_prompt.SYSTEM_PROMPT_COMPARISON,
                user_prompt=f"Текст 1: {prev_news}\n\nТекст 2: {current_news}"
            )
            results.append({
                "previous_news_index": i,
                "is_same_event": comparison_result and "true" in comparison_result.lower(),
                "analysis": comparison_result or "Не удалось выполнить сравнение"
            })
        
        return results
    
    async def update_summary(self, existing_summary: str, new_info: str) -> str:
        """Обновление сводки на основе новой информации."""
        logger.info("Обновляем сводку...")
        result = await self._call_llm(
            system_prompt=update_summary_prompt.SYSTEM_PROMPT,
            user_prompt=f"Существующая сводка: {existing_summary}\n\nНовая информация: {new_info}"
        )
        return result or existing_summary

    @timeout(300)  # Увеличиваем таймаут до 5 минут
    async def process_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """Асинхронная обработка одной новости через всю цепочку промптов."""
        logger.info(f"\n{'='*80}")
        logger.info(f"ОБРАБОТКА НОВОСТИ: {news_item.get('title', 'Без названия')}")
        logger.info("-" * 80)
        
        result = {
            'original_news': news_item,
            'timestamp': datetime.now().isoformat(),
            'processing_steps': []
        }
        
        try:
            # 1. Нормализация стиля
            normalized_text = await self.process_style(news_item.get('text', ''))
            result['style_normalized'] = normalized_text
            
            # 2. Извлечение тегов
            tags = await self.process_tags(normalized_text)
            result['tags'] = tags
            
            # 3. Анализ рыночного влияния
            market_impact = await self.analyze_market_impact(normalized_text)
            result['market_impact'] = market_impact
            
            # 4. Сравнение с предыдущими новостями
            previous_news = [item['style_normalized'] for item in self.news_history[-3:]]
            comparison_results = await self.compare_with_previous(normalized_text, previous_news)
            result['comparison'] = comparison_results
            
            # 5. Обновление сводки
            last_summary = self.news_history[-1]['summary'] if self.news_history else ""
            updated_summary = await self.update_summary(last_summary, normalized_text)
            result['summary'] = updated_summary
            
            # Сохраняем в историю
            self.news_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке новости: {e}", exc_info=True)
            result['error'] = str(e)
            return result

# Синглтон для использования в других модулях
news_processor = NewsProcessor()

async def process_news_batch_async(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Асинхронная обработка пакета новостей."""
    processor = NewsProcessor()
    results = []
    
    for item in news_items:
        try:
            result = await processor.process_news_item(item)
            results.append(result)
        except Exception as e:
            logger.error(f"Ошибка при обработке новости: {e}", exc_info=True)
    
    return results

def process_news_batch(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Синхронная обертка для асинхронной обработки пакета новостей."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(process_news_batch_async(news_items))
    
    return results
