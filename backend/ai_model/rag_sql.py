import os
import psycopg2
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass

@dataclass
class NewsItem:
    id: int
    title: str
    content: str
    source: str
    similarity: Optional[float] = None

class RAGDatabase:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self.conn = self._get_connection()
        self._init_tables()

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

    def add_news(self, title: str, content: str, source: str = "unknown") -> int:
        """Добавление новости в базу с генерацией эмбеддинга"""
        with self.conn.cursor() as cur:
            # Вставляем новость
            cur.execute(
                """
                INSERT INTO news (title, content, source)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (title, content, source)
            )
            news_id = cur.fetchone()[0]
            
            # Генерируем и сохраняем эмбеддинг
            embedding = self.model.encode(content).astype(np.float32).tolist()
            
            cur.execute(
                """
                INSERT INTO news_embeddings (news_id, embedding)
                VALUES (%s, %s);
                """,
                (news_id, embedding)
            )
            
            self.conn.commit()
            return news_id

    def find_similar_news(self, query: str, top_k: int = 5, min_similarity: float = 0.5) -> List[NewsItem]:
        """Поиск похожих новостей по смыслу"""
        with self.conn.cursor() as cur:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.model.encode(query).astype(np.float32).tolist()
            
            cur.execute(
                f"""
                SELECT n.id, n.title, n.content, n.source, 
                       1 - (e.embedding <=> %s::vector) AS similarity
                FROM news n
                JOIN news_embeddings e ON n.id = e.news_id
                WHERE 1 - (e.embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT %s;
                """,
                (query_embedding, query_embedding, min_similarity, top_k)
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
                
            return results

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
    # Инициализация
    rag_db = RAGDatabase()
    
    # Добавление тестовой новости
    news_id = rag_db.add_news(
        title="Компания X объявила о сделке",
        content="Сегодня компания X подтвердила заключение сделки на 5 млрд рублей.",
        source="РБК"
    )
    print(f"Добавлена новость с ID: {news_id}")
    
    # Поиск похожих новостей
    query = "Компания X заключила крупное соглашение"
    similar_news = rag_db.find_similar_news(query, top_k=3)
    
    print(f"\n🔎 Похожие новости на запрос: '{query}':")
    for i, news in enumerate(similar_news, 1):
        print(f"\n{i}. {news.title} (сходство: {news.similarity:.2f})")
        print(f"   Источник: {news.source}")
        print(f"   {news.content[:150]}...")
    
    # Получение новости по ID
    if similar_news:
        news_item = rag_db.get_news_by_id(similar_news[0].id)
        if news_item:
            print(f"\n📰 Полная новость (ID: {news_item.id}):")
            print(f"{news_item.title}\n{news_item.content}")
