# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("about_water_sanitation/", views.about_water_sanitation, name="about_water_sanitation"),
    path("explore_water_quality/", views.explore_water_quality, name="explore_water_quality"),
    path("future_family_safety/", views.future_family_safety, name="future_family_safety"),
    path("pollution_sources/", views.pollution_sources, name="pollution_sources"),
    path("animal_cards/", views.animal_cards, name="animal_cards"),
    path("animal_map/", views.animal_map, name="animal_map"),
    path("diving_game/", views.diving_game, name="diving_game"),

    path("api/sites", views.api_sites, name="api_sites"),
    path("api/family-safety/forecast", views.api_family_safety_forecast, name="api_family_safety_forecast"),
    path("healthz", views.healthz, name="healthz"), # New prediction health check endpoint
]
