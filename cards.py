"""Dated catalogue of supported cards (PRD layer: KNOW).

IMPORTANT: the five cards below are ILLUSTRATIVE SAMPLES with made-up terms so the
product flow can be demonstrated. Before any user test, replace them with real cards
whose terms the team has checked against the issuer's published terms, and update
`last_verified` and `source` for each one.

Field guide
-----------
reward_type   "cashback" or "points"
unit_value    rupee value of one reward unit (1 for cashback, e.g. 0.25 for a point)
base_rate     reward units earned per Rs 100 on any eligible purchase
rules         per-category bonus. Keys of each rule:
                rate           reward units per Rs 100 on the bonus portion
                monthly_cap    max rupee value of bonus per month (None = no cap)
                min_purchase   smallest purchase that qualifies (None = no minimum)
                max_purchase   largest amount per purchase that earns the bonus (None = no limit)
excluded      categories that earn no reward at all
"""

CATEGORIES = [
    "Online shopping",
    "Dining",
    "Groceries",
    "Fuel",
    "Travel",
    "Utilities & bill payments",
    "Other",
]

CARDS = [
    {
        "id": "online_shopper",
        "name": "Sample Online Shopper Card",
        "reward_type": "cashback",
        "unit_value": 1,
        "base_rate": 1,
        "rules": {
            "Online shopping": {
                "rate": 5,
                "monthly_cap": 500,
                "min_purchase": 500,
                "max_purchase": None,
            },
        },
        "excluded": ["Fuel", "Utilities & bill payments"],
        "last_verified": "2026-11-11",
        "source": "Illustrative sample terms (not a real card)",
    },
    {
        "id": "dining_rewards",
        "name": "Sample Dining Rewards Card",
        "reward_type": "cashback",
        "unit_value": 1,
        "base_rate": 1,
        "rules": {
            "Dining": {
                "rate": 5,
                "monthly_cap": 400,
                "min_purchase": 1000,
                "max_purchase": None,
            },
            "Groceries": {
                "rate": 2,
                "monthly_cap": None,
                "min_purchase": None,
                "max_purchase": None,
            },
        },
        "excluded": ["Fuel"],
        "last_verified": "2026-11-11",
        "source": "Illustrative sample terms (not a real card)",
    },
    {
        "id": "travel_points",
        "name": "Sample Travel Points Card",
        "reward_type": "points",
        "unit_value": 0.25,
        "base_rate": 2,
        "rules": {
            "Travel": {
                "rate": 10,
                "monthly_cap": 1000,
                "min_purchase": None,
                "max_purchase": 50000,
            },
        },
        "excluded": ["Fuel", "Utilities & bill payments"],
        "last_verified": "2026-11-11",
        "source": "Illustrative sample terms (not a real card)",
    },
    {
        "id": "everyday_cashback",
        "name": "Sample Everyday Cashback Card",
        "reward_type": "cashback",
        "unit_value": 1,
        "base_rate": 1.5,
        "rules": {},
        "excluded": ["Utilities & bill payments"],
        "last_verified": "2026-11-11",
        "source": "Illustrative sample terms (not a real card)",
    },
    {
        "id": "fuel_bills",
        "name": "Sample Fuel and Bills Card",
        "reward_type": "cashback",
        "unit_value": 1,
        "base_rate": 0.5,
        "rules": {
            "Fuel": {
                "rate": 4,
                "monthly_cap": 250,
                "min_purchase": None,
                "max_purchase": 4000,
            },
            "Utilities & bill payments": {
                "rate": 2,
                "monthly_cap": 150,
                "min_purchase": None,
                "max_purchase": None,
            },
        },
        "excluded": [],
        "last_verified": "2026-11-11",
        "source": "Illustrative sample terms (not a real card)",
    },
]
