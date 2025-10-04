"""
Клиент для работы с OpenRouter API
"""
import os
import logging
from openai import OpenAI
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv('MARSH_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        
        if not self.api_key:
            raise ValueError("MARSH_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/tikhonmakeev/finam_RADAR__finvam_team",
                "X-Title": "Finam Radar"
            }
        )
        logger.info(f"✅ OpenRouter client initialized with model: {self.model}")

    async def generate_response(self, prompt: str, system_prompt: str = None, **kwargs) -> Optional[str]:
        """
        Генерация ответа через OpenRouter API
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
                max_tokens=kwargs.get('max_tokens', 2000),
                top_p=kwargs.get('top_p', 0.9),
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ OpenRouter API error: {e}")
            return None

    async def generate_json_response(self, prompt: str, system_prompt: str = None) -> Optional[Dict]:
        """
        Генерация JSON ответа
        """
        try:
            json_system_prompt = f"{system_prompt}\n\nRespond ONLY with valid JSON, no other text."
            
            response = await self.generate_response(prompt, json_system_prompt)
            
            if response:
                import json
                return json.loads(response)
            return None
            
        except Exception as e:
            logger.error(f"❌ OpenRouter JSON parsing error: {e}")
            return None

    async def get_available_models(self) -> List[Dict]:
        """
        Получение списка доступных моделей через OpenRouter
        """
        try:
            import requests
            
            response = requests.get(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/tikhonmakeev/finam_RADAR__finvam_team",
                    "X-Title": "Finam Radar"
                }
            )
            
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                logger.error(f"Error fetching models: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
