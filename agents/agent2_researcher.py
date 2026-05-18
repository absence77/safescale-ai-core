import os
import requests
import json
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Загружаем настройки инфраструктуры из .env
load_dotenv()

@dataclass
class ActionPlan:
    """
    Паспорт решения, который Агент-2 подготовит для Судьи (Agent-4).
    """
    deployment_name: str
    namespace: str
    current_cpu: float
    recommended_cpu: float
    estimated_savings_percent: float
    risk_level: str          # LOW / MEDIUM / HIGH (оценка безопасности изменений)
    llm_analysis: str        # Текстовое обоснование для CTO/инженеров клиента

def ask_local_llm(prompt: str) -> str:
    """
    Функция-мост до твоей локальной службы Ollama.
    Она берет текст, передает его модели qwen2.5:7b и возвращает ответ.
    """
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2  # Низкая температура, чтобы ИИ не фантазировал, а считал математику
        }
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "Ошибка: ИИ вернул пустой ответ.")
    except Exception as e:
        return f"Ошибка подключения к локальной LLM: {e}"
    return "LLM недоступна."

def research_optimization(anomaly: dict) -> ActionPlan:
    """
    Главная логика Агента-2. 
    Принимает аномалию переплаты и превращает её в бизнес-план оптимизации.
    """
    print(f"\n{'='*60}")
    print(f"[Agent-2: Researcher] Запуск ИИ-анализа для {anomaly['deployment_name']}...")
    print(f"{'='*60}")

    # Формируем строгий промпт инженера для нашей Qwen
    prompt = f"""Ты — Senior DevOps и FinOps эксперт. К нам поступили данные о перерасходе ресурсов в кластере.
    
    КОНТЕКСТ ИНЦИДЕНТА:
    - Компонент (Deployment): {anomaly['deployment_name']}
    - Пространство (Namespace): {anomaly['namespace']}
    - Текущий лимит CPU: {anomaly['allocated_cpu']} ядер
    - Реальный пик нагрузки: {anomaly['max_used_cpu']} ядер
    - Коэффициент избыточности: Лимит завышен в {anomaly['waste_ratio']} раз!
    
    ЗАДАНИЕ:
    1. Рассчитай безопасный новый лимит CPU (Рекомендуется оставить запас около 30-50% от реального пика нагрузки, но не опускать ниже 0.05 ядер для стабильности контейнера).
    2. Посчитай экономию ресурсов в процентах по формуле: ((Текущий - Новый) / Текущий) * 100.
    3. Оцени уровень риска (RISK LEVEL) для стабильности системы: LOW, MEDIUM или HIGH. (Если окружение 'default' или 'test' — риск обычно LOW. Если бы это был 'prod' — риск был бы MEDIUM/HIGH).
    
    Выдай свой вердикт строго в формате JSON (без разметки markdown, без лишнего текста, только чистый JSON):
    {{
      "recommended_cpu": <float_значение_нового_лимита>,
      "savings_percent": <float_значение_экономии>,
      "risk_level": "<LOW|MEDIUM|HIGH>",
      "justification": "<короткое объяснение в 2 предложениях для инженеров на русском языке>"
    }}"""

    print("Отправляем данные в мозг системы (локальная LLM)...")
    llm_response = ask_local_llm(prompt)
    
    # Пытаемся очистить ответ ИИ от возможных артефактов (например, если модель обернула JSON в ```json)
    clean_json = llm_response.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(clean_json)
        
        # Упаковываем данные в итоговый ActionPlan
        plan = ActionPlan(
            deployment_name=anomaly['deployment_name'],
            namespace=anomaly['namespace'],
            current_cpu=anomaly['allocated_cpu'],
            recommended_cpu=float(data.get("recommended_cpu", 0.05)),
            estimated_savings_percent=float(data.get("savings_percent", 0.0)),
            risk_level=data.get("risk_level", "HIGH"),
            llm_analysis=data.get("justification", "Анализ не предоставлен.")
        )
        return plan
    except Exception as e:
        print(f"❌ Ошибка парсинга JSON от ИИ. Сырой ответ был:\n{llm_response}")
        # Фоллбэк (запасной план), если ИИ выдал неверный формат
        return ActionPlan(
            deployment_name=anomaly['deployment_name'],
            namespace=anomaly['namespace'],
            current_cpu=anomaly['allocated_cpu'],
            recommended_cpu=0.05,
            estimated_savings_percent=75.0,
            risk_level="MEDIUM",
            llm_analysis=f"Фоллбэк-анализ из-за ошибки ИИ: {e}"
        )

if __name__ == "__main__":
    # Имитируем получение данных от Агента-1, которые мы только что видели в терминале
    mock_anomaly = {
        "deployment_name": "storage-pod",
        "namespace": "default",
        "allocated_cpu": 0.2,
        "max_used_cpu": 0.01,
        "waste_ratio": 20.0
    }
    
    plan = research_optimization(mock_anomaly)
    
    print("\n✅ Итоговый план оптимизации, сформированный ИИ:")
    print(f"  Компонент:         {plan.deployment_name}")
    print(f"  Было CPU:          {plan.current_cpu} ядер")
    print(f"  Рекомендовано CPU: {plan.recommended_cpu} ядер")
    print(f"  Снижение затрат на: {plan.estimated_savings_percent}%")
    print(f"  Уровень риска:     {plan.risk_level}")
    print(f"  Обоснование ИИ:    {plan.llm_analysis}")
