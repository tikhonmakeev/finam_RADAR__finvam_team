"""
Универсальный LLM клиент с поддержкой Ollama, OpenAI и OpenRouter
"""
import os
import logging
import json
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Union, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем клиенты
# try:
#     from .openai_client import OpenAIClient
# except ImportError:
#     OpenAIClient = None

from .openrouter_client import OpenRouterClient

class LLMClient:
    """Универсальный LLM клиент с поддержкой разных провайдеров."""
    
    def __init__(self):
        """Инициализация клиента с выбранным провайдером."""
        self.provider = os.getenv('LLM_PROVIDER', 'ollama').lower()
        self.timeout = 30  # Таймаут в секундах
        self.client = None
        self._model_checked = False
        
        # Инициализация выбранного провайдера
        if self.provider == 'openrouter':
            try:
                self.client = OpenRouterClient()
                logger.info(f"🌐 Используется OpenRouter с моделью: {os.getenv('OPENROUTER_MODEL')}")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации OpenRouter: {e}")
                raise
        # elif self.provider == 'openaiapi' and OpenAIClient:
        #     self.client = OpenAIClient()
        #     logger.info(f"🚀 Используется OpenAI API с моделью: {self.client.model}")
        else:  # По умолчанию используем Ollama
            self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api")
            self.model = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")
            self.session = None
            logger.info(f"🔮 Используется Ollama с моделью: {self.model}")
            # Не запускаем проверку модели при инициализации
            # Она будет выполнена при первом запросе

    async def _check_model_availability(self):
        """Проверка доступности модели."""
        if self._model_checked:
            return
            
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/tags") as resp:
                if resp.status == 200:
                    models = await resp.json()
                    available_models = [m['name'] for m in models.get('models', [])]
                    logger.info(f"Доступные модели: {available_models}")
                    if self.model not in available_models:
                        logger.warning(f"Модель {self.model} не найдена. Доступные модели: {available_models}")
            self._model_checked = True
        except Exception as e:
            logger.warning(f"Не удалось проверить доступность модели: {e}")
            # Пробуем снова при следующем запросе
            self._model_checked = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def __aenter__(self):
        await self._get_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'session') and self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Выполнение запроса к API Ollama."""
        if not hasattr(self, 'session'):
            logger.error("Сессия не инициализирована. Используйте контекстный менеджер (async with).")
            return None
            
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with session.post(
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка API ({response.status}): {error_text}")
                    return None
                return await response.json()
                
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при обращении к {url} (таймаут: {self.timeout}с)")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения с API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обращении к API: {str(e)}", exc_info=True)
            return None

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: str = None, 
        **kwargs
    ) -> Optional[Union[str, Dict]]:
        """
        Генерация ответа с использованием выбранного провайдера LLM.

        Args:
            prompt: Текст промпта
            system_prompt: Дополнительный системный промпт
            **kwargs: Дополнительные параметры
                - temperature: Температура генерации (0.0-1.0)
                - max_tokens: Максимальное количество токенов
                - top_p: Параметр top-p

        Returns:
            Сгенерированный текст или None в случае ошибки
        """
        # Если используется внешний клиент (OpenRouter, OpenAI API)
        if self.client and hasattr(self.client, 'generate_response'):
            return await self.client.generate_response(prompt, system_prompt, **kwargs)
            
        # Для Ollama проверяем доступность модели при первом запросе
        if not self._model_checked:
            await self._check_model_availability()
            
        # Используем Ollama
        return await self._ollama_generate(prompt, system_prompt, **kwargs)
        
    async def _ollama_generate(
        self, 
        prompt: str, 
        system_prompt: str = None, 
        **kwargs
    ) -> Optional[Union[str, Dict]]:
        """
        Генерация ответа через Ollama API.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

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

        result = await self._make_request("chat", data)
        if not result or 'message' not in result or 'content' not in result['message']:
            return None
            
        return result['message']['content'].strip()

    async def chat_completion(self, messages: list, **kwargs) -> Optional[str]:
        """
        Универсальный chat completion для всех провайдеров.
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}, ...]
            **kwargs: Дополнительные параметры
            
        Returns:
            Ответ модели или None в случае ошибки
        """
        if not messages:
            logger.error("Список сообщений не может быть пустым")
            return None
            
        # Если используется внешний клиент (OpenRouter, OpenAI API)
        if self.client and hasattr(self.client, 'generate_response'):
            # Преобразуем сообщения в формат промпта
            prompt = ""
            system_prompt = None
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                elif msg.get('role') == 'user':
                    prompt = msg.get('content', '')
            
            return await self.client.generate_response(prompt, system_prompt, **kwargs)
            
        # Для Ollama преобразуем сообщения в текстовый формат
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            formatted_messages.append(f"{role}: {content}")
            
        return await self._ollama_generate("\n".join(formatted_messages), **kwargs)
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущем провайдере.
        
        Returns:
            Словарь с информацией о провайдере
        """
        info = {
            'provider': self.provider,
            'status': 'active' if hasattr(self, 'client') and self.client else 'inactive'
        }
        
        if self.provider == 'openrouter' and hasattr(self, 'client') and self.client:
            info['model'] = self.client.model
        # elif self.provider == 'openaiapi' and hasattr(self, 'client') and self.client:
        #     info['model'] = self.client.model
        elif self.provider == 'ollama':
            info['model'] = getattr(self, 'model', 'unknown')
            
        return info

# Глобальный экземпляр для удобства использования
llm_client = LLMClient()