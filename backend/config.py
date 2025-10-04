from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    """
    Класс для хранения настроек приложения.
    Переменные окружения загружаются из .env файла.
    """
    
    # Настройки API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finam Radar API"
    
    # Настройки безопасности
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 дней
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    
    # Настройки модели
    MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    
    class Config:
        # Указываем, что нужно использовать .env файл
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Создаем экземпляр настроек
settings = Settings()

# Пример использования:
# from config import settings
# print(settings.DATABASE_URL)
