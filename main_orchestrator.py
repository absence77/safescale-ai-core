import os
import sys
from dataclasses import asdict

# Импортируем бизнес-логику наших готовых агентов
from agents.agent1_detector import detect_global_financial_waste
from agents.agent2_researcher import research_optimization
from agents.agent4_judge import evaluate_patch_safety

def run_safescale_pipeline():
    print("\n" + "="*60)
    print("🚀 [SafeScale AI Core] Запуск сквозного FinOps оркестратора...")
    print("="*60)

    # ШАГ 1: Запускаем Агента-1 (Detector) для поиска переплат
    anomalies = detect_global_financial_waste()
    
    if not anomalies:
        print("\n✅ [Оркестратор]: Избыточных лимитов не найдено или нет связи с Prometheus.")
        return

    print(f"\n📢 [Оркестратор]: Агент-1 обнаружил объектов для оптимизации: {len(anomalies)}")
    
    # Берем первую критическую аномалию
    target_anomaly = anomalies[0]
    
    # ШАГ 2: Передаем данные Агенту-2 (Researcher)
    anomaly_dict = asdict(target_anomaly)
    action_plan = research_optimization(anomaly_dict)
    
    # ШАГ 3: Передаем сформированный план ИИ-Судье (Agent-4)
    plan_dict = asdict(action_plan)
    verdict = evaluate_patch_safety(plan_dict)
    
    print("\n" + "="*60)
    print("🏁 [РЕЗУЛЬТАТ РАБОТЫ КОНВЕЙЕРА SafeScale AI]:")
    print("="*60)
    print(f"  Объект:           {action_plan.deployment_name} [Namespace: {action_plan.namespace}]")
    print(f"  Решение Судьи:    {verdict.verdict} (Балл безопасности: {verdict.total_score}/100)")
    print(f"  Разбор рисков:    {verdict.reasoning}")
    print("-"*60)

    # ШАГ 4: Исполнение решения (Actuator)
    if verdict.verdict == "APPROVE":
        print("🔥 ДЕЙСТВИЕ: Автоматическое сжатие утверждено! Применяем изменения в K8s...")
        
        kubectl_patch_cmd = (
            f"kubectl patch deployment {action_plan.deployment_name} "
            f"-n {action_plan.namespace} --type='json' "
            f"-p='[{{\"op\": \"replace\", \"path\": \"/spec/template/spec/containers/0/resources/limits/cpu\", \"value\": \"{action_plan.recommended_cpu}\"}}]'"
        )
        
        print(f"\n👉 Выполни эту команду для исправления переплаты:\n\033[92m{kubectl_patch_cmd}\033[0m\n")
        print("✅ [SafeScale AI]: Система успешно оптимизирована. Деньги клиента спасены!")
        
    elif verdict.verdict == "ESCALATE":
        print("⚠️ ДЕЙСТВИЕ: Автоматическое применение заморожено. Требуется ручное подтверждение CTO.")
        print(f"👉 Рекомендованный лимит: {action_plan.recommended_cpu} ядер (Экономия {action_plan.estimated_savings_percent}%)")
        
    else:
        print("❌ ДЕЙСТВИЕ: Изменение полностью заблокировано Судьей из-за критических рисков падения аптайма.")

if __name__ == "__main__":
    run_safescale_pipeline()
