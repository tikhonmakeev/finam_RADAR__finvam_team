from typing import List, Union, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class Embedder:
    """Класс для генерации эмбеддингов текста с использованием sentence-transformers.
    
    Этот класс предоставляет методы для генерации эмбеддингов текста с использованием
    предобученных моделей sentence transformer. Поддерживает как одиночные тексты, так и пакетную обработку.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Инициализация эмбеддера с предобученной моделью.
        
        Аргументы:
            model_name: Название предобученной модели для генерации эмбеддингов.
        """
        self.model = SentenceTransformer(model_name)
        logger.info(f"Инициализирован Embedder с моделью: {model_name}")
        self.dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Инициализирован эмбеддер с моделью {model_name} и размерностью {self.dim}")

    def embed(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """Генерирует эмбеддинги для одного текста или списка текстов.
        
        Аргументы:
            texts: Одиночная строка текста или список строк для преобразования в эмбеддинги.
            batch_size: Количество текстов для обработки в одном пакете.
            
        Возвращает:
            Массив numpy с эмбеддингами формы (количество_текстов, размерность_эмбеддинга).
            Для одного текста возвращает двумерный массив формы (1, размерность_эмбеддинга).
        """
        if isinstance(texts, str):
            texts = [texts]
            
        if not texts:
            logger.warning("Получен пустой список текстов в методе embed()")
            return np.array([])
            
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings
            
        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддингов: {str(e)}")
            raise

    def embed_single(self, text: str) -> np.ndarray:
        """Генерация эмбеддинга для одного текста.
        
        Аргументы:
            text: Текст для векторизации.
            
        Возвращает:
            Векторное представление текста.
        """
        return self.embed([text])[0] if text else np.zeros(self.dim)

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Вычисляет косинусную близость между двумя эмбеддингами.
        
        Аргументы:
            emb1: Первый вектор эмбеддинга.
            emb2: Второй вектор эмбеддинга.
            
        Возвращает:
            Косинусная близость между эмбеддингами (диапазон: от -1 до 1).
            
        Исключения:
            ValueError: Если входные массивы имеют разную форму или не являются одномерными.
        """
        if emb1.shape != emb2.shape:
            raise ValueError(f"Несовпадение размерностей: {emb1.shape} и {emb2.shape}")
            
        if emb1.ndim != 1 or emb2.ndim != 1:
            raise ValueError("Входные массивы должны быть одномерными")
            
        # Вычисляем скалярное произведение и нормы векторов
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        # Избегаем деления на ноль
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))

    def search(self, query: np.ndarray, vectors: np.ndarray, top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """Поиск k ближайших соседей для запросных векторов.
        
        Аргументы:
            query: Запросные векторы формы (n_запросов, размерность).
            vectors: Векторы для поиска формы (n_векторов, размерность).
            top_k: Количество ближайших соседей для каждого запроса.
            
        Возвращает:
            Список списков результатов поиска. Каждый внутренний список содержит
            до top_k словарей с ключами 'score' (оценка сходства) и 'meta' (метаданные).
        """
        if len(query.shape) == 1:
            query = query.reshape(1, -1)
        
        # Вычисляем косинусное сходство между запросными векторами и векторами для поиска
        scores = np.dot(query, vectors.T)
        
        # Нормализуем векторы, если они еще не нормализованы
        query = query / np.linalg.norm(query, axis=1, keepdims=True)
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        scores = np.dot(query, vectors.T)
        
        # Получаем индексы top_k ближайших соседей для каждого запроса
        top_k_indices = np.argsort(-scores, axis=1)[:, :top_k]
        
        # Обрабатываем результаты для каждого запроса
        results = []
        for i in range(query.shape[0]):
            row = []
            for idx in top_k_indices[i]:
                score = scores[i, idx]
                row.append({
                    "score": float(score),  # Преобразуем в нативный float для сериализации
                    "meta": {}  # Метаданные не переданы, поэтому используем пустой словарь
                })
            results.append(row)
        
        return results