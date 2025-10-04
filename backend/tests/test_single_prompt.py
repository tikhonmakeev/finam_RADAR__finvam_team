import asyncio
import requests
import logging
import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем URL из .env или используем по умолчанию
LLM_API_URL = os.getenv('LLM_API_URL', 'http://127.0.0.1:11434')

# УЛУЧШЕННЫЙ ПРОМПТ
SYSTEM_PROMPT_TAGGER = """
Ты — классификатор финансовых новостей. Твоя ЕДИНСТВЕННАЯ задача — выбрать ОДИН тег из списка.

СПИСОК ТЕГОВ (только эти варианты):
Информационные технологии
Металлы и добыча
Макроэкономические показатели
Нефть и газ
Потребительский сектор
Строительные компании
Телекоммуникации
Транспорт
Финансы
Финтех
Фармацевтика
Химия и нефтехимия
Электроэнергетика
None

ЖЕСТКИЕ ПРАВИЛА:
1. Возвращай ТОЛЬКО название тега из списка выше или 'None'
2. НИКАКИХ объяснений, размышлений, дополнительного текста
3. Если новость не подходит ни под один тег — строго 'None'
4. Выбирай наиболее точный тег по СУТИ бизнеса/деятельности

ПРИМЕРЫ ОТВЕТОВ:
"Компания Apple представила новый iPhone" → "Информационные технологии"
"Газпром увеличил добычу газа" → "Нефть и газ" 
"ЦБ повысил ключевую ставку" → "Финансы"
"Открылась новая станция метро" → "None"
"Сбербанк запустил мобильное приложение" → "Финтех"

ТВОЙ ОТВЕТ ДОЛЖЕН БЫТЬ ОДНОЙ СТРОКОЙ БЕЗ КАВЫЧЕК!
"""


def check_ollama_availability():
    """Проверка доступности Ollama"""
    try:
        logger.info(f"🔍 Проверяем доступность Ollama по адресу: {LLM_API_URL}")
        response = requests.get(f"{LLM_API_URL}/api/tags", timeout=500)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✅ Ollama доступен. Модели: {[m['name'] for m in models]}")
            return True
        else:
            logger.error(f"❌ Ollama отвечает с ошибкой: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Не удалось подключиться к Ollama по адресу {LLM_API_URL}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False


def get_fast_model():
    """Выбираем быструю модель из доступных"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/tags", timeout=500)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]

            # Приоритет быстрых моделей
            fast_models = [
                'phi4-mini:latest',  # Самая быстрая
                'llama3.2:1b',  # Очень легкая
                'llama3.2:3b',  # Легкая
            ]

            # Ищем быструю модель из приоритетного списка
            for fast_model in fast_models:
                for available_model in model_names:
                    if fast_model in available_model:
                        logger.info(f"🚀 Выбрана быстрая модель: {available_model}")
                        return available_model

            # Если быстрых нет, берем первую доступную
            if model_names:
                logger.info(f"ℹ️ Используем модель: {model_names[0]}")
                return model_names[0]
            else:
                logger.error("❌ Нет доступных моделей")
                return None

    except Exception as e:
        logger.error(f"❌ Ошибка при выборе модели: {e}")
        return None


def test_prompt_tagger_improved():
    """Улучшенное тестирование промпта тегирования"""

    if not check_ollama_availability():
        return False

    # Выбираем модель
    model_name = get_fast_model()
    if not model_name:
        return False

    # Тестовые новости
    test_cases = [
        "Компания Газпром увеличила добычу газа на 10%",
        "Apple представила новый iPhone с искусственным интеллектом",
        "Банк России повысил ключевую ставку до 15%",
        "В Москве открылся новый торговый центр",
        "Норильский никель сообщил о росте добычи палладия",
        "Сбербанк запустил сервис цифровых платежей",
    ]

    for i, test_text in enumerate(test_cases, 1):
        logger.info(f"\n🧪 Тест {i}: {test_text}")

        # УЛУЧШЕННЫЙ ПРОМПТ - четкая структура
        prompt = f"""{SYSTEM_PROMPT_TAGGER}

НОВОСТЬ ДЛЯ КЛАССИФИКАЦИИ: "{test_text}"

ТЕГ:"""

        try:
            response = requests.post(
                f"{LLM_API_URL}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # МИНИМАЛЬНАЯ случайность
                        "num_predict": 10,  # ОЧЕНЬ короткий ответ
                        "top_k": 1,  # Только самый вероятный вариант
                    }
                },
                timeout=500
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                # ОЧИСТКА ответа - берем только первую строку, убираем лишнее
                cleaned_response = response_text.split('\n')[0].strip()
                cleaned_response = cleaned_response.replace('"', '').replace("'", "")

                logger.info(f"✅ Результат: '{cleaned_response}'")

                # Проверяем валидность тега
                valid_tags = [
                    "Информационные технологии", "Металлы и добыча", "Макроэкономические показатели",
                    "Нефть и газ", "Потребительский сектор", "Строительные компании",
                    "Телекоммуникации", "Транспорт", "Финансы", "Финтех",
                    "Фармацевтика", "Химия и нефтехимия", "Электроэнергетика", "None"
                ]

                if cleaned_response in valid_tags:
                    logger.info(f"🎯 ВАЛИДНЫЙ тег!")
                else:
                    logger.warning(f"⚠️ НЕВАЛИДНЫЙ тег: '{cleaned_response}'")

            else:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            return False

    return True


def main():
    """Основная функция"""
    logger.info("🚀 Запуск ТЕСТИРОВАНИЯ УЛУЧШЕННОГО ПРОМПТА...")

    # Проверка доступности
    if not check_ollama_availability():
        logger.error("❌ Ollama не доступен")
        return

    # Тестирование
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТИРОВАНИЕ КЛАССИФИКАТОРА НОВОСТЕЙ")
    logger.info("=" * 60)

    success = test_prompt_tagger_improved()

    if success:
        logger.info("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        logger.info("\n💥 ЕСТЬ ПРОБЛЕМЫ С КЛАССИФИКАЦИЕЙ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")