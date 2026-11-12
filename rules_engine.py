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
    """Display modeled rupee value to paise; avoid rounding positive rewards to zero."""
    paise = rnd(abs(n)*100)
    whole, fraction = divmod(paise, 100)
    sign = "-" if n < 0 and paise else ""
    return sign + "₹" + group(whole) + (f".{fraction:02d}" if fraction else "")

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
    available: bool = True

def highlight(card):
    if card.get("summary"):
        return card["summary"]
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

def reward_bucket(card, cat, channel, merchant_type="unknown"):
    """Single applicable reward bucket; None means classification unknown."""
    model = card["model"]
    if cat in card.get("excl",{}):
        return None
    if channel == "upi":
        return None
    if model == "channel_capped":
        r = card["channel_rules"][channel]
        return (channel, r["rate"], r["cap"], 0)
    if model == "shared_category_cap":
        if cat in ("dining","groceries"):
            return ("shared", 10, card["rules"][cat]["cap"], 0)
        return ("base", 1.5, None, 0)
    if model in ("hdfc_ornge","hdfc_original","hdfc_blck"):
        orange = model == "hdfc_ornge"
        if merchant_type == "swiggy" and channel == "online" and cat in ("dining","groceries"):
            return ("boost" if orange else "swiggy", 5 if orange else 10, 1500, 249)
        if channel == "online" and merchant_type in ("amazon_prime","amazon_nonprime","marketplace","flipkart","myntra","eligible_online") and cat in ("shopping","cinema"):
            return ("boost" if orange else "online", 5, 1500, 249 if orange else 100)
        if channel == "online" and merchant_type != "other" and merchant_type not in ("axis_preferred",):
            return None
        if cat == "utilities":
            return None
        return ("base", 1, 1000 if orange or model == "hdfc_blck" else 500, 100)
    if model == "flipkart_axis":
        if channel == "online" and cat == "shopping" and merchant_type in ("flipkart","myntra"):
            return (merchant_type, 7.5 if merchant_type == "myntra" else 5, 4000, 0)
        if channel == "online" and cat == "hotel" and merchant_type == "cleartrip":
            return ("cleartrip",5,4000,0)
        if merchant_type == "axis_preferred":
            return ("preferred",4,None,0)
        if merchant_type in ("unknown","marketplace","eligible_online"):
            return None
        return ("base",1,None,0)
    if model == "amazon":
        if merchant_type == "amazon_pay" and channel != "online":
            return None
        if channel == "online" and cat == "shopping" and merchant_type in ("amazon_prime","amazon_nonprime"):
            return ("amazon",5 if merchant_type=="amazon_prime" else 3,None,0)
        if channel == "online" and merchant_type == "amazon_pay":
            return ("amazon_pay",2,None,0)
        if cat == "utilities":
            if merchant_type == "other":
                return ("excluded",0,None,0)
            return None
        if channel == "online" and merchant_type == "unknown":
            return None
        return ("base",1,None,0)
    return None

def evaluate(card, cat, amount, used=0.0, channel="online", merchant_type="unknown", kiwi_remaining=None):
    if cat not in CATEGORY_LABELS or channel not in ("online","offline","upi") or amount <= 0 or used < 0:
        raise ValueError("Unsupported category/channel, invalid purchase amount, or negative used cap")
    out = Result(card=card, category=cat, channel=channel)
    model = card["model"]
    # A merchant UPI QR is a different payment rail, not ordinary card POS.
    if channel == "upi" and not (model == "kiwi" or (model == "scapia" and card.get("network")=="RuPay")):
        out.available = False
        out.code = "unavailable"
        out.reason = "UPI credit-card route not modeled for this product"
        return out
    if model == "kiwi" and channel == "offline":
        out.available = False
        out.code = "unavailable"
        out.reason = "Virtual Kiwi card; choose eligible Kiwi UPI QR or online route"
        return out
    if merchant_type == "scapia_travel" and (channel != "online" or cat not in ("hotel","travel")):
        return _unknown(out,"Scapia travel must be an eligible booking in its app.")
    if model == "kiwi":
        if cat in card.get("excl",{}):
            out.code="excluded"
            out.reason=card["excl"][cat]
            return out
        if merchant_type not in ("kiwi_qr","kiwi_online"):
            return _unknown(out,"Confirm the eligible payment is via Kiwi; standard non-Neon rewards only.")
        if (merchant_type=="kiwi_qr" and channel!="upi") or (merchant_type=="kiwi_online" and channel!="online"):
            return _unknown(out,"Kiwi payment route does not match the selected channel.")
        rate=1.5 if channel=="upi" else 0.5
        value=math.floor(amount/100)*rate
        if kiwi_remaining is not None:
            if kiwi_remaining < 0:
                raise ValueError("Negative Kiwi remaining cap")
            value=min(value,kiwi_remaining)
        out.benefit=round(value,2)
        out.points=out.benefit/0.25
        out.code="kiwi"
        out.reason=f"{pct(rate)} on completed ₹100 blocks via Kiwi" + ("; before monthly cap (conditional)" if kiwi_remaining is None else "; limited by entered remaining cap")
        if kiwi_remaining is None and value>0:
            return _unknown(out,"Monthly Kiwi reward cap depends on your credit limit. Enter known remaining rupee-equivalent cap to rank; uncapped estimate "+inr(value)+".")
        return out
    if model == "scapia":
        if cat in card.get("excl",{}):
            out.code="excluded"
            out.reason=card["excl"][cat]
            return out
        if merchant_type=="unknown":
            return _unknown(out,"Confirm ordinary eligible spend or eligible Scapia travel booking.")
        if card["network"]=="RuPay" and amount==500 and merchant_type!="scapia_travel":
            return _unknown(out,"Issuer documents differ on the exact ₹500 boundary; check current terms.")
        travel=merchant_type=="scapia_travel"
        minimum=card["minimum"]
        if not travel and amount<minimum:
            out.code="below-min"
            out.reason=f"Below {inr(minimum)} eligible transaction minimum"
            return out
        rate=20 if travel else card["coin_rate"]
        # Estimated value of coins, not the published nominal coin-earn rate as cash.
        out.points=rnd(amount*rate/100) if card["network"]=="Visa" else round(amount*rate/100,2)
        out.benefit=round(out.points/5,2)
        out.code="scapia"
        out.reason=f"{pct(rate)} coins = about {pct(rate/5)} rupee-equivalent travel value"
        return out
    if (merchant_type in ("amazon_prime","amazon_nonprime","flipkart","myntra","marketplace") and (channel != "online" or cat != "shopping")) or (merchant_type == "swiggy" and (channel != "online" or cat not in ("dining","groceries"))) or (merchant_type == "cleartrip" and (channel != "online" or cat != "hotel")):
        return _unknown(out,"Merchant route does not match this purchase category or channel.")
    if cat in card.get("excl", {}):
        out.code = "excluded"
        out.reason = card["excl"][cat]
        return out
    if card["model"] in ("hdfc_ornge","hdfc_original","hdfc_blck","amazon","flipkart_axis"):
        bucket = reward_bucket(card,cat,channel,merchant_type)
        if bucket is None:
            return _unknown(out,"Select the specific merchant or confirm ordinary eligible spend; the reward tier is not established.")
        name,rate,cap,minimum = bucket
        if cap is not None and used > cap:
            raise ValueError("Previously earned reward exceeds the applicable cap")
        out.rule = {"rate":rate,"cap":cap,"min":minimum,"bucket":name}
        out.cap_left_before = None if cap is None else cap-used
        if amount < minimum:
            out.code = "below-min"
            out.reason = f"Below {inr(minimum)} minimum for this reward tier"
            return out
        possible = amount * rate / 100
        if card["model"].startswith("hdfc"):
            possible = rnd(possible)
        if card["model"] == "flipkart_axis" and cap is not None and possible > cap-used + 0.005:
            return _unknown(out,"This purchase exceeds the remaining accelerated statement-quarter cap; the catalogue has not established the reward on the rest.")
        out.benefit = round(possible if cap is None else min(possible,cap-used),2)
        out.cap_left_after = None if cap is None else max(0,cap-used-out.benefit)
        out.code = "cap-hit" if cap is not None and possible > cap-used else "bonus"
        out.reason = f"{pct(rate)} eligible {name.replace('_',' ')} reward" + (" (Amazon Pay balance)" if card["model"]=="amazon" else "")
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
            if merchant_type in ("marketplace","amazon_prime","amazon_nonprime","flipkart","myntra"):
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

def rank(cards, cat, amount, used_by_card=None, channel="online", merchant_type="unknown", kiwi_remaining=None):
    used_by_card = used_by_card or {}
    results = [evaluate(c, cat, amount, used_by_card.get(c["id"], 0),
                        channel=channel, merchant_type=merchant_type, kiwi_remaining=kiwi_remaining) for c in cards]
    # An unresolved reward is not a zero reward and must not be treated as such.
    results.sort(key=lambda r: (not r.available, not r.comparable, -r.benefit, r.card["name"]))
    return results

def key_condition(r):
    card = r.card
    if not r.available:
        return r.reason
    if not r.comparable:
        return r.uncertainty
    if r.code in ("excluded","below-min"):
        return r.reason
    if card["model"]=="kiwi":
        return "Standard Kiwi non-Neon rewards via the Kiwi app, completed ₹100 blocks and entered remaining cap. 1 Kiwi = ₹0.25; bank reward points and milestones excluded."
    if card["model"]=="scapia":
        return "Five Scapia Coins = ₹1 in the Scapia app, not cash. Issuer MCC exclusions apply; travel redemption and potential fees may affect usable value."
    if card["model"] in ("hdfc_ornge","hdfc_original","hdfc_blck","amazon","flipkart_axis"):
        if r.code == "below-min":
            return r.reason
        if card["model"] == "amazon":
            return "Reward is credited as Amazon Pay balance; eligible purchases only, not a cash statement credit."
        if card["model"] == "flipkart_axis":
            if r.rule["cap"] is None:
                return "Eligible uncapped cashback; actual merchant ID and exclusions determine the reward."
            return f"Separate {inr(r.rule['cap'])} statement-quarter cap for {r.rule['bucket']}; {inr(r.cap_left_after)} remains. Merchant ID eligibility applies."
        return (f"Applicable billing-cycle cap {inr(r.rule['cap'])}; "
                f"{inr(r.cap_left_after)} remains after this purchase. Minimum {inr(r.rule['min'])}; issuer exclusions apply.")
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
               f"{win.card['name']} offers an estimated {inr(win.benefit)} in {win.card.get('reward_label','cashback').lower()}.")
    if second and second.comparable:
        if abs(second.benefit-win.benefit) < 0.005:
            message += f" {second.card['name']} has the same estimated benefit; this is a tie."
        else:
            message += f" This is {inr(win.benefit-second.benefit)} more than {second.card['name']}."
    return message + " " + key_condition(win)
