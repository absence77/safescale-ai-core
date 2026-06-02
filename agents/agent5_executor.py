import os
import yaml
import subprocess

def apply_gitops_patch(deployment_name: str, namespace: str, recommended_cpu: float) -> bool:
    print(f"\n{'='*60}")
    print(f"[Agent-5: Executor] 🛡️ Запуск безопасного GitOps-процесса...")
    print(f"{'='*60}")
    
    # Путь к соседнему репозиторию, где лежит вся инфраструктура
    infra_repo_path = "/root/devops-to-ai-platform"
    infra_dir = os.path.join(infra_repo_path, "infrastructure")
    
    if not os.path.exists(infra_dir):
        print(f"❌ Папка инфраструктуры {infra_dir} не найдена!")
        return False

    print(f"🔍 Сканируем папку {infra_dir} на наличие манифеста для {deployment_name}...")
    
    target_file = None
    for root, dirs, files in os.walk(infra_dir):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        docs = list(yaml.safe_load_all(f))
                        for doc in docs:
                            if doc and doc.get('kind') == 'Deployment' and doc.get('metadata', {}).get('name') == deployment_name:
                                target_file = file_path
                                break
                except Exception:
                    continue
        if target_file:
            break

    if not target_file:
        print(f"⚠️ Манифест деплоймента '{deployment_name}' не найден в Git.")
        print(f"👉 Создайте YAML-файл деплоймента в {infra_dir}, чтобы работал GitOps-автомат.")
        return False

    print(f"🎯 Найдено совпадение в Git: {target_file}")
    
    try:
        with open(target_file, 'r') as f:
            doc = yaml.safe_load(f)
            
        containers = doc['spec']['template']['spec']['containers']
        old_limit = containers[0].get('resources', {}).get('limits', {}).get('cpu', 'не задан')
        
        if 'resources' not in containers[0]:
            containers[0]['resources'] = {}
        if 'limits' not in containers[0]['resources']:
            containers[0]['resources']['limits'] = {}
            
        # Меняем старый лимит на новый, высчитанный ИИ
        containers[0]['resources']['limits']['cpu'] = f"{recommended_cpu}"
        
        with open(target_file, 'w') as f:
            yaml.safe_dump(doc, f, default_flow_style=False)
            
        print(f"✅ Манифест успешно обновлен в Git! Было: {old_limit} -> Стало: {recommended_cpu}")
        
        # Создаем ветку и делаем коммит
        print(f"📦 Оформляем изменения в Git...")
        branch_name = f"safescale/optimize-{deployment_name}-{namespace}"
        
        subprocess.run(f"git -C {infra_repo_path} checkout -b {branch_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(f"git -C {infra_repo_path} add .", shell=True)
        subprocess.run(f"git -C {infra_repo_path} commit -m 'finops(ai): optimize cpu limits for {deployment_name} in {namespace}'", shell=True, stdout=subprocess.DEVNULL)
        
        print(f"\n🚀 [SafeScale AI GitOps]: Изменения зафиксированы в ветке: \033[94m{branch_name}\033[0m")
        return True

    except Exception as e:
        print(f"❌ Ошибка при обновлении манифеста: {e}")
        return False
