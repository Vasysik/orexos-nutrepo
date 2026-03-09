import os
import json
from datetime import datetime, timezone

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

        nut_file = os.path.join(app_path, "nut.json")
        if not os.path.exists(nut_file):
            print(f"  SKIP {app_id}: no nut.json")
            continue

        with open(nut_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  ERROR {app_id}: {e}")
                continue

        code_file = os.path.join(app_path, data.get("file", ""))
        if not os.path.exists(code_file):
            print(f"  SKIP {app_id}: missing code file {data.get('file')}")
            continue

        with open(code_file, "r", encoding="utf-8") as f:
            code_content = f.read()

        entry = {
            "id": data.get("id", app_id),
            "name": data.get("name", app_id),
            "version": data.get("version", "0.0.1"),
            "categories": data.get("categories", []),
            "description": data.get("description", ""),
            "icon": data.get("icon", "📦"),
            "file": data.get("file", ""),
            "deps": data.get("deps", []),
            "author": data.get("author", ""),
            "size": len(code_content.encode("utf-8")),
            "downloadUrl": f"apps/{app_id}/{data['file']}"
        }

        store["apps"].append(entry)
        print(f"  OK {app_id} v{entry['version']}")

    # Собираем все уникальные категории
    all_cats = set()
    for app in store["apps"]:
        for c in app.get("categories", []):
            all_cats.add(c)
    store["categories"] = sorted(all_cats)

    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

    print(f"\nGenerated index.json: {len(store['apps'])} apps, "
          f"{len(store['categories'])} categories")

if __name__ == "__main__":
    generate()
