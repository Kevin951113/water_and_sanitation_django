import json, os
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def vite_asset(entry: str):
    # entry is something like "main.jsx" or "index.html" → look up the JS it maps to
    manifest_path = os.path.join(settings.BASE_DIR, "main", "static", "treasure", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Vite uses the source filename as the key (e.g., "main.jsx")
    if entry not in manifest:
        # also try with './' prefix just in case
        entry2 = "./" + entry.lstrip("./")
        if entry2 in manifest:
            entry = entry2
        else:
            raise KeyError(f"{entry} not found in Vite manifest")

    file_path = manifest[entry]["file"]  # e.g., "assets/main-3c1d7a5f.js"
    return settings.STATIC_URL.rstrip("/") + "/treasure/" + file_path
