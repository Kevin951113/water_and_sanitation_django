from django.conf import settings
import os
import json
from ..models import KidsCard


try:
    from ..models import KidsCollectCard as _KidsCollectCard  # optional model
except Exception:
    _KidsCollectCard = None

# ===== Switch here =====
# True  -> always use local tuples (no DB/RDS calls)
# False -> always use database
# None  -> fall back to USE_LOCAL_KIDS_CARDS or settings.DEBUG
LOCAL_CARDS_OVERRIDE = True
# =======================

# ---- Local fallback data (tuples -> dicts) ----

_LOCAL_KIDS_TUPLES =[
    (1, 'Water inside an elephant',
     '<p>About 70% of an elephant is water.</p>',
     '<p>This water helps with blood flow, cooling, and moving nutrients.</p>',
     'Tap me to unlock the card!', 1, 0),

    (2, 'How watery is a tomato?',
      '<p>About 95% of a tomato is water.</p>',
      '<p>That’s why tomatoes are so juicy.</p>',
      'Tap me to unlock the card!', 1, 0),

    (3, 'Water in our bodies',
     '<p>About 66% of the human body is water.</p>',
     '<p>It’s in our brain, blood, and organs.</p>',
     'Tap me to unlock the card!', 1, 0),

    (4, 'Longest water pipeline in Australia',
     '<p>The longest water supply pipeline is in Western Australia.</p>',
     '<p>It carries water long distances to drier areas.</p>',
     'Tap me to unlock the card!', 1, 0),

    (5, 'Where at home uses the most water?',
     '<p>The bathroom uses the most water at home.</p>',
     '<p>Short showers and turning off taps can save a lot.</p>',
     'Tap me to unlock the fish!', 1, 0),

    (6, 'Who lacks safe drinking water?',
     '<p>About 1 in 4 people lack safe drinking water.</p>',
     '<p>Clean water projects help families stay healthy.</p>',
     'Tap me to unlock the card!', 1, 0),

    (7, 'Sea turtles and plastic',
     '<p>About 52% of sea turtles have eaten plastic.</p>',
     '<p>Plastic makes them sick and comes from pollution.</p>',
     'Tap me to unlock the card!', 1, 0),

    (8, 'Whale sharks and plastic',
     '<p>A whale shark may swallow about 137 pieces of plastic every hour.</p>',
     '<p>They can’t tell plastic from food while filtering water.</p>',
     'Tap me to unlock the card!', 1, 0),

    (9, 'Sharks and mercury',
     '<p>About 25% of sharks have unsafe mercury levels.</p>',
     '<p>Pollution builds up in the fish they eat.</p>',
     'Tap me to unlock the card!', 1, 0)
]


def _as_dict(row):
    """Convert a tuple into a dict that matches Django .values() output."""
    return {
        "card_order": row[0],
        "title": row[1],
        "lead_html": row[2],
        "detail_html": row[3],
        "hint_text": row[4],
        "read_seconds": row[5],
        "is_starter": bool(row[6]),
    }

def _use_local_data() -> bool:
    """
    Decide whether to use local tuples instead of hitting the DB.
    Priority:
      1) LOCAL_CARDS_OVERRIDE (True/False/None) defined in this file.
      2) settings.USE_LOCAL_KIDS_CARDS (truthy strings like "1", "true", "yes" allowed).
      3) settings.DEBUG (default fallback).
    Prints a line for the exact branch taken.
    """
    override = LOCAL_CARDS_OVERRIDE
    if override is not None:
        print(f"[kids_cards] decision: LOCAL_CARDS_OVERRIDE={override} -> use_local={bool(override)}")
        return bool(override)

    val = getattr(settings, "USE_LOCAL_KIDS_CARDS", None)
    if val is not None:
        # Accept env-style strings like "1", "true", "yes"
        if isinstance(val, str):
            parsed = val.strip().lower() in {"1", "true", "t", "yes", "y"}
        else:
            parsed = bool(val)
        print(f"[kids_cards] decision: settings.USE_LOCAL_KIDS_CARDS={val!r} (parsed={parsed}) -> use_local={parsed}")
        return parsed

    debug = bool(getattr(settings, "DEBUG", False))
    print(f"[kids_cards] decision: settings.DEBUG={debug} -> use_local={debug}")
    return debug

def fetch_kids_cards():
    """
    Dev/local: return static JSON-like data to avoid RDS costs.
    Production: query the DB (keeps the 4-item limit for the page).
    Also prints the chosen source and count.
    """
    use_local = _use_local_data()

    if use_local:
        data = sorted((_as_dict(t) for t in _LOCAL_KIDS_TUPLES),
                      key=lambda d: d["card_order"])[:9]
        print(f"[kids_cards] source=LOCAL tuples, returning={len(data)} items (limit 9)")
        return data

    qs = list(
        KidsCard.objects.order_by("card_order").values(
            "card_order", "title", "lead_html", "detail_html",
            "hint_text", "read_seconds", "is_starter"
        )[:9]
    )
    print(f"[kids_cards] source=DB, returning={len(qs)} items (limit 4)")
    return qs


# =========================
#  Collectible card data below
# =========================

# Local collectible-card tuples:
# (no, title, aria, img_relative, desc, special, levelCap, levelCur) ---> SS, S, A, B, C
_LOCAL_COLLECT_TUPLES = [

    (1, "Elephant", "Elephant card", "cards/elephant.gif",
    "The gentle giant of the land—family-centered, needs vast grasslands and plenty of water.", "B", 3, 3),


    (2, "Blue Whale", "Whale card", "cards/blue_whale.gif",
     "Largest animal on Earth, a gentle giant that filters tiny krill from the ocean.", "S", 3, 1),

    (3, "Great White Shark", "Great White Shark card", "cards/great_white.gif",
    "Apex ocean hunter—keen senses keep food webs balanced; needs clean, open coasts.", "S", 3, 3),

    (4, "Fin Whale", "Fin Whale card", "cards/fin_whale.gif",
    "The sleek ‘greyhound of the sea’—second largest whale, feeds on krill in vast oceans.", "A", 3, 3),

    (5, "Hammerhead Shark", "Hammerhead Shark card", "cards/hammerhead_shark.gif",
    "With its hammer-shaped head, it scans wide seas—needs healthy reefs to hunt and thrive.", "A", 3, 2),

    (6, "Orca", "Orca card", "cards/orca.gif",
    "The black-and-white apex hunter—social and smart, thrives in clean, rich seas.", "SS", 3, 1),

    (7, "Sea Turtle", "Sea Turtle card", "cards/sea_turtle.gif",
    "Ancient ocean traveler—returns to beaches to nest, needs clean seas and safe shores.", "S", 3, 2),

    (8, "Whale Shark", "Whale Shark card", "cards/whale_shark.gif",
    "Gentle giant of the sea—feeds on plankton, thrives in clean, warm oceans.", "A", 3, 3),

    (9, "Sharks", "Sharks card", "cards/sharks.gif",
    "From hammerheads to great whites—sharks come in many forms, all needing healthy oceans.", "SS", 3, 3),
]

def _static_url(path: str) -> str:
    """
    Build a STATIC_URL-based path. If already an http(s) URL or absolute path
    starting with '/', return as-is.
    """
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = getattr(settings, "STATIC_URL", "/static/")
    return f"{base}{path.lstrip('/')}"

def _collect_as_dict(row):
    """Convert a local collectible tuple into the shape expected by the front-end."""
    return {
        "no": row[0],
        "title": row[1],
        "aria": row[2],
        "img": _static_url(row[3]),
        "desc": row[4],
        "special": row[5],
        "levelCap": int(row[6]),
        "levelCur": int(row[7]),
    }

def fetch_collect_cards(limit: int | None = None):
    """
    Return a list[dict] for collectible cards.
    - If _use_local_data() is True, use _LOCAL_COLLECT_TUPLES.
    - Otherwise, if the optional _KidsCollectCard model exists, query the DB.
      (Suggested model fields: no/title/aria/img or image_url/desc/special/levelCap/levelCur)
    """
    use_local = _use_local_data()
    items = []

    if use_local or _KidsCollectCard is None:
        items = [_collect_as_dict(t) for t in _LOCAL_COLLECT_TUPLES]
        src = "LOCAL"
    else:
        # Accommodate multiple possible field names to keep modeling flexible
        values = list(_KidsCollectCard.objects.order_by("no").values(
            "no", "title", "aria", "img", "image_url", "desc", "description",
            "special", "levelCap", "levelCur", "level_cap", "level_cur"
        ))
        for v in values:
            img = v.get("img") or v.get("image_url") or ""
            desc = v.get("desc") or v.get("description") or ""
            level_cap = v.get("levelCap", v.get("level_cap", 3))
            level_cur = v.get("levelCur", v.get("level_cur", 1))
            items.append({
                "no": v.get("no"),
                "title": v.get("title"),
                "aria": v.get("aria") or f"{v.get('title', 'Card')} card",
                "img": _static_url(img),
                "desc": desc,
                "special": v.get("special") or "S",
                "levelCap": int(level_cap or 3),
                "levelCur": int(level_cur or 1),
            })
        src = "DB"

    if limit is not None and isinstance(limit, int) and limit > 0:
        items = items[:limit]

    print(f"[kids_cards] collect_cards source={src}, count={len(items)}")
    return items

def build_collect_cards_json(limit: int | None = None) -> str:
    """
    Produce a JSON string for the template's
    `<script id="collectCardsData" type="application/json">`.
    """
    data = fetch_collect_cards(limit=limit)
    return json.dumps(data, ensure_ascii=False)
