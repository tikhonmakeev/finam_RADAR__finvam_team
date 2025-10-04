"""
Тестирование обработчика новостей с цепочкой промптов и RAG.
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Добавляем корень проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from ai_model.news_processor import NewsProcessor, process_news_batch

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

def load_news_data(file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Загружает новостные данные из CSV файла."""
    import csv
    news_items = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            # Фильтруем пустые или невалидные записи
            rows = [row for row in reader if row.get('Text') and len(row['Text']) > 50]
            return rows[:limit]
    except Exception as e:
        logger.error(f"Ошибка загрузки новостных данных: {e}")
        return []

async def main():
    """Основная функция для тестирования обработчика новостей."""
    logger.info("Запуск тестирования обработчика новостей...")
    
    # Загружаем новостные данные
    data_path = Path(__file__).parent.parent / 'data' / 'news_data.csv'
    logger.info(f"Загружаем новостные данные из: {data_path}")
    news_data = load_news_data(data_path, limit=5)
    
    if not news_data:
        logger.error("Не удалось загрузить новостные данные")
        return
        
    logger.info(f"Загружено {len(news_data)} новостей для обработки")
    
    # Инициализируем процессор новостей
    processor = NewsProcessor()
    results = []
    
    # Обрабатываем каждую новость
    for i, item in enumerate(news_data, 1):
        logger.info("\n" + "="*80)
        logger.info(f"ОБРАБОТКА НОВОСТИ {i} из {len(news_data)}")
        logger.info("-" * 80)
        
        # Подготавливаем данные новости
        news_item = {
            'title': item.get('Title', f'Новость {i}'),
            'text': item.get('Text', ''),
            'source': item.get('Source', 'Неизвестный источник'),
            'date': item.get('Date', '')
        }
        
        # Обрабатываем новость
        try:
            result = await processor.process_news_item(news_item)
            results.append(result)
            
            # Выводим краткую информацию о результате
            logger.info(f"Обработано: {news_item['title']}")
            logger.info(f"Теги: {', '.join(result.get('tags', [])) or 'Нет тегов'}")
            logger.info(f"Рыночное влияние: {result.get('market_impact', {}).get('impact_level', 'неизвестно')}")
            
            # Сохраняем промежуточные результаты в файл
            with open('news_processing_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке новости: {e}", exc_info=True)
    
    # Выводим финальную сводку
    if results:
        logger.info("\n" + "="*80)
        logger.info("ОБРАБОТКА ЗАВЕРШЕНА")
        logger.info("="*80)
        
        for i, result in enumerate(results, 1):
            logger.info(f"\nНОВОСТЬ {i}:")
            logger.info(f"Заголовок: {result['original_news'].get('title', 'Без названия')}")
            logger.info(f"Теги: {', '.join(result.get('tags', [])) or 'Нет тегов'}")
            logger.info(f"Рыночное влияние: {result.get('market_impact', {}).get('impact_level', 'неизвестно')}")
            
            # Выводим сводку (первые 200 символов)
            summary = result.get('summary', '')
            logger.info("Сводка: " + (summary[:200] + '...' if len(summary) > 200 else summary))
    
    logger.info("\nПодробные результаты сохранены в файл 'news_processing_results.json'")

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nОбработка прервана пользователем.")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
