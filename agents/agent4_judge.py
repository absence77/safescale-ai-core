import os
import requests
import json
from dataclasses import dataclass
from dotenv import load_dotenv
import anthropic  # Официальный SDK Anthropic

# Загружаем настройки из .env
load_dotenv()

@dataclass
class JudgeVerdict:
    safety_score: int
    risk_score: int
    total_score: int
    verdict: str
    reasoning: str

def ask_anthropic(prompt: str, api_key: str) -> str:
    """Запрос к облачной Claude через официальный SDK"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Используем актуальную модель Claude 3.5 Haiku
        message = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"⚠️ Ошибка официального Anthropic SDK: {e}")
        return ""

def ask_local_ollama(prompt: str) -> str:
    """Запрос к твоей локальной Ollama"""
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        res = requests.post(url, json={"model": model, "prompt": prompt, "stream": False}, timeout=30)
        if res.status_code == 200:
            return res.json().get("response", "")
    except Exception as e:
        print(f"❌ Ошибка локальной LLM: {e}")
        return ""

def evaluate_patch_safety(action_plan: dict) -> JudgeVerdict:
    print(f"\n{'='*60}")
    print(f"[Agent-4: Judge] 🐙 Проверка плана безопасности через Claude API...")
    print(f"{'='*60}")

    system_rules = """Ты — скептический Senior SRE архитектор, проверяющий планы оптимизации ресурсов.
    Оцени предложенный план по следующим критериям (от 0 до 100):
    1. SAFETY (Безопасность): Не упадет ли сервис? 100 = полностью безопасно, 0 = гарантированный сбой.
    2. RISK (Риск урезания): Насколько критично окружение? (В test/default — риск низкий, в prod — высокий).
    
    ПРАВИЛА ВЕРДИКТА:
    - Итоговый балл (total_score) >= 70 -> APPROVE.
    - Итоговый балл 50-69 -> ESCALATE.
    - Итоговый балл < 50 -> REJECT.
    
    Ответь СТРОГО в формате чистого JSON, не используй разметку markdown (не пиши ```json):
    {
      "safety_score": <int>,
      "risk_score": <int>,
      "total_score": <int>,
      "verdict": "<APPROVE|REJECT|ESCALATE>",
      "reasoning": "<объяснение на русском языке в 2 предложениях>"
    }"""

    prompt = f"{system_rules}\n\nПЛАН ДЛЯ АНАЛИЗА:\n{json.dumps(action_plan, ensure_ascii=False)}"

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Железобетонная проверка префикса ключа
    if api_key and api_key.startswith("sk-ant-"):
        raw_response = ask_anthropic(prompt, api_key)
        if not raw_response:
            print("Локальный бэкап: Облако недоступно, переключаюсь на Ollama Qwen...")
            raw_response = ask_local_ollama(prompt)
    else:
        print("Используем локальный бесплатный ИИ-движок Qwen...")
        raw_response = ask_local_ollama(prompt)

    # Строка склеена намертво в один ряд, разрывов больше не будет
    clean_json = raw_response.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(clean_json)
        return JudgeVerdict(
            safety_score=int(data.get("safety_score", 50)),
            risk_score=int(data.get("risk_score", 50)),
            total_score=int(data.get("total_score", 50)),
            verdict=data.get("verdict", "ESCALATE"),
            reasoning=data.get("reasoning", "Успешно распарсено.")
        )
    except Exception as e:
        print(f"❌ Ошибка парсинга JSON от ИИ. Сырой ответ был:\n{raw_response}")
        return JudgeVerdict(50, 50, 50, "ESCALATE", f"Ошибка валидации данных: {e}")

if __name__ == "__main__":
    mock_plan = {
        "deployment_name": "storage-pod",
        "namespace": "default",
        "current_cpu": 0.2,
        "recommended_cpu": 0.06,
        "estimated_savings_percent": 70.0,
        "risk_level": "LOW"
    }

    verdict = evaluate_patch_safety(mock_plan)
    
    print("\n⚖️ ВЕРДИКТ CLAUDE С ПРЕДОХРАНИТЕЛЕМ:")
    print(f"  Оценка безопасности: {verdict.safety_score}/100")
    print(f"  Оценка рисков:       {verdict.risk_score}/100")
    print(f"  ИТОГОВЫЙ БАЛЛ:       {verdict.total_score}/100")
    print(f"  РЕШЕНИЕ СИСТЕМЫ:     {verdict.verdict}")
    print(f"  Критический разбор:  {verdict.reasoning}")
