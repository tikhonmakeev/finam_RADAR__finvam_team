"""
Клиент для работы с локальной LLM через Ollama.
"""
import os
import logging
import aiohttp
from typing import Optional, Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    """Клиент для работы с локальной LLM через Ollama."""
    
    def __init__(self):
        """Инициализация клиента Ollama."""
        self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api")
        self.model = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")  # Используем phi4-mini как модель по умолчанию
        self.session = None
        logger.info(f"Инициализирован клиент Ollama с моделью: {self.model}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def __aenter__(self):
        await self._get_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: str = None, 
        **kwargs
    ) -> Optional[str]:
        """
        Генерация ответа с использованием локальной LLM.

        Args:
            prompt: Текст промпта
            system_prompt: Дополнительный системный промпт
            **kwargs: Дополнительные параметры

        Returns:
            Сгенерированный текст или None в случае ошибки
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        session = await self._get_session()

        try:
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.1),
                    "top_p": kwargs.get('top_p', 0.9),
                    "max_tokens": kwargs.get('max_tokens', 1000)
                }
            }

            async with session.post(
                f"{self.base_url}/chat",
                json=data,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка Ollama API: {response.status} - {error_text}")
                    return None

                result = await response.json()
                return result['message']['content'].strip()

        except Exception as e:
            logger.error(f"Ошибка при вызове Ollama API: {str(e)}", exc_info=True)
            return None

# Глобальный экземпляр для удобства использования
llm_client = LLMClient()