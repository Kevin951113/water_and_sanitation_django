from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.http import require_GET
from .services import for_kids_learn_play_service, future_family_safety_service, home_service, about_water_sanitation_service, pollution_sources_service, pollution_sources_service
from .services.for_kids_learn_play_service import fetch_kids_cards


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
def for_kids_learn_play(request):
    return render(request, "for_kids_learn_play.html")
"""

def for_kids_learn_play(request):
    return render(request, "for_kids_learn_play.html", {"db_cards": fetch_kids_cards()})