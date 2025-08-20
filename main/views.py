from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.http import require_GET
from .services import for_kids_learn_play_service, future_family_safety_service, home_service, about_water_sanitation_service, pollution_sources_service, pollution_sources_service

# Create your views here.
def home(request):
    return render(request, 'water_home.html')

def about_water_sanitation(request):
    return render(request, "about_water_sanitation.html")

def explore_water_quality(request):
    return render(request, "explore_water_quality.html")

def future_family_safety(request):
    return render(request, "future_family_safety.html")


def pollution_sources(request):
    return render(request, "pollution_sources.html")


def for_kids_learn_play(request):
    return render(request, "for_kids_learn_play.html")