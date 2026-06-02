import os
import sys
from dataclasses import asdict

from agents.agent1_detector import detect_global_financial_waste
from agents.agent2_researcher import research_optimization
from agents.agent4_judge import evaluate_patch_safety
from agents.agent5_executor import apply_gitops_patch

def run_safescale_pipeline():
    print("\n" + "="*60)
    print("🚀 [SafeScale AI Core] Запуск сквозного FinOps оркестратора...")
    print("="*60)

    anomalies = detect_global_financial_waste()
    
    if not anomalies:
        print("\n✅ [Оркестратор]: Избыточных лимитов не найдено или нет связи с Prometheus.")
        return

    print(f"\n📢 [Оркестратор]: Агент-1 обнаружил объектов для оптимизации: {len(anomalies)}")
    
    target_anomaly = anomalies[0]
    anomaly_dict = asdict(target_anomaly)
    action_plan = research_optimization(anomaly_dict)
    
    plan_dict = asdict(action_plan)
    verdict = evaluate_patch_safety(plan_dict)
    
    print("\n" + "="*60)
    print("🏁 [РЕЗУЛЬТАТ РАБОТЫ КОНВЕЙЕРА SafeScale AI]:")
    print("="*60)
    print(f"  Объект:           {action_plan.deployment_name} [Namespace: {action_plan.namespace}]")
    print(f"  Решение Судьи:    {verdict.verdict} (Балл безопасности: {verdict.total_score}/100)")
    print(f"  Разбор рисков:    {verdict.reasoning}")
    print("-"*60)

    if verdict.verdict == "APPROVE":
        success = apply_gitops_patch(
            deployment_name=action_plan.deployment_name,
            namespace=action_plan.namespace,
            recommended_cpu=action_plan.recommended_cpu
        )
        if success:
            print("✅ [SafeScale AI]: Лимит обновлен в репозитории инфраструктуры.")
        else:
            print("⚠️ [SafeScale AI]: GitOps-изменения не применились.")
        
    elif verdict.verdict == "ESCALATE":
        print("⚠️ ДЕЙСТВИЕ: Автоматическое применение заморожено. Требуется ручное подтверждение CTO.")
        print(f"👉 Рекомендованный лимит: {action_plan.recommended_cpu} ядер")
    else:
        print("❌ ДЕЙСТВИЕ: Изменение полностью заблокировано Судьей.")

if __name__ == "__main__":
    run_safescale_pipeline()
