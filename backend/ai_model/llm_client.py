import json
import logging
from typing import Optional
import requests
from requests.exceptions import RequestException
from config import settings

# Настройка логирования
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Конфигурация для локального LLM (Ollama/Пользовательский HTTP)
LLM_API_URL = getattr(settings, 'LLM_API_URL', 'http://127.0.0.1:11434')
MODEL_NAME = getattr(settings, 'LLM_MODEL_NAME', 'qwen3:latest')


class LocalLLMClient:
    """Клиент для взаимодействия с локальной LLM-службой.
    
    Поддерживает как API, совместимые с Ollama, так и с OpenAI.
    """
    
    def __init__(self, base_url: str = None, model: str = None):
        base_url = base_url or LLM_API_URL
        model = model or MODEL_NAME
        """Инициализация клиента LLM.
        
        Args:
            base_url (str): Базовый URL сервера LLM API
            model (str): Название используемой модели
            
        Инициализирует сессию для HTTP-запросов и сохраняет настройки подключения.
        """
        self.base_url = base_url.rstrip('/')  # Удаляем слэш в конце, если есть
        self.model = model
        self.session = requests.Session()  # Создаем сессию для повторного использования соединения
        
    def chat(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        """Отправка сообщения в LLM и получение ответа.
        
        Args:
            prompt (str): Промпт пользователя
            system (Optional[str]): Системное сообщение (опционально)
            max_tokens (int): Максимальное количество токенов в ответе
            temperature (float): Температура сэмплирования (0-1, где 0 - детерминированный вывод)
            
        Returns:
            str: Сгенерированный текстовый ответ
            
        Raises:
            RequestException: При ошибке HTTP-запроса
            ValueError: При невозможности разобрать ответ сервера
            
        Пример использования:
            client = LocalLLMClient()
            response = client.chat("Привет, как дела?", temperature=0.5)
        """
        # Подготавливаем сообщения для отправки
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Формируем тело запроса
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": max(0, min(1, temperature))  # Ограничиваем температуру в диапазоне [0, 1]
        }
        
        try:
            # Пытаемся отправить запрос к API, совместимому с Ollama
            logger.debug(f"Отправка запроса к {self.base_url}/api/chat")
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=500  # Увеличенный таймаут до 500 секунд
            )
            response.raise_for_status()  # Проверяем статус ответа
            
            # Пробуем распарсить JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                # Если не удалось распарсить JSON, возвращаем сырой текст
                logger.warning(f"Не удалось распарсить JSON ответа. Сырой ответ: {response.text}")
                return response.text.strip()
            
            # Обрабатываем различные форматы ответов от разных API
            try:
                if isinstance(data, dict):
                    if 'message' in data and isinstance(data['message'], dict) and 'content' in data['message']:
                        return str(data['message']['content']).strip()
                    elif 'choices' in data and isinstance(data['choices'], list) and data['choices']:
                        choice = data['choices'][0]
                        if isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                            return str(choice['message']['content']).strip()
                        return str(choice).strip()
                    elif 'text' in data:
                        return str(data['text']).strip()
                
                # Если формат ответа не распознан, возвращаем весь ответ как строку
                return str(data).strip()
                
            except Exception as e:
                logger.warning(f"Ошибка при обработке ответа: {str(e)}. Ответ: {data}")
                return str(data).strip()
                
        except RequestException as e:
            # Обработка ошибок сети и HTTP
            logger.error(f"Ошибка при запросе к API: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            # Обработка ошибок парсинга JSON
            error_msg = f"Не удалось разобрать ответ сервера: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e