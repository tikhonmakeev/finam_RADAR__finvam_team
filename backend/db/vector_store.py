from typing import Dict, List, Any, Optional
import logging
import psycopg2
from psycopg2.extras import execute_values
from backend.ai_model.embedder import Embedder
from backend.ai_model.rag_utils import chunk_text

# Настройка логирования
logger = logging.getLogger(__name__)

class VectorStore:
    """Хранилище векторов для эффективного поиска похожих текстовых фрагментов с использованием PostgreSQL и pgvector.
    
    Этот класс отвечает за индексацию и поиск текстовых фрагментов с их векторными
    представлениями, обеспечивая эффективный поиск похожих документов.
    """
    
    def __init__(self, dim: int = 384, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Инициализация хранилища векторов с указанной размерностью и моделью.
        
        Аргументы:
            dim: Размерность эмбеддингов.
            model_name: Название модели для генерации эмбеддингов.
        """
        self.dim = dim
        self.embedder = Embedder(model_name=model_name)
        self.conn = self._get_db_connection()
        self._init_db()
        logger.info(f"Инициализировано хранилище векторов с размерностью: {dim} и моделью: {model_name}")

    def _get_db_connection(self):
        """Создание подключения к базе данных с использованием переменных окружения."""
        return psycopg2.connect(
            dbname="your_db_name",
            user="your_username",
            password="your_password",
            host="localhost",
            port=5432
        )

    def _init_db(self):
        """Инициализация таблиц в базе данных и расширения pgvector."""
        with self.conn.cursor() as cur:
            # Включаем расширение pgvector
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Создаем таблицу новостей
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
            
            # Создаем таблицу фрагментов с векторным полем
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS news_chunks (
                id SERIAL PRIMARY KEY,
                news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding vector({self.dim}) NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
            
            # Создаем индекс для ускорения поиска похожих векторов
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_chunks_embedding 
            ON news_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """)
            
            self.conn.commit()

    def index_news(self, news_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """Индексирует новостную статью, разбивая её на фрагменты и сохраняя эмбеддинги.
        
        Аргументы:
            news_id: Уникальный идентификатор новостной статьи.
            text: Полный текст новостной статьи.
            metadata: Дополнительные метаданные для сохранения вместе со статьей.
        """
        if metadata is None:
            metadata = {}
            
        try:
            # Разбиваем текст на фрагменты
            chunks = chunk_text(text)
            if not chunks:
                logger.warning(f"Не удалось создать фрагменты для новости с ID: {news_id}")
                return
                
            # Генерируем эмбеддинги для каждого фрагмента
            embeddings = self.embedder.embed(chunks)
            
            with self.conn.cursor() as cur:
                # Вставляем новость, если её еще нет
                cur.execute("""
                INSERT INTO news (id, title, content, source)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE 
                SET title = EXCLUDED.title, 
                    content = EXCLUDED.content,
                    source = EXCLUDED.source,
                    updated_at = NOW()
                RETURNING id;
                """, (
                    news_id,
                    metadata.get('title', ''),
                    text,
                    metadata.get('source', 'неизвестно')
                ))
                
                # Подготавливаем данные фрагментов для пакетной вставки
                chunk_data = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_meta = {
                        'chunk_index': i,
                        **{k: v for k, v in metadata.items() if k != 'title' and k != 'source'}
                    }
                    chunk_data.append((
                        news_id,
                        chunk,
                        i,
                        embedding.tolist(),  # Преобразуем numpy массив в список для psycopg2
                        chunk_meta
                    ))
                
                # Удаляем существующие фрагменты для этого news_id
                cur.execute("DELETE FROM news_chunks WHERE news_id = %s", (news_id,))
                
                # Вставляем фрагменты пачкой
                execute_values(
                    cur,
                    """
                    INSERT INTO news_chunks (news_id, chunk_text, chunk_index, embedding, metadata)
                    VALUES %s
                    RETURNING id;
                    """,
                    chunk_data,
                    template="(%s, %s, %s, %s::vector, %s::jsonb)"
                )
                
                self.conn.commit()
                logger.info(f"Проиндексировано {len(chunks)} фрагментов для новости с ID: {news_id}")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при индексации новости {news_id}: {str(e)}")
            raise
            
    def search_similar(self, query: str, top_k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Ищет похожие текстовые фрагменты по запросу с использованием pgvector.
        
        Аргументы:
            query: Текст поискового запроса.
            top_k: Максимальное количество возвращаемых результатов.
            threshold: Минимальный порог схожести (от 0 до 1) для результатов.
            
        Возвращает:
            Список словарей, содержащих похожие фрагменты и их метаданные.
        """
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.embedder.embed_single(query).tolist()
            
            with self.conn.cursor() as cur:
                # Ищем похожие фрагменты с использованием оператора косинусного расстояния pgvector (<=>)
                cur.execute("""
                SELECT 
                    nc.id,
                    nc.news_id,
                    n.title as news_title,
                    n.source as news_source,
                    nc.chunk_text,
                    nc.chunk_index,
                    nc.metadata,
                    1 - (nc.embedding <=> %s::vector) as similarity
                FROM news_chunks nc
                JOIN news n ON n.id = nc.news_id
                WHERE 1 - (nc.embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT %s;
                """, (query_embedding, query_embedding, threshold, top_k))
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'chunk_id': row[0],
                        'news_id': row[1],
                        'news_title': row[2],
                        'news_source': row[3],
                        'text': row[4],
                        'chunk_index': row[5],
                        'metadata': row[6] or {},
                        'score': float(row[7])
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих документов: {str(e)}")
            return []
    
    def get_news_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Получает новостную статью и её фрагменты по ID.
        
        Аргументы:
            news_id: ID новостной статьи для получения.
            
        Возвращает:
            Словарь с данными новостной статьи и её фрагментами, или None, если не найдена.
        """
        try:
            with self.conn.cursor() as cur:
                # Получаем данные новости
                cur.execute("""
                SELECT id, title, content, source, created_at, updated_at
                FROM news
                WHERE id = %s;
                """, (news_id,))
                
                news_row = cur.fetchone()
                if not news_row:
                    return None
                
                # Получаем все фрагменты для этой новости
                cur.execute("""
                SELECT id, chunk_text, chunk_index, metadata, created_at
                FROM news_chunks
                WHERE news_id = %s
                ORDER BY chunk_index;
                """, (news_id,))
                
                chunks = []
                for chunk_row in cur.fetchall():
                    chunks.append({
                        'id': chunk_row[0],
                        'text': chunk_row[1],
                        'index': chunk_row[2],
                        'metadata': chunk_row[3] or {},
                        'created_at': chunk_row[4]
                    })
                
                return {
                    'id': news_row[0],
                    'title': news_row[1],
                    'content': news_row[2],
                    'source': news_row[3],
                    'created_at': news_row[4],
                    'updated_at': news_row[5],
                    'chunks': chunks
                }
                
        except Exception as e:
            logger.error(f"Ошибка при получении новости {news_id}: {str(e)}")
            return None
    
    def delete_news(self, news_id: str) -> bool:
        """Удаляет новостную статью и все её фрагменты по ID.
        
        Аргументы:
            news_id: ID новостной статьи для удаления.
            
        Возвращает:
            True, если статья была удалена, иначе False.
        """
        try:
            with self.conn.cursor() as cur:
                # Это вызовет каскадное удаление всех связанных фрагментов
                # благодаря ограничению внешнего ключа ON DELETE CASCADE
                cur.execute("DELETE FROM news WHERE id = %s", (news_id,))
                deleted = cur.rowcount > 0
                self.conn.commit()
                return deleted
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при удалении новости {news_id}: {str(e)}")
            return False
    
    def __del__(self):
        """Закрывает соединение с базой данных при уничтожении объекта."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")