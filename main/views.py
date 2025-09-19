from django.shortcuts import render
from django.http import JsonResponse
import json
import folium
from django.views.decorators.http import require_GET
from .services import diving_game_service, animal_map_service , animal_cards_service, future_family_safety_service, home_service, about_water_sanitation_service, pollution_sources_service, pollution_sources_service
from .services.animal_cards_service import fetch_kids_cards, build_collect_cards_json


from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from .services.future_family_safety_service import predict_site, list_sites, health_payload

# Create your views here.
def home(request):
    return render(request, 'water_home.html')

def about_water_sanitation(request):
    return render(request, "about_water_sanitation.html")

def explore_water_quality(request):
    return render(request, "explore_water_quality.html")

# #ranjana - 15/09/2025
# import folium

# def animal_map(request):
#     # Coordinates for Victoria
#     victoria_coords = [-37.4713, 144.7852]

#     # Create map
#     m = folium.Map(location=victoria_coords, zoom_start=6)
#     folium.Marker(
#         location=[-37.8136, 144.9631],
#         popup="Melbourne",
#         icon=folium.Icon(color="blue", icon="info-sign")
#     ).add_to(m)

#     # Get HTML representation of the map
#     map_html = m._repr_html_()

#     return render(request, 'animal_map.html', {'map_html': map_html})

# # end - ranjana

## ranjana - 18/09/2025
# views.py (update animal_map)

"""
import os
import urllib.parse
from django.conf import settings
from .services import animal_map_service

def animal_map(request):
    victoria_coords = [-37.4713, 144.7852]
    victoria_bounds = [[-39.2, 140.9], [-33.9, 150.0]]

    m = folium.Map(location=victoria_coords, zoom_start=6, max_bounds=True)
    m.fit_bounds(victoria_bounds)

    sightings = animal_map_service.get_all_sightings()

    for sighting in sightings:
        lat, lon = sighting.latitude, sighting.longitude
        name = sighting.common_name
        img_filename = f"{name}.png"

        # Path to image file on disk (used by folium)
        file_path = os.path.join(settings.STATICFILES_DIRS[0], "sea-animal", img_filename)

        # If the image doesn't exist, use a default
        #if not os.path.exists(file_path):
            #file_path = os.path.join(settings.STATICFILES_DIRS[0], "sea-animal", "default.png")

        icon = folium.CustomIcon(
            icon_image=file_path,  # Must be actual file path for folium
            icon_size=(50, 50),
            icon_anchor=(25, 25),
        )

        popup = folium.Popup(f"<b>{name}</b>", max_width=200)

        folium.Marker(
            location=[lat, lon],
            popup=popup,
            icon=icon,
        ).add_to(m)

    map_html = m._repr_html_()
    return render(request, 'animal_map.html', {'map_html': map_html})
"""


#--------------------------------------------------------------------


#2025/09/18 Kevin map revise#
from django.contrib.staticfiles import finders
from django.templatetags.static import static

from .services.animal_map_service import get_all_sightings_dict

import os
import re


def _resolve_icon_url(common_name: str) -> str:
    """
    Return a static URL for an icon under static/sea-animal/*.png.
    Tries several filename variants (space/underscore/dash/lowercase); falls back to default.png.
    """
    if not common_name:
        candidates = ["sea-animal/default.png"]
    else:
        base = common_name.strip()
        lower = base.lower()
        candidates = [
            # keep original first (may contain spaces & capitals)
            f"sea-animal/{base}.png",
            f"sea-animal/{base.replace(' ', '_')}.png",
            f"sea-animal/{base.replace(' ', '-')}.png",

            # lowercase variants
            f"sea-animal/{lower}.png",
            f"sea-animal/{lower.replace(' ', '_')}.png",
            f"sea-animal/{lower.replace(' ', '-')}.png",

            # sometimes data already contains underscores/dashes and needs the other
            f"sea-animal/{re.sub(r'[_-]+', ' ', lower)}.png",
            f"sea-animal/{re.sub(r'[_\\s]+', '-', lower)}.png",
            f"sea-animal/{re.sub(r'[-\\s]+', '_', lower)}.png",

            "sea-animal/default.png",
        ]

    for rel in candidates:
        if finders.find(rel):
            return static(rel)

    # Last-resort fallback (even if not found by finders, still return a URL)
    return static("sea-animal/default.png")


def _scan_gallery_from_static():
    """
    Scan collected static files and build a full gallery from sea-animal/*.png.
    This shows ALL species images that exist in static, not just those with sightings.
    """
    results = {}
    # Iterate all static finders and list files
    for f in finders.get_finders():
        for path, storage in getattr(f, "list", lambda *a, **k: [])([]):
            if not path.lower().startswith("sea-animal/"):
                continue
            if not path.lower().endswith(".png"):
                continue

            # path like "sea-animal/Bottlenose dolphin.png"
            filename = os.path.basename(path)
            name_no_ext = os.path.splitext(filename)[0]

            # Convert file name to display name: underscores/dashes -> spaces, title-case
            display_name = re.sub(r"[_-]+", " ", name_no_ext).strip()
            # Keep original capitalization if filename already looks titled; else .title()
            if display_name.islower():
                display_name = display_name.title()

            icon_url = static(path)

            # Use dict to de-duplicate by display_name, keep first found
            results.setdefault(display_name, {
                "common_name": display_name,
                "icon_url": icon_url,
                # You can add more fields later, e.g. "desc"
            })

    # Stable sort by name
    return [results[k] for k in sorted(results.keys(), key=lambda s: s.lower())]


def animal_map(request):
    """
    Render the page shell. The map and markers are drawn on the client side
    by fetching /animal_map/data (JSON).
    """
    return render(request, "animal_map.html")


def animal_map_data(request):
    """
    JSON endpoint for sightings + full gallery.
    Keep original variable names for center/bounds to avoid breaking JS.
    """
    # --- keep these names as requested ---
    victoria_coords = (-37.4713, 144.7852)
    victoria_bounds = [(-39.2, 140.9), (-33.9, 150.0)]

    raw = get_all_sightings_dict()  # list[dict]: sighting_id, latitude, longitude, common_name

    # Build sightings (map markers)
    items = []
    # For quick "focusAnimal": map a species -> first sighting coords
    first_coords_by_name = {}

    for s in raw:
        lat = s.get("latitude")
        lon = s.get("longitude")
        name = (s.get("common_name") or "Unknown").strip()

        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue  # skip invalid coords

        icon_url = _resolve_icon_url(name)

        items.append({
            "id": s.get("sighting_id"),
            "latitude": lat,
            "longitude": lon,
            "common_name": name,
            "icon_url": icon_url,
            "popup_html": f"<strong>{name}</strong>",
        })

        first_coords_by_name.setdefault(name, (lat, lon))

    # Build FULL gallery by scanning static/sea-animal (independent of sightings)
    gallery = _scan_gallery_from_static()

    payload = {
        "meta": {
            "victoria_coords": list(victoria_coords),
            "victoria_bounds": [list(victoria_bounds[0]), list(victoria_bounds[1])],
            "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "tile_attribution": "© OpenStreetMap contributors",
        },
        "items": items,
        "gallery": gallery,  # right-side original-size images (ALL images in static)
        # for front-end focusing to first known sighting when clicking gallery
        "first_coords_by_name": {k: list(v) for k, v in first_coords_by_name.items()},
    }

    resp = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    resp["Cache-Control"] = "public, max-age=300"  # light browser cache (5 min)
    return resp
#--------------------------------------------------------------------


def animal_map(request):
    """
    Render the page shell. The map and markers are drawn on the client side
    by fetching /animal_map/data (JSON).
    """
    return render(request, "animal_map.html")


def animal_map_data(request):
    """
    JSON endpoint for sightings. Frontend fetches this to draw markers.
    Keeps original variable names: victoria_coords, victoria_bounds.
    """
    # --- keep these names the same as your original logic ---
    victoria_coords = (-37.4713, 144.7852)
    victoria_bounds = [(-39.2, 140.9), (-33.9, 150.0)]

    raw = get_all_sightings_dict()  # list[dict]: sighting_id, latitude, longitude, common_name

    items = []
    for s in raw:
        lat = s.get("latitude")
        lon = s.get("longitude")
        name = s.get("common_name") or "Unknown"
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue  # skip invalid coords

        items.append({
            "id": s.get("sighting_id"),
            "latitude": lat,
            "longitude": lon,
            "common_name": name,
            "icon_url": _resolve_icon_url(name),
            "popup_html": f"<strong>{name}</strong>",
        })

    payload = {
        "meta": {
            # expose with the same names so the frontend can reuse existing logic
            "victoria_coords": list(victoria_coords),
            "victoria_bounds": [list(victoria_bounds[0]), list(victoria_bounds[1])],
            "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "tile_attribution": "© OpenStreetMap contributors",
        },
        "items": items,
    }

    resp = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    resp["Cache-Control"] = "public, max-age=300"  # 5 minutes browser cache
    return resp



#--------------------------------------------------------------------
"""
def future_family_safety(request):
    return render(request, "future_family_safety.html")

"""
def future_family_safety(request):
    site_id = (request.GET.get("site_id") or "").strip()
    try:
        horizon_days = max(1, int(request.GET.get("horizon_days", "2")))
    except Exception:
        horizon_days = 2

    ctx = {
        "site_id": site_id,
        "horizon_days": horizon_days,
        "site_options": list_sites(),
    }
    if site_id:
        ctx["result"] = predict_site(site_id=site_id, horizon_days=horizon_days)

    return render(request, "future_family_safety.html", ctx)


def api_sites(request: HttpRequest):
    try:
        return JsonResponse({"sites": list_sites()})
    except Exception as e:
        return JsonResponse({"sites": [], "error": str(e)}, status=500)

def api_family_safety_forecast(request: HttpRequest):
    site_id = request.GET.get("site_id") or ""
    # accept either hours or days; 48h == 2 days
    h_hours = request.GET.get("h") or request.GET.get("hours")
    h_days = request.GET.get("d") or request.GET.get("days")

    if h_hours:
        try:
            import math
            horizon_days = max(1, math.ceil(int(h_hours) / 24))
        except Exception:
            horizon_days = 2
    elif h_days:
        try:
            horizon_days = max(1, int(h_days))
        except Exception:
            horizon_days = 2
    else:
        horizon_days = 2  # default for your 48h page

    if not site_id:
        return JsonResponse({"error": "missing site_id"}, status=400)

    try:
        result = predict_site(site_id=str(site_id), horizon_days=horizon_days)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# --------------------------------------------------------------------
# NEW: Health check endpoint
# --------------------------------------------------------------------
def healthz(request: HttpRequest):
    """Lightweight health check for Nginx/Docker/ELB probes."""
    return JsonResponse(health_payload())


#--------------------------------------------------------------------

def pollution_sources(request):
    return render(request, "pollution_sources.html")

"""
def animal_cards(request):
    return render(request, "for_kids_learn_play.html")
"""

def animal_cards(request):
    return render(request, "animal_cards.html", {"db_cards": fetch_kids_cards(),
                                                        "collect_cards_json": build_collect_cards_json(),})


# def animal_map(request):
#     return render(request, "animal_map.html")



def diving_game(request):
    return render(request, "diving_game.html")
