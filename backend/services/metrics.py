from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def cosine_score(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Косинусное сходство между двумя эмбеддингами."""
    return float(cosine_similarity([vec1], [vec2])[0][0])


def jaccard_score(tokens1: list[str], tokens2: list[str]) -> float:
    """Жаккаровское сходство между двумя множествами слов."""
    set1, set2 = set(tokens1), set(tokens2)
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


def combined_score(
    vec1: np.ndarray,
    vec2: np.ndarray,
    tokens1: list[str],
    tokens2: list[str],
    alpha: float = 0.7
) -> float:
    """
    Комбинированный скор: косинусное сходство + Жаккар.
    alpha = вес косинусного сходства, (1-alpha) = вес Жаккара.
    """
    cos = cosine_score(vec1, vec2)
    jac = jaccard_score(tokens1, tokens2)
    return alpha * cos + (1 - alpha) * jac
