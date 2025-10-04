import os
import psycopg2
import numpy as np
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """Класс для представления новостной статьи.
    
    Атрибуты:
        id: Уникальный идентификатор новости
        title: Заголовок новости
        content: Содержимое новости
        source: Источник новости
        similarity: Степень сходства с поисковым запросом (опционально)
    """
    id: int
    title: str
    content: str
    source: str
    similarity: Optional[float] = None

class RAGDatabase:
    """Класс для работы с базой данных RAG (Retrieval-Augmented Generation).
    
    Обеспечивает хранение и поиск новостных статей с использованием векторных эмбеддингов.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Инициализация RAG базы данных.
        
        Аргументы:
            model_name: Название модели для генерации эмбеддингов
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # Размерность для модели all-MiniLM-L6-v2
        self.conn = self._get_connection()
        self._init_tables()
        logger.info(f"Инициализирована RAG база данных с моделью: {model_name}")

    def _get_connection(self):
        """Создаем подключение к базе данных"""
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "radar"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432)
        )

    def _init_tables(self):
        """Инициализация таблиц в базе данных"""
        with self.conn.cursor() as cur:
            # Создаем расширение pgvector если его нет
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Таблица новостей
            cur.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """)
            
            # Таблица эмбеддингов
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS news_embeddings (
                news_id INT PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
                embedding vector({self.embedding_dim}) NOT NULL
            );
            """)
            
            # Создаем индекс для ускорения поиска
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_embedding ON news_embeddings 
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """)
            
            self.conn.commit()

    def _get_embedding(self, text: str) -> np.ndarray:
        """Генерация эмбеддинга для текста.
        
        Аргументы:
            text: Входной текст для векторизации
            
        Возвращает:
            Векторное представление текста в виде NumPy массива
        """
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            # Ensure we return a NumPy array even if model.encode returns a different type
            if hasattr(embedding, 'numpy'):  # If it's a PyTorch tensor
                return embedding.numpy()
            return np.array(embedding)  # Convert to NumPy array if it's not already
        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддинга: {str(e)}")
            raise

    def add_news(self, title: str, content: str, source: str) -> int:
        """Добавление новости в базу данных.
        
        Аргументы:
            title: Заголовок новости
            content: Текст новости
            source: Источник новости
            
        Возвращает:
            ID добавленной новости
        """
        try:
            with self.conn.cursor() as cur:
                # Вставляем новость в таблицу
                cur.execute(
                    """
                    INSERT INTO news (title, content, source)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (title, content, source)
                )
                news_id = cur.fetchone()[0]
                
                # Генерируем эмбеддинг для контента
                embedding = self._get_embedding(content)
                
                # Сохраняем эмбеддинг
                cur.execute(
                    """
                    INSERT INTO news_embeddings (news_id, embedding)
                    VALUES (%s, %s);
                    """,
                    (news_id, embedding.tolist())
                )
                
                self.conn.commit()
                logger.info(f"Добавлена новость с ID: {news_id}")
                return news_id
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при добавлении новости: {str(e)}")
            raise

    def find_similar_news(self, query: str, top_k: int = 5) -> List[NewsItem]:
        """Поиск похожих новостей по запросу с использованием семантического поиска.
        
        Аргументы:
            query: Поисковый запрос
            top_k: Количество возвращаемых результатов
            
        Возвращает:
            Список объектов NewsItem, отсортированных по убыванию релевантности
        """
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self._get_embedding(query)
            
            with self.conn.cursor() as cur:
                # Ищем похожие новости с использованием косинусного расстояния
                cur.execute(
                    """
                    SELECT n.id, n.title, n.content, n.source, 
                           1 - (e.embedding <=> %s::vector) as similarity
                    FROM news n
                    JOIN news_embeddings e ON n.id = e.news_id
                    ORDER BY e.embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (query_embedding.tolist(), query_embedding.tolist(), top_k)
                )
                
                results = []
                for row in cur.fetchall():
                    news_item = NewsItem(
                        id=row[0],
                        title=row[1],
                        content=row[2],
                        source=row[3],
                        similarity=float(row[4])
                    )
                    results.append(news_item)
                
                logger.debug(f"Найдено {len(results)} похожих новостей для запроса: {query[:50]}...")
                return results
                
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих новостей: {str(e)}")
            return []

    def get_news_by_id(self, news_id: int) -> Optional[NewsItem]:
        """Получение новости по ID"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, content, source FROM news WHERE id = %s",
                (news_id,)
            )
            row = cur.fetchone()
            if row:
                return NewsItem(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    source=row[3]
                )
            return None

    def __del__(self):
        """Закрываем соединение при уничтожении объекта"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

# Пример использования
if __name__ == "__main__":
    similar = None  # Initialize similar variable
    try:
        logger.info("Запуск тестового примера работы с RAG базой данных")
        # Создаем экземпляр базы данных
        rag_db = RAGDatabase()
        
        # Добавление тестовых данных
        test_news = [
            ("Новость о технологиях", "Компания выпустила новую версию своего программного обеспечения.", "ИТ-портал"),
            ("Финансовые новости", "Биржевые индексы выросли на фоне позитивных экономических данных.", "Финансовый вестник"),
            ("Спортивные новости", "Футбольная команда одержала победу в важном матче.", "Спорт-экспресс")
        ]
        
        logger.info("Добавление тестовых новостей в базу...")
        for title, content, source in test_news:
            news_id = rag_db.add_news(title, content, source)
            logger.debug(f"Добавлена тестовая новость с ID: {news_id}")
        
        # Поиск похожих новостей
        query = "новые технологии"
        logger.info(f"Выполнение поиска по запросу: {query}")
        similar = rag_db.find_similar_news(query)
        
        # Вывод результатов
        print(f"\nРезультаты поиска по запросу: '{query}'")
        print("-" * 80)
        
        if not similar:
            print("По вашему запросу ничего не найдено.")
        else:
            for i, news in enumerate(similar, 1):
                print(f"{i}. [{news.source}] {news.title}")
                print(f"   Сходство: {news.similarity:.2f}")
                print(f"   {news.content[:100]}...\n")
                
    except Exception as e:
        logger.error(f"Ошибка в тестовом примере: {str(e)}")
    finally:
        logger.info("Завершение работы тестового примера")
    
    # Получение новости по ID
    if similar:
        news_item = rag_db.get_news_by_id(similar[0].id)
        if news_item:
            print(f"\nПолная новость (ID: {news_item.id}):")
            print(f"{news_item.title}\n{news_item.content}")
