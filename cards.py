"""Dated catalogue of supported cards (PRD layer: KNOW).

IMPORTANT: the cards below are the FICTIONAL samples from the prototype. Issuers and
terms are made up so the flow can be demonstrated. Before user testing, replace them
with real cards whose terms the team has checked against the issuer's published terms
(see "How to replace the sample cards" in README.md), then set SAMPLE_DATA = False.

Field guide for one card
------------------------
id             short unique id, no spaces
name, issuer   shown on screen
chip           one coloured-square emoji shown beside the name
hue            hex colour used on the result screen
fee            annual fee in rupees (only used to break exact ties)
base           flat reward rate, in percent of the purchase value, on any category
               that is not excluded
point_value    OPTIONAL. Rupee value of one reward point. Only used to show points.
               Rates below are always percent of rupee value.
rules          per-category bonus, keyed by category id. Keys of each rule:
                 rate  bonus rate in percent (replaces the base rate on the covered amount)
                 cap   OPTIONAL. Max bonus in rupees per month
                 min   OPTIONAL. Smallest purchase that earns the bonus
                 max   OPTIONAL. Largest part of one purchase that earns the bonus
excl           categories that earn no flat reward, mapped to the reason shown
last_verified  date (YYYY-MM-DD) the team last checked the terms
source         where the terms came from (issuer page and date)
"""

SAMPLE_DATA = True

# Cards ticked when the app opens. Use [] for user testing so people choose their own.
DEFAULT_WALLET = ["voyage", "everyday", "dine", "flat2"]

CATEGORIES = [
    ("dining", "Dining"),
    ("groceries", "Groceries"),
    ("travel", "Travel"),
    ("shopping", "Online shopping"),
    ("fuel", "Fuel"),
    ("bills", "Bills"),
    ("entertainment", "Entertainment"),
    ("other", "Other"),
]
CATEGORY_LABELS = dict(CATEGORIES)

_SAMPLE_SOURCE = "Fictional sample terms from the prototype (not a real card)"
_VERIFIED = "2026-11-11"

CARDS = [
    {
        "id": "voyage",
        "name": "Voyage Platinum",
        "issuer": "Orbit Bank",
        "chip": "🟦",
        "hue": "#1D5C8C",
        "fee": 2500,
        "base": 1,
        "rules": {"travel": {"rate": 5, "cap": 1500}},
        "excl": {"fuel": "No rewards on fuel", "bills": "No rewards on bills"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "everyday",
        "name": "Everyday Cashback",
        "issuer": "Meridian Bank",
        "chip": "🟪",
        "hue": "#6B4AA8",
        "fee": 500,
        "base": 1,
        "rules": {"shopping": {"rate": 5, "cap": 500}, "bills": {"rate": 2, "cap": 200}},
        "excl": {"fuel": "No cashback on fuel"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "dine",
        "name": "Dine & Delight",
        "issuer": "Lumen Bank",
        "chip": "🟥",
        "hue": "#B04A3A",
        "fee": 1000,
        "base": 1,
        "rules": {"dining": {"rate": 10, "cap": 400, "min": 1000}},
        "excl": {"fuel": "No rewards on fuel"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "fuel",
        "name": "FuelSaver",
        "issuer": "Orbit Bank",
        "chip": "🟩",
        "hue": "#2F7D4F",
        "fee": 499,
        "base": 0.5,
        "rules": {"fuel": {"rate": 4, "cap": 300, "min": 500, "max": 4000}},
        "excl": {"bills": "No rewards on bills"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "grocer",
        "name": "Grocer Plus",
        "issuer": "Kestrel Bank",
        "chip": "🟨",
        "hue": "#B8860B",
        "fee": 0,
        "base": 1,
        "rules": {"groceries": {"rate": 5, "cap": 600}},
        "excl": {"fuel": "No rewards on fuel"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "flat2",
        "name": "Flat Two",
        "issuer": "Kestrel Bank",
        "chip": "⬛",
        "hue": "#3C4A55",
        "fee": 999,
        "base": 2,
        "rules": {},
        "excl": {"fuel": "No rewards on fuel", "bills": "No rewards on bills"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
    {
        "id": "life",
        "name": "Lifestyle Points",
        "issuer": "Lumen Bank",
        "chip": "🟧",
        "hue": "#8C2F6E",
        "fee": 1500,
        "base": 0.5,
        "point_value": 0.25,
        "rules": {"entertainment": {"rate": 2.5}, "dining": {"rate": 1.5}},
        "excl": {"fuel": "No points on fuel"},
        "last_verified": _VERIFIED,
        "source": _SAMPLE_SOURCE,
    },
]
