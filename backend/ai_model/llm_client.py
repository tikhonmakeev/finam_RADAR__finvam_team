"""
Клиент для взаимодействия с OpenAI API.
"""
import json
import logging
import os
import asyncio
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    """Клиент для работы с OpenAI API."""
    
    def __init__(self):
        """Инициализация клиента OpenAI."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        logger.info(f"Инициализирован клиент OpenAI с моделью: {self.model}")

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: str = None, 
        **kwargs
    ) -> Optional[str]:
        """
        Генерация ответа с использованием выбранного провайдера
        
        Args:
            prompt: Текст промпта
            system_prompt: Дополнительный системный промпт
            **kwargs: Дополнительные параметры для API
            
        Returns:
            Сгенерированный текст или None в случае ошибки
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 1000),
                top_p=kwargs.get('top_p', 0.9),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                presence_penalty=kwargs.get('presence_penalty', 0.0),
                stop=kwargs.get('stop', None)
            )
            
            if response and response.choices:
                return response.choices[0].message.content.strip()
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI API: {str(e)}", exc_info=True)
            return None

# Создаем глобальный экземпляр для удобства использования
llm_client = LLMClient()