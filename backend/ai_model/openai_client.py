"""
Клиент для работы с OpenAI API
"""
import os
import logging
from openai import OpenAI
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info(f"✅ OpenAI client initialized with model: {self.model}")

    async def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> Optional[str]:
        """
        Генерация ответа через OpenAI API
        
        Args:
            prompt: Пользовательский промпт
            system_prompt: Системный промпт
            **kwargs: Дополнительные параметры
            
        Returns:
            Текст ответа или None при ошибке
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 500),
                top_p=kwargs.get('top_p', 0.9),
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return None

    async def generate_json_response(self, prompt: str, system_prompt: str = None) -> Optional[Dict]:
        """
        Генерация JSON ответа (для структурированных данных)
        """
        try:
            # Добавляем инструкцию для JSON формата
            json_system_prompt = f"{system_prompt}\n\nRespond ONLY with valid JSON, no other text."
            
            response = await self.generate_response(prompt, json_system_prompt)
            
            if response:
                import json
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"❌ OpenAI JSON parsing error: {e}")
            return None
