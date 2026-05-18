import os
import requests
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Загружаем настройки из .env
load_dotenv()

@dataclass
class FinOpsTarget:
    deployment_name: str
    namespace: str
    allocated_cpu: float
    max_used_cpu: float
    waste_ratio: float
    severity: str

def get_prometheus_metric(query: str) -> list:
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090")
    try:
        response = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query}, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {}).get("result", [])
    except Exception as e:
        print(f"[Ошибка Prometheus]: {e}")
    return []

def detect_global_financial_waste() -> list[FinOpsTarget]:
    print(f"\n{'='*60}")
    print(f"[Agent-1: Detector] Сканируем ВЕСЬ кластер на финансовые потери...")
    print(f"{'='*60}")

    # Запрашиваем ВСЕ лимиты CPU во всем кластере, без привязки к конкретному namespace
    global_limit_query = 'kube_pod_container_resource_limits{resource="cpu"}'
    limits_data = get_prometheus_metric(global_limit_query)

    if not limits_data:
        print("⚠️ Метрики лимитов в кластере вообще не найдены.")
        return []

    detected_anomalies = []
    
    # Список пространств, которые стартапу оптимизировать не нужно (безопасность бизнеса)
    ignored_namespaces = ["kube-system", "kube-public", "kube-node-lease", "ingress-nginx"]

    for item in limits_data:
        metric_info = item.get("metric", {})
        
        # Динамически вытаскиваем namespace, который нам вернул Prometheus!
        pod_namespace = metric_info.get("namespace", "default")
        
        # Пропускаем системные поды Kubernetes, туда ИИ лезть запрещено
        if pod_namespace in ignored_namespaces:
            continue

        pod_name = metric_info.get("pod", "unknown")
        dep_name = "-".join(pod_name.split("-")[:-2]) if pod_name.count("-") >= 2 else pod_name
        
        # Получаем значение лимита CPU
        limit_value = float(item.get("value", [0, 0])[1])
        if limit_value == 0:
            continue

        # Симулируем пиковое потребление для вычисления потенциала оптимизации
        # (Далее мы свяжем это с реальным графиком нагрузки)
        simulated_max_usage = 0.01 
        waste_ratio = limit_value / simulated_max_usage

        if waste_ratio > 5.0:
            severity = "HIGH (Критический перерасход)"
        elif waste_ratio > 2.0:
            severity = "MEDIUM (Рекомендуется сжатие)"
        else:
            severity = "LOW"

        if waste_ratio > 2.0:
            anomaly = FinOpsTarget(
                deployment_name=dep_name,
                namespace=pod_namespace,
                allocated_cpu=limit_value,
                max_used_cpu=simulated_max_usage,
                waste_ratio=round(waste_ratio, 2),
                severity=severity
            )
            detected_anomalies.append(anomaly)

    return detected_anomalies

if __name__ == "__main__":
    anomalies = detect_global_financial_waste()
    
    print(f"\n[Анализ завершен] Найдено объектов для оптимизации: {len(anomalies)}")
    for index, anomaly in enumerate(anomalies, 1):
        print(f"\n🔥 Цель №{index}:")
        print(f"  Пространство (Namespace): {anomaly.namespace}")
        print(f"  Деплоймент (Компонент):   {anomaly.deployment_name}")
        print(f"  Текущий лимит CPU:        {anomaly.allocated_cpu} ядер")
        print(f"  Коэффициент переплаты:    Ресурсы завышены в {anomaly.waste_ratio} раз!")
        print(f"  Бизнес-статус:            {anomaly.severity}")
