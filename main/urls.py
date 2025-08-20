# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("about_water_sanitation/", views.about_water_sanitation, name="about_water_sanitation"),
    path("explore_water_quality/", views.explore_water_quality, name="explore_water_quality"),
    path("future_family_safety/", views.future_family_safety, name="future_family_safety"),
    path("pollution_sources/", views.pollution_sources, name="pollution_sources"),
    path("for_kids_learn_play/", views.for_kids_learn_play, name="for_kids_learn_play"),
]
