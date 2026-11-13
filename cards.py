"""Version-controlled, read-only catalogue of issuer rules. No user data is saved here."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "card_catalog" / "cards.json").read_text(encoding="utf-8"))
CATEGORIES = [(row["id"], row["label"]) for row in CATALOG["categories"]]
CATEGORY_LABELS = dict(CATEGORIES)
# Centralised market-informed browsing order. Financial ranking remains in rules_engine.py.
MARKET = json.loads((Path(__file__).parent / "card_catalog" / "market_order.json").read_text(encoding="utf-8"))
_catalog_by_id = {c["id"]: c for c in CATALOG["cards"]}
_order = MARKET["display_order"]
if len(_order) != len(_catalog_by_id) or set(_order) != set(_catalog_by_id):
    raise ValueError("Market display order must contain every catalogue card exactly once")
CARDS = [_catalog_by_id[cid] for cid in _order]
DEFAULT_WALLET = []   # Never assume which cards a person owns.
SAMPLE_DATA = False    # Real issuer-labelled, dated, conditional rules.


def supports_credit_upi(card):
    """The same supported credit-card UPI products used by the rules engine."""
    return card["model"] == "kiwi" or (
        card["model"] == "scapia" and card.get("network") == "RuPay"
    )


def payment_methods(selected):
    """Only offer payment methods relevant to the selected card set."""
    methods = ["online", "offline"]
    if any(supports_credit_upi(card) for card in selected):
        methods.append("upi")
    return methods


def valid_payment_method(selected, current):
    """Reset a previous selection if it is no longer offered."""
    return current if current in payment_methods(selected) else "online"


def upi_merchant_routes(selected):
    """Offer the Kiwi-specific QR route only when Kiwi is selected."""
    if not any(supports_credit_upi(card) for card in selected):
        return {}
    routes = {"unconfirmed": "Not sure — show conditional UPI estimates"}
    if any(card["model"] == "kiwi" for card in selected):
        routes["kiwi_qr"] = "Kiwi app — merchant accepts RuPay credit on UPI"
    routes["other"] = "Other UPI app — merchant accepts RuPay credit on UPI"
    return routes
