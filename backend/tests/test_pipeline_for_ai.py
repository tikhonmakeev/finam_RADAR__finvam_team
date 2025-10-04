"""
ПОЛНЫЙ ТЕСТ ПАЙПЛАЙНА ОБРАБОТКИ НОВОСТЕЙ
1. Создание саммари → 2. Тегирование → 3. Оценка влияния → 4. Сравнение → 5. Обновление дубликатов
"""
import sys
from pathlib import Path
import logging
import asyncio
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Загружаем переменные окружения
load_dotenv()

# Добавляем корень проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from ai_model.news_processor import NewsProcessor, process_news_batch
from backend.db.vector_store import VectorStore

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('full_pipeline_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

LLM_API_URL = os.getenv('LLM_API_URL', 'http://127.0.0.1:11434')


def load_test_news():
    """Загрузка тестовых новостей для пайплайна"""
    test_news = [
        # Новости о Газпроме (похожие, но с разными деталями)
        {
            'title': 'Газпром увеличил добычу газа',
            'text': 'Компания Газпром сообщила о росте добычи газа на 10% в этом квартале. Акции компании выросли на 5%. Подписывайтесь на наш канал!',
            'source': 'Телеграм-канал 1',
            'date': '2025-01-02'
        },
        {
            'title': 'Газпром нарастил добычу',
            'text': 'По данным отчетности, Газпром увеличил объем добычи газа на 12% в последнем квартале. Инвесторы позитивно оценили новость.',
            'source': 'Телеграм-канал 2',
            'date': '2025-01-02'
        },
        {
            'title': 'Газпром: рекордная добыча',
            'text': 'Газпром установил рекорд по добыче газа - рост составил 15%. Акции Газпрома демонстрируют уверенный рост.',
            'source': 'Новостной портал',
            'date': '2025-01-03'
        },

        # Новости о технологиях (разные компании)
        {
            'title': 'Apple представила новый iPhone',
            'text': 'Компания Apple announced новый iPhone с искусственным интеллектом. Ожидается рост продаж.',
            'source': 'Tech News',
            'date': '2025-01-02'
        },
        {
            'title': 'Samsung выпустил новый Galaxy',
            'text': 'Samsung представил новый смартфон Galaxy с улучшенной камерой. Конкуренция на рынке усиливается.',
            'source': 'Tech Portal',
            'date': '2025-01-02'
        },

        # Финансовые новости
        {
            'title': 'ЦБ повысил ключевую ставку',
            'text': 'Центральный банк повысил ключевую ставку на 1%. Аналитики ожидают давления на рынок акций.',
            'source': 'Финансовый канал',
            'date': '2025-01-02'
        },
        {
            'title': 'Банк X увеличил прибыль',
            'text': 'Банк X сообщил о росте чистой прибыли на 25% в этом квартале. Акции банка показали рост.',
            'source': 'Банковские новости',
            'date': '2025-01-02'
        }
    ]
    return test_news


async def test_individual_steps():
    """Тестирование каждого этапа пайплайна отдельно"""
    logger.info("\n" + "=" * 80)
    logger.info("ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ ЭТАПОВ ПАЙПЛАЙНА")
    logger.info("=" * 80)

    processor = NewsProcessor()
    test_news = load_test_news()

    # Тестируем на первой новости
    sample_news = test_news[0]

    logger.info(f"\n📰 ТЕСТОВАЯ НОВОСТЬ: {sample_news['title']}")
    logger.info(f"📝 Текст: {sample_news['text'][:100]}...")

    # 1. ТЕСТИРУЕМ ПОЛНУЮ ОБРАБОТКУ
    logger.info("\n1. 🔄 ПОЛНАЯ ОБРАБОТКА НОВОСТИ...")
    try:
        full_result = await processor.process_news_item(sample_news)

        if full_result:
            logger.info("✅ Полная обработка завершена")
            logger.info(f"   🏷️ Теги: {', '.join(full_result.get('tags', []))}")
            logger.info(f"   📈 Влияние: {full_result.get('market_impact', {}).get('impact_level', 'неизвестно')}")
            logger.info(f"   📋 Сводка: {full_result.get('summary', '')[:100]}...")
        else:
            logger.error("❌ Ошибка полной обработки")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка полной обработки: {e}")
        return False

    return True


async def test_duplicate_detection():
    """Тестирование обнаружения и обработки дубликатов"""
    logger.info("\n" + "=" * 80)
    logger.info("ТЕСТИРОВАНИЕ ОБНАРУЖЕНИЯ ДУБЛИКАТОВ")
    logger.info("=" * 80)

    processor = NewsProcessor()
    test_news = load_test_news()

    # Берем новости о Газпроме (похожие)
    gazprom_news = [news for news in test_news if 'Газпром' in news['title']]

    logger.info(f"🔍 Тестируем обнаружение дубликатов среди {len(gazprom_news)} новостей о Газпроме")

    results = []
    for i, news in enumerate(gazprom_news, 1):
        logger.info(f"\n📰 Обработка новости {i}: {news['title']}")

        try:
            result = await processor.process_news_item(news)
            if result:
                results.append(result)
                logger.info(
                    f"   ✅ Обработана: теги={result.get('tags', [])}, влияние={result.get('market_impact', {}).get('impact_level', 'неизвестно')}")
            else:
                logger.error(f"   ❌ Ошибка обработки")
        except Exception as e:
            logger.error(f"   ❌ Ошибка: {e}")

    # Анализ дубликатов
    if len(results) >= 2:
        logger.info("\n🔍 АНАЛИЗ ДУБЛИКАТОВ:")

        # Простая проверка по тегам и сути
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results[i + 1:], i + 1):
                tags1 = set(result1.get('tags', []))
                tags2 = set(result2.get('tags', []))

                common_tags = tags1.intersection(tags2)
                if common_tags:
                    logger.info(f"   📰 Новость {i + 1} и {j + 1}: общие теги {list(common_tags)} - ВОЗМОЖНЫЕ ДУБЛИКАТЫ")
                else:
                    logger.info(f"   📰 Новость {i + 1} и {j + 1}: разные теги - РАЗНЫЕ СОБЫТИЯ")


async def test_batch_processing():
    """Тестирование пакетной обработки"""
    logger.info("\n" + "=" * 80)
    logger.info("ТЕСТИРОВАНИЕ ПАКЕТНОЙ ОБРАБОТКИ")
    logger.info("=" * 80)

    test_news = load_test_news()

    logger.info(f"📦 Обрабатываем пакет из {len(test_news)} новостей...")

    try:
        results = await process_news_batch(test_news)

        successful = [r for r in results if r is not None]
        logger.info(f"✅ Успешно обработано: {len(successful)}/{len(test_news)}")

        # Статистика по тегам
        all_tags = []
        for result in successful:
            all_tags.extend(result.get('tags', []))

        from collections import Counter
        tag_stats = Counter(all_tags)
        logger.info(f"🏷️ Распределение тегов: {dict(tag_stats)}")

        # Статистика по влиянию
        impact_stats = Counter()
        for result in successful:
            impact = result.get('market_impact', {}).get('impact_level', 'unknown')
            impact_stats[impact] += 1
        logger.info(f"📈 Распределение влияния: {dict(impact_stats)}")

    except Exception as e:
        logger.error(f"❌ Ошибка пакетной обработки: {e}")


async def test_news_aggregation():
    """Тестирование агрегации похожих новостей"""
    logger.info("\n" + "=" * 80)
    logger.info("ТЕСТИРОВАНИЕ АГРЕГАЦИИ НОВОСТЕЙ")
    logger.info("=" * 80)

    processor = NewsProcessor()

    # Создаем явные дубликаты с разными источниками
    duplicate_news = [
        {
            'title': 'Компания X увеличила прибыль',
            'text': 'Компания X сообщила о росте чистой прибыли на 20% в этом квартале. Ожидается рост дивидендов.',
            'source': 'Источник A',
            'date': '2025-01-02'
        },
        {
            'title': 'Рост прибыли компании X',
            'text': 'По данным отчетности, компания X показала рост чистой прибыли на 20%. Инвесторы довольны результатами.',
            'source': 'Источник B',
            'date': '2025-01-02'
        },
        {
            'title': 'Компания X: финансовые результаты',
            'text': 'Компания X отчиталась о росте прибыли на 20%. Акции компании демонстрируют позитивную динамику.',
            'source': 'Источник C',
            'date': '2025-01-03'
        }
    ]

    logger.info("🔄 Обрабатываем явные дубликаты...")

    results = []
    for news in duplicate_news:
        try:
            result = await processor.process_news_item(news)
            if result:
                results.append(result)
                logger.info(f"   ✅ {news['source']}: {news['title']}")
        except Exception as e:
            logger.error(f"   ❌ Ошибка обработки {news['source']}: {e}")

    # Анализ результатов агрегации
    if len(results) >= 2:
        logger.info("\n📊 АНАЛИЗ АГРЕГАЦИИ:")

        # Группируем по основным тегам
        news_by_tag = {}
        for result in results:
            tags = result.get('tags', [])
            main_tag = tags[0] if tags else 'unknown'
            if main_tag not in news_by_tag:
                news_by_tag[main_tag] = []
            news_by_tag[main_tag].append(result)

        for tag, news_list in news_by_tag.items():
            if len(news_list) > 1:
                logger.info(f"   🔗 Тег '{tag}': {len(news_list)} похожих новостей")
                sources = [n['original_news']['source'] for n in news_list]
                logger.info(f"      Источники: {', '.join(sources)}")


async def test_vector_store_integration():
    """Тестирование интеграции с векторным хранилищем"""
    logger.info("\n" + "=" * 80)
    logger.info("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ С VECTOR STORE")
    logger.info("=" * 80)

    try:
        from backend.db.vector_store import VectorStore

        vector_store = VectorStore()
        test_news = load_test_news()

        logger.info("🗄️ Индексируем тестовые новости...")

        # Индексируем несколько новостей
        for i, news in enumerate(test_news[:3], 1):
            try:
                vector_store.index_news(
                    news_id=f"test_{i}",
                    text=news['text'],
                    metadata={
                        'title': news['title'],
                        'source': news['source'],
                        'date': news['date'],
                        'tags': ['test']  # Тестовые теги
                    }
                )
                logger.info(f"   ✅ Проиндексирована: {news['title']}")
            except Exception as e:
                logger.error(f"   ❌ Ошибка индексации: {e}")

        # Тестируем поиск
        logger.info("\n🔍 Тестируем поиск похожих новостей...")
        try:
            search_results = vector_store.query("Газпром добыча газ", top_k=2)
            if search_results:
                logger.info(f"   ✅ Найдено {len(search_results)} результатов по запросу 'Газпром'")
                for i, result in enumerate(search_results, 1):
                    meta = result.get('meta', {})
                    logger.info(
                        f"      {i}. {meta.get('title', 'Без названия')} (сходство: {result.get('score', 0):.3f})")
            else:
                logger.info("   ℹ️ Поиск не дал результатов")

        except Exception as e:
            logger.error(f"   ❌ Ошибка поиска: {e}")

    except ImportError:
        logger.warning("⚠️ VectorStore не доступен, пропускаем тест")
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования VectorStore: {e}")


async def generate_pipeline_report():
    """Генерация отчета о работе пайплайна"""
    logger.info("\n" + "=" * 80)
    logger.info("ФИНАЛЬНЫЙ ОТЧЕТ ПО ПАЙПЛАЙНУ")
    logger.info("=" * 80)

    test_news = load_test_news()
    processor = NewsProcessor()

    # Обрабатываем все новости для отчета
    all_results = []
    for news in test_news:
        try:
            result = await processor.process_news_item(news)
            if result:
                all_results.append(result)
        except Exception as e:
            logger.error(f"Ошибка обработки {news['title']}: {e}")

    # Аналитический отчет
    logger.info("\n📊 СВОДНЫЙ ОТЧЕТ:")
    logger.info(f"📈 Всего новостей: {len(test_news)}")
    logger.info(f"✅ Успешно обработано: {len(all_results)}")
    logger.info(f"📝 Эффективность: {(len(all_results) / len(test_news) * 100):.1f}%")

    # Анализ тегов
    all_tags = []
    for result in all_results:
        all_tags.extend(result.get('tags', []))

    from collections import Counter
    if all_tags:
        tag_stats = Counter(all_tags)
        logger.info(f"\n🏷️ РАСПРЕДЕЛЕНИЕ ТЕГОВ:")
        for tag, count in tag_stats.most_common():
            logger.info(f"   {tag}: {count} новостей")

    # Анализ влияния
    impact_stats = Counter()
    for result in all_results:
        impact = result.get('market_impact', {}).get('impact_level', 'unknown')
        impact_stats[impact] += 1

    logger.info(f"\n📈 РАСПРЕДЕЛЕНИЕ ВЛИЯНИЯ:")
    for impact, count in impact_stats.most_common():
        logger.info(f"   {impact}: {count} новостей")

    # Качество нормализации
    normalization_stats = []
    for result in all_results:
        original_len = len(result['original_news']['text'])
        normalized_len = len(result.get('style_normalized', ''))
        if normalized_len > 0:
            compression = ((original_len - normalized_len) / original_len * 100)
            normalization_stats.append(compression)

    if normalization_stats:
        avg_compression = sum(normalization_stats) / len(normalization_stats)
        logger.info(f"\n✂️ ЭФФЕКТИВНОСТЬ НОРМАЛИЗАЦИИ:")
        logger.info(f"   Среднее сжатие: {avg_compression:.1f}%")
        logger.info(f"   Лучшее сжатие: {max(normalization_stats):.1f}%")
        logger.info(f"   Худшее сжатие: {min(normalization_stats):.1f}%")


async def main():
    """Основная функция тестирования"""
    logger.info("🚀 ЗАПУСК ПОЛНОГО ТЕСТА ПАЙПЛАЙНА ОБРАБОТКИ НОВОСТЕЙ")

    # Проверка подключения
    try:
        import requests
        response = requests.get(f"{LLM_API_URL}/api/tags", timeout=10)
        if response.status_code != 200:
            logger.error("❌ Ollama не доступен")
            return
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return

    # Запускаем все тесты
    await test_individual_steps()
    await test_duplicate_detection()
    await test_batch_processing()
    await test_news_aggregation()
    await test_vector_store_integration()
    await generate_pipeline_report()

    logger.info("\n🎉 ТЕСТИРОВАНИЕ ПАЙПЛАЙНА ЗАВЕРШЕНО!")
    logger.info("💡 Рекомендации:")
    logger.info("   1. Проверьте логи на наличие ошибок")
    logger.info("   2. Убедитесь, что все этапы работают корректно")
    logger.info("   3. Проанализируйте эффективность обнаружения дубликатов")
    logger.info("   4. Оптимизируйте параметры для улучшения производительности")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")