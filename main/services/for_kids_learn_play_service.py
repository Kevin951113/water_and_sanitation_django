from ..models import KidsCard

def fetch_kids_cards():
    return list(
        KidsCard.objects.order_by("card_order").values(
            "card_order","title","lead_html","detail_html",
            "hint_text","read_seconds","is_starter"
        ) #[:1]
    )
