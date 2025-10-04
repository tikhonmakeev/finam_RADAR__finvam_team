"""
Тестирование интеграции с OpenRouter
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_openrouter():
    """Тестирование базовой функциональности OpenRouter."""
    from backend.ai_model.llm_client import LLMClient
    
    print("🌐 Тестируем OpenRouter интеграцию...")
    
    # Проверяем, что API ключ установлен
    if not os.getenv('MARSH_API_KEY'):
        print("❌ ОШИБКА: Не найден MARSH_API_KEY в переменных окружения")
        print("Добавьте в .env файл:")
        print("MARSH_API_KEY=ваш_ключ_от_openrouter")
        print("OPENROUTER_BASE_URL=https://openrouter.ai/api/v1")
        print("OPENROUTER_MODEL=anthropic/claude-3.5-sonnet")
        print("LLM_PROVIDER=openrouter")
        return
    
    client = LLMClient()
    provider_info = await client.get_provider_info()
    
    print(f"✅ Провайдер: {provider_info['provider']}")
    print(f"📊 Статус: {provider_info['status']}")
    if 'model' in provider_info:
        print(f"🤖 Модель: {provider_info['model']}")
    
    # Тестовый промпт для финансовой аналитики
    test_prompt = """
    Проанализируй следующую финансовую новость и определи:
    1. Основную компанию/сектор
    2. Потенциальное влияние на рынок
    3. Ключевые факты
    
    Новость: "Газпром сообщил о росте добычи газа на 15% в этом квартале. Акции компании выросли на 5%."
    """
    
    system_prompt = """
    Ты — финансовый аналитик. Отвечай структурированно и профессионально.
    """
    
    print("\n🧪 Отправляем запрос...")
    response = await client.generate_response(
        prompt=test_prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=500
    )
    
    if response:
        print(f"✅ Ответ от {provider_info['provider']}:")
        print("-" * 50)
        print(response)
        print("-" * 50)
    else:
        print("❌ Ошибка получения ответа")

async def test_available_models():
    """Тестирование получения списка доступных моделей."""
    from backend.ai_model.openrouter_client import OpenRouterClient
    
    print("\n📋 Получаем доступные модели...")
    
    try:
        client = OpenRouterClient()
        models = await client.get_available_models()
        
        if models:
            print(f"✅ Доступно моделей: {len(models)}")
            print("\nТоп-5 моделей:")
            for i, model in enumerate(models[:5]):
                print(f"  {i+1}. {model.get('id', 'Unknown')}")
                print(f"     Контекст: {model.get('context_length', 'N/A')} токенов")
                print(f"     Поставщик: {model.get('pricing', {}).get('prompt', 'N/A')} / {model.get('pricing', {}).get('completion', 'N/A')}")
        else:
            print("❌ Не удалось получить список моделей")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
    # Раскомментируйте следующую строку, чтобы протестировать получение списка моделей
    # asyncio.run(test_available_models())
