from typing import List, Sequence, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


# Конфигурация модели для эмбеддингов
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder:
    """Класс для работы с текстовыми эмбеддингами с использованием Sentence Transformers.
    
    Атрибуты:
        model: Модель SentenceTransformer для генерации эмбеддингов.
        dim: Размерность выходных эмбеддингов.
    """
    def __init__(self, model_name: str = EMBED_MODEL_NAME) -> None:
        """Инициализация Embedder с предобученной моделью.
        
        Args:
            model_name (str): Название предобученной модели для эмбеддингов.
                            По умолчанию используется многоязычная модель.
        """
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        print(f"Инициализирован эмбеддер с размерностью {self.dim}")

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Генерация эмбеддингов для последовательности текстов.
        
        Args:
            texts (Sequence[str]): Последовательность текстовых строк для векторизации.
            
        Returns:
            np.ndarray: Нормализованные эмбеддинги формы (количество_текстов, размерность_эмбеддинга).
            
        Пример:
            >>> embedder = Embedder()
            >>> embeddings = embedder.embed(["Пример текста", "Еще один текст"])
            >>> embeddings.shape
            (2, 384)  # Для модели с размерностью 384
        """
        if not texts:
            return np.array([])
            
        embs = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # Автоматическая нормализация для косинусного сходства
        )
        return embs

    def embed_one(self, text: str) -> np.ndarray:
        """Генерация эмбеддинга для одного текста.
        
        Args:
            text (str): Входной текст для векторизации.
            
        Returns:
            np.ndarray: Нормализованный вектор эмбеддинга.
            
        Примечание:
            Является оберткой над методом embed() для удобства работы с одиночными текстами.
        """
        return self.embed([text])[0] if text else np.zeros(self.dim)


class FaissIndex:
    """Обертка над FAISS индексом для эффективного поиска похожих векторов.
    
    Атрибуты:
        dim (int): Размерность векторов в индексе.
        index: FAISS индекс для поиска похожих векторов.
        metadatas: Список метаданных, соответствующих индексированным векторам.
    """
    def __init__(self, dim: int) -> None:
        """Инициализация FAISS индекса.
        
        Args:
            dim (int): Размерность индексируемых векторов.
            
        Примечание:
            Использует косинусное сходство через скалярное произведение нормализованных векторов.
        """
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # Скалярное произведение для нормализованных векторов = косинусное сходство
        self.metadatas: List[Dict[str, Any]] = []
        print(f"Инициализирован FAISS индекс с размерностью {dim}")

    def add(self, vectors: np.ndarray, metadatas: List[Dict[str, Any]]) -> None:
        """Добавление векторов и соответствующих метаданных в индекс.
        
        Args:
            vectors (np.ndarray): Массив векторов для добавления в индекс.
            metadatas (List[Dict[str, Any]]): Список словарей с метаданными для каждого вектора.
            
        Исключения:
            AssertionError: Если размерность векторов не соответствует размерности индекса.
            
        Пример:
            >>> index = FaissIndex(384)
            >>> vectors = np.random.rand(10, 384).astype('float32')
            >>> metadatas = [{"id": i} for i in range(10)]
            >>> index.add(vectors, metadatas)
        """
        if len(vectors) == 0:
            return
            
        assert vectors.shape[1] == self.dim, \
            f"Размерность вектора {vectors.shape[1]} не соответствует размерности индекса {self.dim}"
            
        self.index.add(vectors)
        self.metadatas.extend(metadatas)

    def search(self, query: np.ndarray, top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """Поиск k ближайших соседей для запросных векторов.
        
        Args:
            query (np.ndarray): Запросные векторы формы (n_запросов, размерность).
            top_k (int): Количество ближайших соседей для каждого запроса.
            
        Returns:
            List[List[Dict[str, Any]]]: Список списков результатов поиска. Каждый внутренний список содержит
                                     до top_k словарей с ключами 'score' (оценка сходства) и 'meta' (метаданные).
                                     
        Пример:
            >>> index = FaissIndex(384)
            >>> query_vector = np.random.rand(1, 384).astype('float32')
            >>> results = index.search(query_vector, top_k=3)
            >>> for result in results[0]:
            ...     print(f"Сходство: {result['score']:.3f}, ID: {result['meta']['id']}")
        """
        if len(query.shape) == 1:
            query = query.reshape(1, -1)
            
        # Выполняем поиск
        scores, ids = self.index.search(query, top_k)
        results = []
        
        # Обрабатываем результаты для каждого запроса
        for i in range(query.shape[0]):
            row = []
            # Обрабатываем каждый найденный результат
            for score, idx in zip(scores[i], ids[i]):
                if idx < 0 or idx >= len(self.metadatas):  # Пропускаем недопустимые индексы
                    continue
                meta = self.metadatas[idx]
                row.append({
                    "score": float(score),  # Преобразуем в нативный float для сериализации
                    "meta": meta
                })
            results.append(row)
            
        return results