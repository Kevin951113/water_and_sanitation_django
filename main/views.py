from django.shortcuts import render
from django.http import JsonResponse
import json
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

import os
import urllib.parse
from django.conf import settings
import folium
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


##

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
