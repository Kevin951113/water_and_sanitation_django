# animal_map_service.py

from ..models import AnimalSighting

def get_all_sightings():
    return AnimalSighting.objects.all()      