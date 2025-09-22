from django.test import TestCase

# example: unit-level test with monkeypatch to isolate DB / I/O
from main.services import animal_cards_service as svc