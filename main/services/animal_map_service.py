# animal_map_service.py

from django.core.cache import cache
from ..models import AnimalSighting

CACHE_KEY = "all_sightings_json"
CACHE_TTL = 60 * 60 * 12  # 12 hours

def get_all_sightings_dict():
    """
    Return a list[dict] that is safe for JSON serialization.
    Keep only fields the frontend needs for the map.
    """
    data = cache.get(CACHE_KEY)
    if data is None:
        # NOTE: keep keys consistent with your DB columns
        data = list(
            AnimalSighting.objects.values(
                "sighting_id", "latitude", "longitude", "common_name"
            )
        )
        cache.set(CACHE_KEY, data, timeout=CACHE_TTL)
        #print("Cached AnimalSightings:", data[:3])
    #else:
        #print("Loaded AnimalSightings from cache:", data[:3])
    return data

def clear_sightings_cache():
    """Manual cache invalidation (also call from signals on save/delete)."""
    cache.delete(CACHE_KEY)

  