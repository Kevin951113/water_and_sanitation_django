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
_LOCAL_KIDS_TUPLES = [
    (1, 'What is water pollution?',
     '<p>When dirty stuff gets into rivers, lakes, or the ocean, animals, plants, and people are affected.</p>',
     '<p>Common sources: factory wastewater, household detergents, plastic trash, oil, and farm chemicals.</p>',
     'Tap me to unlock the fish!', 1, 1),

    (2, 'Why do rainy days matter?',
      '<p>Rain washes street grime into the water — like oil and litter.</p>',
      '<p>During heavy storms, runoff carries microplastics, fertilizers, and animal waste into creeks.</p>',
      'Tap me to unlock the fish!', 1, 0),

    (3, 'How does plastic harm fish?',
     '<p>Fish may mistake tiny plastic bits for food.</p>',
     '<p>Microplastics can remain in their bodies and move up the food chain.</p>',
     'Tap me to unlock the fish!', 1, 0),

    (4, 'What can we do at home?',
     '<p>Don’t pour used oil down the sink — store it for recycling.</p>',
     '<p>Choose eco-friendly cleaners and use less to keep drains safer.</p>',
     'Tap me to unlock the fish!', 1, 0),

    (5, 'What about parks and schools?',
     '<p>Put rubbish in the bin and pick up stray plastic bags and caps.</p>',
     '<p>Storm drains often flow straight to rivers or the sea.</p>',
     'Tap me to unlock the fish!', 1, 0),

    (6, 'Why do animals need clean water?',
     '<p>Fish, shrimp, and frogs live in water — dirty water harms them first.</p>',
     '<p>Healthy streams and seas mean healthier environments for everyone.</p>',
     'Tap me to unlock the fish!', 1, 0),

    (7, 'What is algal bloom?',
     '<p>Too many nutrients make algae “explode” in number.</p>',
     '<p>It reduces oxygen and can suffocate fish. Cut fertilizer runoff.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (8, 'What is sewer overflow?',
     '<p>In big storms, mixed water may be released from treatment plants.</p>',
     '<p>Check public advisories and avoid water play right after storms.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (9, 'Be a Water Helper!',
     '<p>Reduce plastic, recycle, and join a beach or river clean-up.</p>',
     '<p>Share what you learned so more people can protect our water together!</p>',
     'Tap me to unlock the fish!', 4, 0),

    (10, 'Elephants are mostly water',
     '<p>An elephant’s body is about <strong>70%</strong> water — that’s a lot of splash-power!</p>',
     '<p>Water helps carry nutrients, cool the body, and keep blood moving.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (11, 'A lifetime of sips',
     '<p>Across a whole life, a person drinks about <strong>75,000&nbsp;L</strong> of water — like <em>hundreds</em> of bathtubs!</p>',
     '<p>Drinking water keeps our brain focused and our body happy and healthy.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (12, 'Trees breathe out water',
     '<p>One big tree can release around <strong>265&nbsp;L</strong> of water into the air each day!</p>',
     '<p>This is called “transpiration” and it powers the water cycle (clouds and rain!).</p>',
     'Tap me to unlock the fish!', 4, 0),

    (13, 'Tomatoes are juicy water balloons',
     '<p>A tomato is about <strong>95%</strong> water — no wonder it’s so squishy!</p>',
     '<p>Lots of fruits and veggies carry water, making them tasty <em>and</em> hydrating.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (14, 'You are a water hero',
     '<p>Your body is around <strong>66%</strong> water — that’s why you need regular sips.</p>',
     '<p>Water helps you think clearly, move smoothly, and cool down when you play.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (15, 'The sun lifts oceans into the sky',
     '<p>Every day, sunshine evaporates about <strong>one trillion tonnes</strong> of water!</p>',
     '<p>That invisible water vapour later becomes clouds, then raindrops.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (16, 'Your coffee’s hidden water',
     '<p>One cup takes about <strong>140&nbsp;L</strong> of water to grow, process, and brew.</p>',
     '<p>Most of that water goes into farming the coffee plant — choose and sip wisely!</p>',
     'Tap me to unlock the fish!', 4, 0),

    (17, 'Australia’s longest water pipeline',
     '<p>The longest water supply pipeline in Australia is in <strong>Western Australia</strong>.</p>',
     '<p>Pipelines move precious water across long distances to towns and communities.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (18, 'Our biggest river catchment',
     '<p>Australia’s largest catchment is the <strong>Murray–Darling Basin</strong>.</p>',
     '<p>A “catchment” is land where rain drains into streams, rivers, and lakes.</p>',
     'Tap me to unlock the fish!', 4, 0),

    (19, 'Animals that hardly ever drink',
     '<p><strong>Koalas</strong> and <strong>desert rats</strong> can get most of their water from leaves and food.</p>',
     '<p>They still need water inside their bodies — their diets do the heavy lifting!</p>',
     'Tap me to unlock the fish!', 4, 0),
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
                      key=lambda d: d["card_order"])[:6]
        print(f"[kids_cards] source=LOCAL tuples, returning={len(data)} items (limit 4)")
        return data

    qs = list(
        KidsCard.objects.order_by("card_order").values(
            "card_order", "title", "lead_html", "detail_html",
            "hint_text", "read_seconds", "is_starter"
        )[:4]
    )
    print(f"[kids_cards] source=DB, returning={len(qs)} items (limit 4)")
    return qs


# =========================
#  Collectible card data below
# =========================

# Local collectible-card tuples:
# (no, title, aria, img_relative, desc, special, levelCap, levelCur) ---> SS, S, A, B, C
_LOCAL_COLLECT_TUPLES = [
    (1, "Blue Whale", "Whale card", "cards/blue_whale.gif",
     "Largest animal on Earth, a gentle giant that filters tiny krill from the ocean.", "S", 3, 1),

    (2, "Great White Shark", "Great White Shark card", "cards/great_white.gif",
    "Apex ocean hunter—keen senses keep food webs balanced; needs clean, open coasts.", "S", 3, 3),

    (3, "Sharks", "Sharks card", "cards/sharks.gif",
    "From hammerheads to great whites—sharks come in many forms, all needing healthy oceans.", "SS", 3, 3),

    (4, "Whale Shark", "Whale Shark card", "cards/whale_shark.gif",
    "Gentle giant of the sea—feeds on plankton, thrives in clean, warm oceans.", "A", 3, 3),

    (5, "Hammerhead Shark", "Hammerhead Shark card", "cards/hammerhead_shark.gif",
    "With its hammer-shaped head, it scans wide seas—needs healthy reefs to hunt and thrive.", "A", 3, 2),

    (6, "Orca", "Orca card", "cards/orca.gif",
    "The black-and-white apex hunter—social and smart, thrives in clean, rich seas.", "B", 3, 3),


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
