import pandas as pd
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import sys

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

from backend.db.vector_store import VectorStore
from backend.ai_model.summarizer import summarize_text
from backend.services.rag_service import retrieve_and_normalize

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Добавляем поддержку кириллицы в логах
)
logger = logging.getLogger(__name__)

class RAGTester:
    def __init__(self, vector_dim: int = 384):
        """Инициализация тестера RAG с векторным хранилищем."""
        self.vector_store = VectorStore(dim=vector_dim)
        logger.info("RAG Tester инициализирован с векторным хранилищем")

    def load_news_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Загрузка новостных статей из CSV файла.
        
        Args:
            csv_path: Путь к CSV файлу с новостными данными
            
        Returns:
            Список словарей с данными новостей
        """
        try:
            df = pd.read_csv(csv_path)
            # Конвертируем DataFrame в список словарей
            news_list = df.to_dict('records')
            logger.info(f"Загружено {len(news_list)} новостных статей из {csv_path}")
            return news_list
        except Exception as e:
            logger.error(f"Ошибка при загрузке CSV файла: {str(e)}")
            raise

    def index_news_batch(self, news_list: List[Dict[str, Any]]):
        """Индексация пакета новостных статей.
        
        Args:
            news_list: Список словарей с новостными статьями
        """
        for i, news in enumerate(news_list, 1):
            try:
                # Создаем уникальный ID для каждой новости
                news_id = f"news_{i}"
                
                # Генерируем краткое содержание
                summary = summarize_text(news.get('text', news.get('content', '')))
                
                # Подготавливаем метаданные
                metadata = {
                    'title': news.get('title', 'Без названия'),
                    'source': news.get('source', 'Неизвестно'),
                    'date': news.get('date', ''),
                    'summary': summary
                }
                
                # Индексируем документ
                self.vector_store.index_news(
                    news_id=news_id,
                    text=news.get('text', news.get('content', '')),
                    metadata=metadata
                )
                
                if i % 10 == 0:
                    logger.info(f"Проиндексировано {i}/{len(news_list)} новостных статей")
                    
            except Exception as e:
                logger.error(f"Ошибка при индексации новости {i}: {str(e)}")
                continue
                
        logger.info(f"Завершена индексация {len(news_list)} новостных статей")

    async def test_query(self, query: str, top_k: int = 3):
        """Тестирование запроса к проиндексированным новостям.
        
        Args:
            query: Поисковый запрос
            top_k: Количество возвращаемых результатов
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"Тестируем запрос: '{query}'")
            logger.info(f"{'='*70}")
            
            # 1. Получаем необработанные результаты поиска
            results = self.vector_store.query(query, top_k=top_k)
            
            # 2. Выводим необработанные результаты
            logger.info("\nНеобработанные результаты поиска:")
            for i, result in enumerate(results, 1):
                meta = result.get('meta', {})
                logger.info(f"\nРезультат {i} (Оценка: {result.get('score', 0):.4f}):")
                logger.info(f"Заголовок: {meta.get('title', 'Без названия')}")
                logger.info(f"Источник: {meta.get('source', 'Неизвестно')}")
                logger.info(f"Краткое содержание: {meta.get('summary', 'Нет краткого содержания')[:150]}...")
            
            # 3. Тестируем улучшенный RAG-ответ
            logger.info("\nУлучшенный RAG-ответ:")
            rag_response = retrieve_and_normalize(query, top_k=top_k)
            logger.info(f"\n{rag_response}")
            
        except Exception as e:
            logger.error(f"Ошибка при тестировании запроса: {str(e)}")
            raise

async def main():
    # Инициализируем тестер
    tester = RAGTester()
    
    # Путь к вашему CSV файлу (замените на актуальный путь)
    csv_path = "backend/data/news_data.csv"
    
    try:
        # Загружаем и индексируем новости
        logger.info("Начинаем загрузку и индексацию новостей...")
        news_list = tester.load_news_from_csv(csv_path)
        tester.index_news_batch(news_list)
        
        # Примеры запросов для тестирования
        test_queries = [
            "новости о фондовом рынке",
            "криптовалюты и биткоин",
            "экономические санкции",
            "изменение курса доллара",
            "новые технологии в финансах"
        ]
        
        # Тестируем каждый запрос
        logger.info("\n" + "="*50)
        logger.info("НАЧИНАЕМ ТЕСТИРОВАНИЕ ЗАПРОСОВ")
        logger.info("="*50)
        
        for query in test_queries:
            await tester.test_query(query)
            logger.info("\n" + "-"*70 + "\n")
            
        logger.info("="*50)
        logger.info("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        logger.info("="*50)
            
    except Exception as e:
        logger.error(f"Ошибка в основной функции: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Запуск тестирования RAG модели...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nТестирование прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise
