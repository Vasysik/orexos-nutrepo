import os
import json
import glob
from datetime import datetime, timezone

def parse_orex_manifest(file_path):
    manifest = {}
    with open(file_path, "r", encoding="utf-8") as f:
        in_manifest = False
        for line in f:
            line = line.strip()
            if line == "@manifest":
                in_manifest = True
                continue
            if line == "@end" and in_manifest:
                break
            if in_manifest and ":" in line:
                key, val = line.split(":", 1)
                manifest[key.strip()] = val.strip()
    return manifest

def generate():
    store = {
        "version": 1,
        "generated": datetime.now(timezone.utc).isoformat(),
        "apps": []
    }

    apps_dir = "apps"
    if not os.path.isdir(apps_dir):
        print("No apps/ directory found")
        return

    for app_id in sorted(os.listdir(apps_dir)):
        app_path = os.path.join(apps_dir, app_id)
        if not os.path.isdir(app_path):
            continue

        # Читаем nut.json, если он есть (теперь он опционален или минимален)
        nut_file = os.path.join(app_path, "nut.json")
        nut_data = {}
        if os.path.exists(nut_file):
            with open(nut_file, "r", encoding="utf-8") as f:
                try:
                    nut_data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"  ERROR {app_id}: Invalid nut.json - {e}")
                    continue

        # Определяем исполняемый файл: берем из nut.json или ищем первый .orex
        file_name = nut_data.get("file")
        if not file_name:
            orex_files = glob.glob(os.path.join(app_path, "*.orex"))
            if not orex_files:
                print(f"  SKIP {app_id}: No .orex files found")
                continue
            file_name = os.path.basename(orex_files[0])

        code_file = os.path.join(app_path, file_name)
        if not os.path.exists(code_file):
            print(f"  SKIP {app_id}: Missing code file {file_name}")
            continue

        # Парсим манифест из .orex файла
        orex_manifest = parse_orex_manifest(code_file)
        
        # Считаем размер файла
        code_size = os.path.getsize(code_file)

        # Обрабатываем зависимости (могут быть строкой "app1, app2" в манифесте)
        deps_raw = nut_data.get("deps", orex_manifest.get("deps", ""))
        deps_list = []
        if isinstance(deps_raw, list):
            deps_list = deps_raw
        elif isinstance(deps_raw, str) and deps_raw.strip():
            deps_list = [d.strip() for d in deps_raw.split(",")]

        # Формируем итоговую запись. 
        # Приоритет: 1. nut.json (если задано явно), 2. @manifest в .orex, 3. Дефолтные значения
        entry = {
            "id": nut_data.get("id", orex_manifest.get("id", app_id)),
            "name": nut_data.get("name", orex_manifest.get("name", app_id)),
            "version": nut_data.get("version", orex_manifest.get("version", "0.0.1")),
            "categories": nut_data.get("categories", ["utilities"]), # По дефолту утилиты
            "description": nut_data.get("description", orex_manifest.get("desc", "")),
            "icon": nut_data.get("icon", orex_manifest.get("icon", "📦")),
            "file": file_name,
            "deps": deps_list,
            "author": nut_data.get("author", orex_manifest.get("author", "")),
            "size": code_size,
            "downloadUrl": f"apps/{app_id}/{file_name}"
        }

        store["apps"].append(entry)
        print(f"  OK {entry['id']} v{entry['version']}")

    # Собираем категории
    all_cats = set(c for app in store["apps"] for c in app.get("categories", []))
    store["categories"] = sorted(all_cats)

    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

    print(f"\nGenerated index.json: {len(store['apps'])} apps, {len(store['categories'])} categories")

if __name__ == "__main__":
    generate()
