"""Rules engine: computes the rupee benefit of each card for one purchase.

A Python port of the prototype's rules logic. No GenAI here. Every number shown to
the user comes from this module.
"""

import math
from dataclasses import dataclass

from cards import CATEGORY_LABELS


def rnd(x):
    """Round half up to a whole number (matches the prototype's Math.round)."""
    return int(math.floor(x + 0.5))


def group(n):
    """Indian digit grouping for a non-negative whole number: 1,20,000."""
    s = str(int(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return s


def inr(n):
    return "₹" + group(rnd(n))


def pct(n):
    return f"{round(n * 100) / 100:g}%"


def category_label(cat):
    return CATEGORY_LABELS[cat]


@dataclass
class Result:
    card: dict
    category: str
    rule: dict = None
    code: str = ""
    reason: str = ""
    bonus_amt: float = 0.0
    bonus_benefit: float = 0.0
    base_benefit: float = 0.0
    cap_left_before: float = None
    cap_left_after: float = None
    benefit: float = 0.0
    points: float = None


def highlight(card):
    """One-line summary of a card's bonus rules, shown in the wallet list."""
    parts = []
    for cat, r in card["rules"].items():
        s = f"{pct(r['rate'])} {category_label(cat).lower()}"
        if r.get("cap"):
            s += f" (cap {inr(r['cap'])}/mo)"
        if r.get("min"):
            s += f", min {inr(r['min'])}"
        parts.append(s)
    parts.append(f"{pct(card['base'])} elsewhere")
    return " · ".join(parts)


def evaluate(card, cat, amount, used=0.0):
    """Apply one card's rules to one purchase. `used` is the bonus already earned this
    month on this card's rule for this category (0 unless the user says otherwise)."""
    rule = card["rules"].get(cat)
    base_allowed = cat not in card["excl"]
    base_rate = card["base"] if base_allowed else 0
    o = Result(card=card, category=cat, rule=rule)
    label = category_label(cat).lower()

    if rule:
        if rule.get("min") and amount < rule["min"]:
            o.code = "below-min"
            o.reason = f"Bonus needs {inr(rule['min'])}+ per purchase"
            o.base_benefit = amount * base_rate / 100
        else:
            eligible = amount
            if rule.get("max") and amount > rule["max"]:
                eligible = rule["max"]
                o.code = "above-max"
                o.reason = f"Bonus covers the first {inr(rule['max'])} of a purchase"
            if rule.get("cap"):
                left = max(0.0, rule["cap"] - used)
                max_amt = left * 100 / rule["rate"]
                if max_amt < eligible:
                    eligible = max_amt
                    o.code = "cap-exhausted" if left <= 0 else "cap-hit"
                    if left <= 0:
                        o.reason = f"Monthly cap of {inr(rule['cap'])} already used"
                    elif used > 0:
                        o.reason = f"Only {inr(left)} of bonus left this month"
                    else:
                        o.reason = f"Bonus capped at {inr(rule['cap'])} a month"
                o.cap_left_before = left
            o.bonus_amt = eligible
            o.bonus_benefit = eligible * rule["rate"] / 100
            o.base_benefit = (amount - eligible) * base_rate / 100
            if rule.get("cap"):
                o.cap_left_after = max(0.0, o.cap_left_before - o.bonus_benefit)
            if not o.code:
                o.code = "bonus"
                o.reason = f"{pct(rule['rate'])} on {label}"
    elif not base_allowed:
        o.code = "excluded"
        o.reason = card["excl"][cat]
    else:
        o.base_benefit = amount * base_rate / 100
        o.code = "base"
        o.reason = f"{pct(base_rate)} flat rate"

    o.benefit = round(o.bonus_benefit + o.base_benefit, 2)
    if card.get("point_value"):
        o.points = o.benefit / card["point_value"]
    return o


def rank(cards, cat, amount, used_by_card=None):
    """Best benefit first. Exact ties go to the lower annual fee, then the name."""
    used_by_card = used_by_card or {}
    results = [evaluate(c, cat, amount, used_by_card.get(c["id"], 0)) for c in cards]
    results.sort(key=lambda r: (-r.benefit, r.card["fee"], r.card["name"]))
    return results


def key_condition(r):
    """The one condition worth reading before paying, chosen by priority."""
    rule, c = r.rule, r.card
    earns_base = r.base_benefit > 0
    rest = pct(c["base"]) if earns_base else "nothing"
    flat = f"only the flat {pct(c['base'])} applies" if earns_base else "no reward applies"
    if r.code == "cap-hit":
        return (
            f"Monthly cap: only the first {inr(r.bonus_amt)} of this purchase earns "
            f"{pct(rule['rate'])}. The rest earns {rest}."
        )
    if r.code == "above-max":
        return f"{r.reason}. The rest earns {rest}."
    if r.code in ("below-min", "cap-exhausted"):
        return f"{r.reason}, so {flat}."
    if r.code == "bonus" and rule.get("cap"):
        return (
            f"Monthly cap {inr(rule['cap'])} on this bonus. "
            f"{inr(r.cap_left_after)} will be left after this purchase."
        )
    if r.code == "bonus" and rule.get("min"):
        return f"The bonus applies to purchases of {inr(rule['min'])} or more."
    if r.code == "bonus":
        return "No monthly cap on this category."
    excluded = [category_label(k).lower() for k in c["excl"]]
    text = "Flat rate with no monthly cap."
    if excluded:
        text += f" Not earned on {' and '.join(excluded)}."
    return text


def template_explain(win, second, amount, cat):
    """Plain explanation built only from the rules output (the default text)."""
    s = (
        f"Use {win.card['name']} for this {inr(amount)} {category_label(cat).lower()} "
        f"purchase. You should earn about {inr(win.benefit)}"
    )
    if win.card.get("point_value"):
        s += f" ({group(rnd(win.points))} points at ₹{win.card['point_value']:g} each)"
    s += "."
    if second:
        if abs(second.benefit - win.benefit) < 0.005:
            s += f" {second.card['name']} earns the same, so the two tie."
            if win.card["fee"] < second.card["fee"]:
                s += " This one is listed first for its lower annual fee."
        else:
            s += (
                f" That is {inr(win.benefit - second.benefit)} more than "
                f"{second.card['name']}, your next best card."
            )
    return s + " " + key_condition(win)
