"""Version-controlled, read-only catalogue of issuer rules. No user data is saved here."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "card_catalog" / "cards.json").read_text(encoding="utf-8"))
CATEGORIES = [(row["id"], row["label"]) for row in CATALOG["categories"]]
CATEGORY_LABELS = dict(CATEGORIES)
CARDS = CATALOG["cards"]
DEFAULT_WALLET = []   # Never assume which cards a person owns.
SAMPLE_DATA = False    # Real issuer-labelled, dated, conditional rules.
