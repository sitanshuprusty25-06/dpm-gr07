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
