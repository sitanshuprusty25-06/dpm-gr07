"""Customer-facing reward text; does not change calculations."""
from datetime import date
from rules_engine import pct

def review_date(value):
    try:
        return date.fromisoformat(value).strftime("%d %b %Y").lstrip("0")
    except (TypeError, ValueError):
        return str(value or "Not recorded")

def comparison_text(result):
    if not result.available:
        return result.reason, ""
    if not result.comparable:
        return result.uncertainty, ""
    if result.code in ("excluded", "below-min"):
        return result.reason, ""
    reason = result.reason
    rule = result.rule or {}
    model = result.card.get("model")
    if model in ("hdfc_ornge", "hdfc_original", "hdfc_blck", "flipkart_axis") and "rate" in rule:
        context = {"boost":"eligible purchases", "swiggy":"eligible Swiggy purchases",
                   "online":"eligible listed online purchases", "base":"other eligible purchases",
                   "flipkart":"eligible Flipkart purchases", "myntra":"eligible Myntra purchases",
                   "cleartrip":"eligible Cleartrip hotel bookings", "preferred":"eligible partner purchases"}.get(rule.get("bucket"))
        if context:
            reason = f"{pct(rule['rate'])} cashback on {context}"
    elif model == "shared_category_cap" and result.code == "bonus" and "rate" in rule:
        reason = f"{pct(rule['rate'])} cashback on eligible purchases"
    if result.code == "cap-hit" and rule.get("cap") is not None and result.cap_left_before is not None:
        reason = reason.rstrip(".") + " · Limited by remaining cap"
    return reason, result.card.get("reward_label", "Cashback")

def redemption_guidance(ranked):
    forms = {item.card.get("reward_label", "") for item in ranked}
    details = []
    if "Amazon Pay balance" in forms:
        details.append("Amazon Pay balance is not cash or statement credit.")
    if any(form.startswith("Scapia Coins") for form in forms):
        details.append("Scapia Coins represent travel redemption value, not cash.")
    if any(form.startswith("Kiwis") for form in forms):
        details.append("Kiwi rewards are bank-redeemable under applicable Kiwi terms.")
    if len(forms) > 1 and details:
        details.append("Compare the usefulness of each reward form to you before paying.")
    return " ".join(details)
