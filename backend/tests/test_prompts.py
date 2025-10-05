"""
Тестирование ВСЕХ промптов через цепочку обработки новостей.
Использует промпты из файлов проекта.
"""
import sys
from pathlib import Path
import logging
import asyncio
import functools
import os
from dotenv import load_dotenv
from ai_model.prompts.prompt_tagger import SYSTEM_PROMPT_TAGGER
from ai_model.prompts.prompt_market_impact import SYSTEM_PROMPT_MARKET_IMPACT as SYSTEM_PROMPT_MARKET_IMPACT
from ai_model.prompts.prompt_comparison import SYSTEM_PROMPT_COMPARISON as SYSTEM_PROMPT_COMPARISON
from ai_model.prompts.prompt_style_news import SYSTEM_PROMPT as SYSTEM_PROMPT_STYLE_NEWS

# Загружаем переменные окружения из корня проекта, перекрывая переменные окружения
root_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=root_env_path, override=True)

# Добавляем корень проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from ai_model.news_processor import NewsProcessor, process_news_batch
from ai_model.llm_client import llm_client as global_llm_client


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('news_processor_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Провайдер LLM
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openrouter').lower()
LLM_API_URL = os.getenv('LLM_API_URL', 'http://127.0.0.1:11434')  # используется только для ollама

def timeout(seconds=500):
    """Декоратор для установки таймаута на асинхронные функции."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Функция {func.__name__} превысила таймаут {seconds} секунд")
                return None
        return wrapper
    return decorator

async def test_individual_prompts():
    """Тестирование каждого промпта отдельно используя ваши файлы"""

    logger.info("\n" + "="*80)
    logger.info("ТЕСТИРОВАНИЕ ВСЕХ ПРОМПТОВ ИЗ ФАЙЛОВ")
    logger.info("="*80)

    # ИСПОЛЬЗУЕМ ВАШИ ПРОМПТЫ ИЗ ФАЙЛОВ
    PROMPTS = {
        "tagger": {
            "system": SYSTEM_PROMPT_TAGGER,
            "test_cases": [
                ("Компания Газпром увеличила добычу газа на 10%", "Нефть и газ"),
                ("Apple представила новый iPhone с ИИ", "Информационные технологии"),
                ("Банк России повысил ключевую ставку", "Финансы"),
                ("Норильский никель сообщил о росте добычи", "Металлы и добыча"),
                ("В Москве открылся новый торговый центр", "None"),
            ]
        },
        "market_impact": {
            "system": SYSTEM_PROMPT_MARKET_IMPACT,
            "test_cases": [
                ("Компания X объявила о росте прибыли на 15%", "True"),
                ("Акции компании Y упали на 10% после отчета", "False"),
                ("Компания запустила новый перспективный продукт", "True"),
                ("Компания объявила о банкротстве", "False"),
                ("ЦБ повысил ключевую ставку", "False"),
            ]
        },
        "comparison": {
            "system": SYSTEM_PROMPT_COMPARISON,
            "test_cases": [
                (("Компания X объявила о росте прибыли", "Акции X выросли после отчета о прибыли"), "True"),
                (("ЦБ повысил ставку", "Минфин предложил новые налоги"), "False"),
                (("Газпром увеличил добычу газа", "Газпром сообщил о росте добычи на 10%"), "True"),
                (("Apple представила новый iPhone", "Samsung выпустил новый смартфон"), "False"),
            ]
        },
        "style_normalization": {
            "system": SYSTEM_PROMPT_STYLE_NEWS,
            "test_cases": [
                ("Сегодня Газпром сообщил о росте добычи! Подписывайтесь на наши новости!", "Газпром сообщил о росте добычи."),
                ("По данным телеграм-канала, Apple представила новый iPhone с ИИ. Автор считает это прорывом.", "Apple представила новый iPhone с ИИ."),
                ("Вчера вечером стало известно, что ЦБ может изменить ставку. Подробности читайте на нашем сайте!", "ЦБ может изменить ставку."),
            ]
        }
    }

    # Выбираем модель (только для ollama пути)
    model_name = "phi4-mini:latest"

    for prompt_name, prompt_data in PROMPTS.items():
        logger.info(f"\n🧪 ТЕСТИРУЕМ ПРОМПТ: {prompt_name.upper()}")
        logger.info("-" * 50)

        system_prompt = prompt_data["system"]
        test_cases = prompt_data["test_cases"]

        success_count = 0
        total_count = len(test_cases)

        for i, (test_input, expected) in enumerate(test_cases, 1):
            try:
                if prompt_name == "comparison":
                    news_a, news_b = test_input
                    user_prompt = f"Новость A: {news_a}\nНовость B: {news_b}"
                else:
                    user_prompt = f"{test_input}"

                if LLM_PROVIDER == 'ollama':
                    import requests
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = requests.post(
                        f"{LLM_API_URL}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.0,
                                "num_predict": 30,
                                "top_k": 1
                            }
                        },
                        timeout=500
                    )

                    if response.status_code == 200:
                        result = response.json()
                        response_text = result.get('response', '').strip()
                    else:
                        logger.error(f"   ❌ Ошибка API: {response.status_code}")
                        continue

                else:
                    # Используем OpenRouter через универсальный клиент
                    response_text = await global_llm_client.generate_response(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        max_tokens=512,
                        temperature=0.0,
                        top_p=0.9
                    ) or ""

                # Очистка ответа для разных типов промптов
                if prompt_name in ["tagger", "market_impact", "comparison"]:
                    cleaned_response = response_text.split('\n')[0].strip()
                    cleaned_response = cleaned_response.replace('"', '').replace("'", "").replace('"""', '')
                else:
                    cleaned_response = response_text[:200] + "..." if len(response_text) > 200 else response_text

                logger.info(f"Тест {i}:")
                logger.info(f"   Вход: {test_input}")
                logger.info(f"   Ожидалось: {expected}")
                logger.info(f"   Получено: '{cleaned_response}'")

                # Проверка результатов
                if prompt_name == "style_normalization":
                    if cleaned_response and len(cleaned_response) > 5 and len(cleaned_response) < len(str(test_input)):
                        logger.info("   ✅ ОК (текст нормализован)")
                        success_count += 1
                    else:
                        logger.warning("   ⚠️ Возможно проблема с нормализацией")
                else:
                    if expected.lower() in cleaned_response.lower():
                        logger.info("   ✅ ОК")
                        success_count += 1
                    else:
                        logger.warning("   ⚠️ Не совпадает с ожидаемым")

            except Exception as e:
                logger.error(f"   ❌ Ошибка: {e}")

        # Статистика по промпту
        logger.info(f"📊 Результаты {prompt_name}: {success_count}/{total_count} успешно")

    logger.info("\n✅ ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ ПРОМПТОВ ЗАВЕРШЕНО")

@timeout(500)
async def main():
    """Основная функция для тестирования обработчика новостей."""
    logger.info("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ ОБРАБОТЧИКА НОВОСТЕЙ...")

    # Сначала тестируем отдельные промпты
    await test_individual_prompts()

    # Затем тестируем полную обработку через NewsProcessor
    logger.info("\n" + "="*80)
    logger.info("ТЕСТИРОВАНИЕ ПОЛНОЙ ЦЕПОЧКИ ОБРАБОТКИ ЧЕРЕЗ NEWSPROCESSOR")
    logger.info("="*80)

    # Разнообразные тестовые новости
    test_news_items = [
        {
            'title': 'Газпром увеличил добычу газа',
            'text': 'Компания Газпром сообщила о росте добычи газа на 10% в этом квартале! Акции компании выросли на 5%. Подписывайтесь на наш канал для больше новостей!',
            'source': 'Телеграм-канал',
            'date': '2025-10-04'
        },
        {
            'title': 'Apple представила новый iPhone',
            'text': 'По данным инсайдеров, компания Apple announced новый iPhone с искусственным интеллектом. Автор канала считает это революцией. Не пропустите следующие новости!',
            'source': 'Телеграм-канал',
            'date': '2025-10-04'
        },
        {
            'title': 'ЦБ изменил ставку',
            'text': 'Сегодня стало известно, что Центральный банк может изменить ключевую ставку на следующем заседании. Эксперты ожидают роста volatility на рынке.',
            'source': 'Новостной портал',
            'date': '2025-10-04'
        },
        {
            'title': 'Сбербанк запустил новый сервис',
            'text': 'Сбербанк представил новый сервис цифровых платежей через мобильное приложение. Подписывайтесь на обновления!',
            'source': 'Пресс-релиз',
            'date': '2025-10-04'
        }
    ]

    # Инициализируем процессор
    processor = NewsProcessor()

    # Обрабатываем каждую новость отдельно
    results = []
    for i, news_item in enumerate(test_news_items, 1):
        logger.info(f"\n📰 ОБРАБОТКА НОВОСТИ {i}: {news_item['title']}")
        logger.info("-" * 50)

        try:
            # Обрабатываем с таймаутом
            result = await asyncio.wait_for(
                processor.process_news_item(news_item),
                timeout=500.0  # Increased timeout to 500 seconds
            )

            if result is None:
                logger.error("❌ Результат обработки - None")
                results.append(None)
                continue

            results.append(result)

            # Выводим результаты
            logger.info("✅ РЕЗУЛЬТАТЫ ОБРАБОТКИ:")

            # Теги
            tags = result.get('tags', [])
            logger.info(f"   Теги: {', '.join(tags) if tags else 'Нет тегов'}")

            # Рыночное влияние
            market_impact = result.get('market_impact', {})
            impact_level = market_impact.get('impact_level', 'неизвестно')
            logger.info(f"   Влияние: {impact_level}")

            # Сводка
            summary = result.get('summary', '')
            if summary:
                logger.info(f"   Сводка: {summary[:100]}{'...' if len(summary) > 100 else ''}")
            else:
                logger.info("   Сводка: Нет сводки")

            # Нормализация стиля
            original_length = len(news_item['text'])
            normalized = result.get('style_normalized', '')
            if normalized and normalized != news_item['text']:
                normalized_length = len(normalized)
                logger.info(f"   ✅ Стиль нормализован: {original_length} → {normalized_length} символов")
            else:
                logger.info("   ℹ️  Стиль не изменен")

            logger.info("   ✅ Обработка завершена!")

        except asyncio.TimeoutError:
            logger.error("❌ ТАЙМАУТ: Обработка новости заняла более 120 секунд")
            results.append(None)
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке новости: {e}")
            results.append(None)

    # Анализ итоговых результатов
    logger.info("\n" + "="*80)
    logger.info("ИТОГОВАЯ СТАТИСТИКА")
    logger.info("="*80)

    successful_results = [r for r in results if r is not None]
    logger.info(f"📊 Успешно обработано: {len(successful_results)} из {len(test_news_items)}")

    if successful_results:
        # Анализ тегов
        all_tags = []
        for result in successful_results:
            all_tags.extend(result.get('tags', []))

        from collections import Counter
        tag_stats = Counter(all_tags)
        logger.info(f"🏷️  Распределение тегов: {dict(tag_stats)}")

        # Анализ влияния
        impact_stats = {}
        for result in successful_results:
            impact = result.get('market_impact', {}).get('impact_level', 'unknown')
            impact_stats[impact] = impact_stats.get(impact, 0) + 1
        logger.info(f"📈 Распределение влияния: {impact_stats}")

        # Анализ нормализации
        normalization_stats = []
        for i, result in enumerate(successful_results):
            if 'style_normalized' in result and result['style_normalized'] != test_news_items[i]['text']:
                orig_len = len(test_news_items[i]['text'])
                norm_len = len(result['style_normalized'])
                compression = (orig_len - norm_len) / orig_len * 100
                normalization_stats.append(compression)

        if normalization_stats:
            avg_compression = sum(normalization_stats) / len(normalization_stats)
            logger.info(f"✂️  Среднее сжатие текста: {avg_compression:.1f}%")

    logger.info("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")

async def test_ollama_connection():
    """Проверка подключения к Ollama. Пропускается если провайдер не ollama."""
    if LLM_PROVIDER != 'ollama':
        logger.info("🔍 Пропускаем проверку Ollama (используется не Ollama провайдер)")
        return True

    import requests

    logger.info("🔍 Проверка подключения к Ollama...")
    try:
        response = requests.get(f"{LLM_API_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            logger.info(f"✅ Ollama доступен. Модели: {model_names}")

            fast_models = ['phi4-mini:latest', 'llama3.2:1b', 'llama3.2:3b']
            available_fast = [model for model in model_names if any(fm in model for fm in fast_models)]

            if available_fast:
                logger.info(f"🚀 Рекомендуемые быстрые модели: {available_fast}")
            else:
                logger.warning("⚠️ Быстрые модели не найдены, обработка может занять больше времени")

            return True
        else:
            logger.error(f"❌ Ollama не доступен. Status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Ollama: {e}")
        return False

if __name__ == "__main__":
    try:
        # Сначала проверяем подключение к Ollama, если он выбран
        if not asyncio.run(test_ollama_connection()):
            logger.error("❌ Не удалось подключиться к Ollama. Проверьте запущен ли сервер или переключитесь на OpenRouter (LLM_PROVIDER=openrouter).")
            exit(1)

        # Затем запускаем основной тест
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Тест прерван пользователем.")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)