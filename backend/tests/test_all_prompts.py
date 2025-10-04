"""
Тестирование всех промптов из директории prompts.
Запускает тесты для каждого промпта с примерами и проверяет корректность ответов.
"""
import os
import sys
import logging
import requests
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

# Добавляем корень проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем URL из .env или используем по умолчанию
LLM_API_URL = os.getenv('LLM_API_URL', 'http://127.0.0.1:11434')

# Тестовые данные для каждого типа промптов
TEST_CASES = {
    'tagger': [
        ("Компания Газпром увеличила добычу газа на 10%", "Нефть и газ"),
        ("Apple представила новый iPhone с искусственным интеллектом", "Информационные технологии"),
        ("Банк России повысил ключевую ставку до 15%", "Финансы"),
        ("В Москве открылся новый торговый центр", "Потребительский сектор"),
        ("Норильский никель сообщил о росте добычи палладия", "Металлы и добыча"),
        ("Сбербанк запустил сервис цифровых платежей", "Финтех"),
    ],
    'comparison': [
        (("Газпром сообщил о росте выручки на 12% в 2024 году.",
          "Газпром отчитался: выручка выросла на 12%, прибыль снизилась на 5%."), "True"),
        (("ЦБ России объявил о снижении ключевой ставки.",
          "Минфин предложил повысить налог на прибыль компаний."), "False"),
    ],
    'market_impact': [
        ("Компания X объявила о рекордной прибыли в 15 млн долларов в этом квартале. Акции компании выросли на 15% после выхода отчета.",
         {"impact_level": "high", "affected_sectors": ["X"]}),
    ],
    'style_news': [
        ("компания газпром увеличила добычу газа на 10% в этом году",
         "Компания Газпром увеличила добычу газа на 10% в этом году."),
    ],
    'update_summary': [
        (("Ранее сообщалось о росте выручки на 10%.",
          "По уточненным данным, выручка выросла на 12%."),
         "По уточненным данным, выручка выросла на 12%."),
    ]
}

def get_fast_model() -> str:
    """Выбираем быструю модель из доступных"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            # Приоритет быстрых моделей
            fast_models = [
                'phi4-mini:latest',
                'llama3.2:1b',
                'llama3.2:3b',
                'llama2',
                'mistral'
            ]

            # Ищем быструю модель из приоритетного списка
            for fast_model in fast_models:
                for available_model in model_names:
                    if fast_model in available_model.lower():
                        logger.info(f"🚀 Выбрана модель: {available_model}")
                        return available_model

            # Если быстрых нет, берем первую доступную
            if model_names:
                logger.info(f"ℹ️ Используем модель: {model_names[0]}")
                return model_names[0]
            
            logger.error("❌ Нет доступных моделей")
            return ""
        
        logger.error(f"❌ Ошибка при получении списка моделей: {response.status_code}")
        return ""
    
    except Exception as e:
        logger.error(f"❌ Ошибка при выборе модели: {e}")
        return ""

async def test_prompt(prompt_type: str, system_prompt: str, test_cases: List[Tuple[Any, Any]], model_name: str):
    """Тестирование конкретного промпта"""
    logger.info(f"\n{'='*80}")
    logger.info(f"ТЕСТИРУЕМ ПРОМПТ: {prompt_type.upper()}")
    logger.info("-" * 80)
    
    success_count = 0
    
    for i, (test_input, expected_output) in enumerate(test_cases, 1):
        try:
            # Инициализируем переменную user_prompt
            user_prompt = ""
            
            # Формируем промпт в зависимости от типа
            if isinstance(test_input, tuple):
                # Для промптов, которые принимают несколько входных значений
                if prompt_type == 'comparison':
                    user_prompt = (
                        f"Новость A: \"{test_input[0]}\"\n"
                        f"Новость B: \"{test_input[1]}\"\n\n"
                        "Выход:\n"
                        '"""'
                    )
                elif prompt_type == 'update_summary':
                    user_prompt = (
                        f"Существующая сводка: \"{test_input[0]}\"\n\n"
                        f"Новая информация: \"{test_input[1]}\"\n\n"
                        "Обновленная сводка:"
                    )
            
            # Если user_prompt не был установлен, используем test_input как есть
            if not user_prompt:
                user_prompt = str(test_input)
            
            # Добавляем системный промпт
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Отправляем запрос к модели
            response = requests.post(
                f"{LLM_API_URL}/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 100,
                    }
                },
                timeout=300
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Ошибка API ({response.status_code}) для теста {i}")
                continue
                
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Очистка ответа
            cleaned_response = response_text.split('\n')[0].strip()
            cleaned_response = cleaned_response.replace('"', '').replace("'", "")
            
            # Проверяем результат
            if isinstance(expected_output, dict):
                # Для словарей проверяем только наличие ключевых полей
                try:
                    result_dict = eval(cleaned_response)
                    is_match = all(k in result_dict and result_dict[k] == v 
                                 for k, v in expected_output.items())
                    result_str = str(result_dict)
                except:
                    is_match = False
                    result_str = cleaned_response
            else:
                is_match = expected_output.lower() in cleaned_response.lower()
                result_str = cleaned_response
            
            if is_match:
                success_count += 1
                logger.info(f"✅ Тест {i}: ОК")
            else:
                logger.warning(f"⚠️ Тест {i}: ОШИБКА")
                logger.info(f"   Ожидалось: {expected_output}")
                logger.info(f"   Получено: {result_str}")
            
            logger.info(f"   Ответ: {result_str[:200]}..." if len(result_str) > 200 else f"   Ответ: {result_str}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении теста {i}: {str(e)}")
    
    logger.info(f"\n📊 ИТОГО: {success_count} из {len(test_cases)} тестов пройдено успешно")
    return success_count == len(test_cases)

async def main():
    """Основная функция тестирования"""
    logger.info("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ВСЕХ ПРОМПТОВ")
    
    # Выбираем модель
    model_name = get_fast_model()
    if not model_name:
        logger.error("❌ Не удалось выбрать модель для тестирования")
        return
    
    # Импортируем все системные промпты
    from ai_model.prompts import (
        prompt_tagger,
        prompt_comparison,
        prompt_market_impact,
        prompt_style_news,
        prompt_update_summary
    )
    
    # Словарь с промптами и их тест-кейсами
    prompts_to_test = {
        'tagger': (prompt_tagger.SYSTEM_PROMPT_TAGGER, TEST_CASES['tagger']),
        'comparison': (prompt_comparison.SYSTEM_PROMPT, TEST_CASES['comparison']),
        'market_impact': (prompt_market_impact.SYSTEM_PROMPT, TEST_CASES['market_impact']),
        'style_news': (prompt_style_news.SYSTEM_PROMPT, TEST_CASES['style_news']),
        'update_summary': (prompt_update_summary.SYSTEM_PROMPT, TEST_CASES['update_summary']),
    }
    
    # Запускаем тесты для каждого промпта
    results = {}
    for prompt_type, (system_prompt, test_cases) in prompts_to_test.items():
        success = await test_prompt(prompt_type, system_prompt, test_cases, model_name)
        results[prompt_type] = success
    
    # Выводим итоговую сводку
    logger.info("\n" + "="*80)
    logger.info("ИТОГОВАЯ СВОДКА")
    logger.info("="*80)
    
    for prompt_type, success in results.items():
        status = "✅ УСПЕШНО" if success else "❌ ОШИБКИ"
        logger.info(f"{prompt_type.upper():<20} {status}")
    
    logger.info("\nТестирование завершено!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nТестирование прервано пользователем.")
    except Exception as e:
        logger.error(f"\nКритическая ошибка: {e}", exc_info=True)
