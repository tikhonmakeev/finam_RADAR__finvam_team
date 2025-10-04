import json
import os
from pathlib import Path
from typing import Dict

import httpx

# Загружаем промпт
PROMPT_PATH = Path(__file__).parent / "prompts" / "prompt_comparison.txt"
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()

# URL локальной LLM (например, Ollama или vLLM)
LLM_URL = os.getenv("LLM_URL", "http://localhost:8001/v1/chat/completions")

async def compare_news(news1: str, news2: str) -> Dict:
    """
    Сравнение двух новостей через LLM и prompt_comparison.
    Возвращает словарь с выводом модели.
    """
    prompt = PROMPT_TEMPLATE.format(
        news1=news1.strip(),
        news2=news2.strip()
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            LLM_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": "qwen2.5:7b",
                "messages": [
                    {"role": "system", "content": "Ты эксперт по анализу новостей."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }
        )

    data = response.json()
    output = data["choices"][0]["message"]["content"]

    try:
        # Можно сразу пытаться парсить JSON, если промпт заставляет LLM выдавать JSON
        return json.loads(output)
    except Exception:
        # Если не JSON — вернем текст
        return {"result": output}


if __name__ == "__main__":
    import asyncio

    news_a = "Компания X подтвердила сделку на 5 миллиардов рублей."
    news_b = "Компания X объявила о заключении соглашения стоимостью 5 млрд."
    result = asyncio.run(compare_news(news_a, news_b))
    print("📊 Сравнение новостей:")
    print(result)
