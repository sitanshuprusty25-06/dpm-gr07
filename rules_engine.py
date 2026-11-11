"""Deterministic purchase-level comparison of the *supported* issuer rules.

When merchant classification or after-cap treatment is unresolved, we do not
pretend to know the winner. This model contains no user storage or API calls.
"""
import math
from dataclasses import dataclass
from cards import CATEGORY_LABELS

def rnd(x):
    return int(math.floor(x + 0.5))

def group(n):
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])

def inr(n):
    return "₹" + group(rnd(n))

def pct(n):
    return f"{float(n):g}%"

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
    comparable: bool = True
    uncertainty: str = ""
    channel: str = "online"

def highlight(card):
    if card["model"] == "channel_capped":
        a, b = card["channel_rules"]["online"], card["channel_rules"]["offline"]
        return f"{pct(a['rate'])} online (cap {inr(a['cap'])}/cycle); {pct(b['rate'])} in-store (cap {inr(b['cap'])}/cycle)"
    return f"10% on eligible boosted categories (shared {inr(card['rules']['dining']['cap'])}/cycle); {pct(card['base'])} on most other eligible spends"

def _unknown(out, message):
    out.comparable = False
    out.code = "unresolved"
    out.reason = "Eligibility/benefit cannot be established"
    out.uncertainty = message
    return out

def evaluate(card, cat, amount, used=0.0, channel="online", merchant_type="unknown"):
    if cat not in CATEGORY_LABELS or channel not in ("online","offline") or amount <= 0 or used < 0:
        raise ValueError("Unsupported category/channel, invalid purchase amount, or negative used cap")
    out = Result(card=card, category=cat, channel=channel)
    if cat in card.get("excl", {}):
        out.code = "excluded"
        out.reason = card["excl"][cat]
        return out
    if card["model"] == "channel_capped":
        rule = card["channel_rules"][channel]
        if used > rule["cap"]:
            raise ValueError("Previously earned cashback exceeds this channel's cap")
        out.rule = rule
        out.cap_left_before = max(0.0, rule["cap"] - used)
        out.bonus_benefit = min(amount * rule["rate"] / 100, out.cap_left_before)
        out.cap_left_after = max(0.0, out.cap_left_before - out.bonus_benefit)
        out.benefit = round(out.bonus_benefit, 2)
        out.code = "cap-hit" if amount * rule["rate"] / 100 > out.cap_left_before + 0.005 else "bonus"
        out.reason = f"{pct(rule['rate'])} eligible {channel} cashback, subject to its statement-cycle cap"
        return out
    if card["model"] == "shared_category_cap":
        rule = card["rules"].get(cat)
        if cat == "shopping":
            if merchant_type == "marketplace":
                rule = None  # HSBC gives 1.5% on Amazon / Flipkart / Myntra.
            else:
                return _unknown(out, "HSBC shopping reward depends on the merchant's MCC; this app cannot confirm its 10% eligibility.")
        if cat == "utilities":
            return _unknown(out, "HSBC utility MCCs may earn accelerated or zero cashback. The utility type alone is insufficient.")
        if rule:
            cap = rule["cap"]  # Shared by *all* accelerated categories.
            if used > cap:
                raise ValueError("Previously earned boosted cashback exceeds the shared cap")
            out.rule = rule
            out.cap_left_before = max(0.0, cap - used)
            possible = amount * rule["rate"] / 100
            out.bonus_benefit = min(possible, out.cap_left_before)
            out.cap_left_after = max(0.0, out.cap_left_before - out.bonus_benefit)
            if possible > out.cap_left_before + 0.005:
                return _unknown(out, "HSBC boosted cashback exceeds the remaining shared cap; the rate on the rest is not confirmed by our source material.")
            out.benefit = round(out.bonus_benefit, 2)
            out.code = "bonus"
            out.reason = f"{pct(rule['rate'])} eligible boosted cashback, subject to a shared billing-cycle cap"
            return out
        out.base_benefit = amount * card["base"] / 100
        out.benefit = round(out.base_benefit, 2)
        out.code = "base"
        out.reason = f"{pct(card['base'])} on this eligible domestic purchase"
        return out
    raise ValueError(f"Unrecognized calculation model: {card['model']}")

def rank(cards, cat, amount, used_by_card=None, channel="online", merchant_type="unknown"):
    used_by_card = used_by_card or {}
    results = [evaluate(c, cat, amount, used_by_card.get(c["id"], 0),
                        channel=channel, merchant_type=merchant_type) for c in cards]
    # An unresolved reward is not a zero reward and must not be treated as such.
    results.sort(key=lambda r: (not r.comparable, -r.benefit, r.card["name"]))
    return results

def key_condition(r):
    card = r.card
    if not r.comparable:
        return r.uncertainty
    if r.code == "excluded":
        return r.reason
    if card["model"] == "channel_capped":
        rule = card["channel_rules"][r.channel]
        if r.code == "cap-hit":
            return (f"{pct(rule['rate'])} eligible {r.channel} cashback has a "
                    f"{inr(rule['cap'])} statement-cycle cap; no cashback is awarded after that channel's cap. "
                    "Other issuer MCC exclusions may apply.")
        return (f"{pct(rule['rate'])} on eligible {r.channel} spending, capped at {inr(rule['cap'])} "
                "per statement cycle. Other MCC exclusions may apply.")
    if r.code == "bonus":
        return (f"Boosted rewards share a {inr(r.rule['cap'])} billing-cycle cap across categories. "
                f"After this purchase {inr(r.cap_left_after)} of accelerated cashback would remain, "
                "assuming issuer MCC eligibility.")
    if r.category == "shopping":
        return "Amazon, Flipkart and Myntra earn 1.5%, not the 10% accelerated shopping rate."
    return "1.5% on most eligible domestic purchases; merchant MCC exclusions may apply."

def template_explain(win, second, amount, cat):
    if not win.comparable:
        return "A trustworthy purchase comparison is not available. " + win.uncertainty
    message = (f"For this {inr(amount)} {category_label(cat).lower()} purchase, "
               f"{win.card['name']} offers an estimated {inr(win.benefit)}.")
    if second and second.comparable:
        if abs(second.benefit-win.benefit) < 0.005:
            message += f" {second.card['name']} has the same estimated benefit; this is a tie."
        else:
            message += f" This is {inr(win.benefit-second.benefit)} more than {second.card['name']}."
    return message + " " + key_condition(win)
