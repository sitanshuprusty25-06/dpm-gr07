"""Rules engine: computes the rupee benefit of each card for one purchase.

No GenAI here. All numbers shown to the user come from this module.
"""

from dataclasses import dataclass, field


@dataclass
class CardResult:
    card_id: str
    name: str
    benefit: float
    reason: str
    key_condition: str
    condition_type: str
    reward_type: str
    last_verified: str
    source: str
    # Every number the explanation is allowed to quote.
    facts: dict = field(default_factory=dict)


def inr(x):
    """Format a rupee amount with Indian digit grouping, e.g. 1,20,000 or 520.50."""
    x = round(float(x), 2)
    whole = int(x)
    frac = round(x - whole, 2)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    if frac:
        s += f"{frac:.2f}"[1:]
    return f"₹{s}"


def pct(x):
    """Format a percentage without trailing zeros, e.g. 5, 1.5, 0.5."""
    return f"{round(float(x), 2):g}%"


def evaluate_card(card, amount, category, cap_used=0.0):
    """Apply one card's rules to one purchase and return a CardResult."""
    unit = card["unit_value"]
    base_pct = card["base_rate"] * unit
    cap_used = max(float(cap_used or 0), 0.0)

    facts = {"amount": amount, "base_rate_pct": base_pct}
    if card["reward_type"] == "points":
        facts["point_value"] = unit
    points_note = (
        f" Points are valued at {inr(unit)} each, which is an estimate."
        if card["reward_type"] == "points"
        else ""
    )

    def result(benefit, reason, condition, ctype):
        facts["benefit"] = round(benefit, 2)
        return CardResult(
            card_id=card["id"],
            name=card["name"],
            benefit=round(benefit, 2),
            reason=reason + points_note,
            key_condition=condition,
            condition_type=ctype,
            reward_type=card["reward_type"],
            last_verified=card["last_verified"],
            source=card["source"],
            facts=dict(facts),
        )

    # 1. Excluded category: no reward at all.
    if category in card["excluded"]:
        return result(
            0.0,
            f"No reward on {category}.",
            f"{card['name']} excludes {category} purchases from rewards.",
            "excluded",
        )

    base_benefit = amount * base_pct / 100
    rule = card["rules"].get(category)

    # 2. No category bonus: base rate only.
    if rule is None:
        return result(
            base_benefit,
            f"{pct(base_pct)} base rate; no {category} bonus.",
            "No category bonus applies, so only the base rate is earned.",
            "base",
        )

    bonus_pct = max(rule["rate"] * unit, base_pct)
    cap = rule["monthly_cap"]
    min_p = rule["min_purchase"]
    max_p = rule["max_purchase"]
    facts["bonus_rate_pct"] = bonus_pct
    if cap is not None:
        facts["monthly_cap"] = cap
        facts["cap_used"] = cap_used
    if min_p is not None:
        facts["min_purchase"] = min_p
    if max_p is not None:
        facts["max_purchase"] = max_p

    # 3. Below the minimum purchase: bonus does not apply.
    if min_p is not None and amount < min_p:
        return result(
            base_benefit,
            f"Below the {inr(min_p)} minimum for the {pct(bonus_pct)} bonus; "
            f"{pct(base_pct)} base rate applies.",
            f"The {pct(bonus_pct)} bonus needs a purchase of at least {inr(min_p)}.",
            "below_min",
        )

    eligible = min(amount, max_p) if max_p is not None else amount
    remaining = max(cap - cap_used, 0.0) if cap is not None else None
    facts["eligible_amount"] = eligible

    # 4. Monthly bonus cap already used up.
    if remaining is not None and remaining == 0:
        facts["cap_remaining"] = 0
        return result(
            base_benefit,
            f"Monthly bonus cap already used; {pct(base_pct)} base rate applies.",
            f"The {inr(cap)} monthly bonus cap is used up, so only the base rate is earned.",
            "cap_exhausted",
        )

    # Bonus portion: the bonus rate replaces the base rate on the covered amount.
    covered = eligible
    if remaining is not None:
        covered = min(eligible, remaining * 100 / bonus_pct)
    bonus_part = covered * bonus_pct / 100
    base_part = (amount - covered) * base_pct / 100
    total = bonus_part + base_part
    covered = round(covered, 2)
    facts["covered_amount"] = covered
    facts["bonus_part"] = round(bonus_part, 2)
    facts["base_part"] = round(base_part, 2)
    if remaining is not None:
        facts["cap_remaining"] = remaining

    # 5. Cap reached part-way through this purchase.
    if remaining is not None and covered < eligible:
        return result(
            total,
            f"{pct(bonus_pct)} on the first {inr(covered)} (cap reached), "
            f"{pct(base_pct)} on the rest.",
            f"The {pct(bonus_pct)} bonus is capped at {inr(cap)} a month, so it covers "
            f"only the first {inr(covered)} of this purchase.",
            "cap_hit",
        )

    # 6. Per-purchase limit on the bonus.
    if eligible < amount:
        return result(
            total,
            f"{pct(bonus_pct)} on the first {inr(eligible)}, {pct(base_pct)} on the rest.",
            f"The bonus applies to at most {inr(max_p)} per purchase.",
            "max_purchase",
        )

    # 7. Full bonus earned.
    if remaining is not None:
        left = round(remaining - bonus_part, 2)
        facts["cap_left_after"] = left
        condition = (
            f"The bonus is capped at {inr(cap)} a month; {inr(left)} of it would be "
            f"left after this purchase."
        )
    else:
        condition = "No cap or minimum applies to this bonus."
    return result(
        total,
        f"{pct(bonus_pct)} bonus on the full amount.",
        condition,
        "full_bonus",
    )


def evaluate_all(cards, amount, category, cap_used_by_card=None):
    """Return results for the given cards, best benefit first."""
    cap_used_by_card = cap_used_by_card or {}
    results = [
        evaluate_card(c, amount, category, cap_used_by_card.get(c["id"], 0.0))
        for c in cards
    ]
    return sorted(results, key=lambda r: (-r.benefit, r.name))
