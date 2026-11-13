"""One grounded AI capability: select a useful reason and caution.

The rules engine alone determines financial facts. No arbitrary model prose
is rendered. The response and diagnostics remain in temporary session state.
"""
import json
import time
from importlib.metadata import version, PackageNotFoundError

from rules_engine import category_label, key_condition, inr, rate_value, money, pct

SYSTEM_PROMPT = (
    "Help the shopper understand this purchase decision. Choose the most useful "
    "reason and caution from the supplied options, based on the purchase and reward. "
    "Prefer an explanation of the underlying reward rate, eligibility or binding cap; "
    "do not merely repeat the numerical advantage shown elsewhere. Choose a caution "
    "about the most relevant constraint or redemption type. Return ONLY a JSON "
    "object containing exactly card_id, benefit_inr, reward_form, reason_id, "
    "caution_id. Copy card_id, benefit_inr and reward_form exactly from recommended. "
    "Choose one reason_id and one caution_id from their respective option maps. "
    "Do not calculate, invent claims, change the recommendation or add prose."
)


def _cashback_cap_binds(result):
    """Only claim a binding cap when the calculation engine established it."""
    return (result.available and result.comparable and result.code == "cap-hit"
            and result.rule is not None and result.rule.get("cap") is not None
            and result.cap_left_before is not None)


def _comparison_reason(win, second):
    """Use modeled causes, not a repetition of the difference on the result card."""
    if not (second and second.available and second.comparable
            and win.available and win.comparable and win.benefit > second.benefit):
        return None
    if _cashback_cap_binds(second):
        win_rate = (win.rule or {}).get("rate")
        second_rate = second.rule.get("rate")
        if win_rate is not None and win_rate == second_rate:
            opening = f"Both cards have a {pct(win_rate)} eligible reward rate for this purchase."
        else:
            opening = _sentence(win.reason)
        cap = (f"{second.card['name']} has only {inr(second.cap_left_before)} of "
               "applicable cashback allowance available before this purchase.")
        if win.rule and "cap" in win.rule and win.rule["cap"] is None:
            conclusion = "The recommended card has no applicable reward cap in this model."
        elif _cashback_cap_binds(win):
            conclusion = (f"The recommended card is also capped, but has "
                          f"{inr(win.cap_left_before)} of applicable allowance available.")
        else:
            conclusion = ""
        return " ".join(part for part in (opening, cap, conclusion) if part)
    if second.code == "below-min":
        return _sentence(win.reason) + " " + second.card["name"] + ": " + _sentence(second.reason)
    if second.code == "excluded":
        return _sentence(win.reason) + " " + second.card["name"] + " has no modeled reward for this purchase."
    win_rate = (win.rule or {}).get("rate")
    second_rate = (second.rule or {}).get("rate")
    if win_rate is not None and second_rate is not None and win_rate > second_rate:
        return (_sentence(win.reason) + f" {second.card['name']} has a "
                f"{pct(second_rate)} applicable reward rate for this purchase.")
    # If no additional supported cause is established, give the actual
    # eligibility reason rather than restating the amount difference.
    return _sentence(win.reason)


def build_payload(win, second, amount, cat):
    form = win.card.get("reward_label", "Cashback")
    eligibility = win.reason
    if win.card["model"] == "channel_capped" and win.code == "cap-hit" and win.rule:
        # Explain arithmetic here; reserve the actual limit for the caution.
        eligibility = (f"At {win.rule['rate']:g}%, the cashback before the cap "
                       f"would be {inr(rate_value(amount,win.rule['rate']))}")
    comparison = _comparison_reason(win, second)
    binding_competitor = bool(comparison and _cashback_cap_binds(second))
    # A binding competitor cap is material to the decision. Include it in
    # every approved reason and in the rules-only default.
    reasons = {"eligibility": comparison if binding_competitor else eligibility}
    if comparison:
        reasons["advantage"] = comparison
    if win.cap_left_after is not None and not binding_competitor:
        reasons["remaining_cap"] = (
            _sentence(eligibility) + " "
            f"Based on the entered cap usage, the estimated remaining applicable "
            f"reward allowance after this purchase is {inr(win.cap_left_after)}."
        )
    cautions = {"issuer_condition": key_condition(win)}
    if form == "Amazon Pay balance" or form.startswith(("Scapia Coins", "Kiwis")):
        # The mandatory issuer condition already includes the redemption
        # limitation. Keep the supported option ID, but use one approved
        # statement so choosing it cannot repeat the same information.
        cautions["redemption"] = cautions["issuer_condition"]
    return {
        "recommended": {"card_id": win.card["id"], "card": win.card["name"],
                        "benefit_inr": round(float(win.benefit), 2), "reward_form": form},
        "purchase": {"amount_inr": money(amount), "category": category_label(cat), "channel": win.channel},
        "reason_options": reasons, "caution_options": cautions,
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def check_response(text, payload):
    """Check exact schema, computed identity, amount, reward form and option IDs."""
    checks = {"Response format": False, "Recommended card": False,
              "Reward amount": False, "Reward type": False,
              "Approved reason": False, "Approved caution": False}
    try:
        obj = json.loads(text, object_pairs_hook=_unique_object)
    except (TypeError, ValueError):
        return None, checks, "Response was not valid JSON or contained duplicate keys."
    required = {"card_id", "benefit_inr", "reward_form", "reason_id", "caution_id"}
    if not isinstance(obj, dict) or set(obj) != required:
        return None, checks, "Unexpected or missing response fields."
    checks["Response format"] = True
    expected = payload["recommended"]
    checks["Recommended card"] = obj["card_id"] == expected["card_id"]
    value = obj["benefit_inr"]
    checks["Reward amount"] = type(value) in (int, float) and value == expected["benefit_inr"]
    checks["Reward type"] = obj["reward_form"] == expected["reward_form"]
    checks["Approved reason"] = isinstance(obj["reason_id"], str) and obj["reason_id"] in payload["reason_options"]
    checks["Approved caution"] = isinstance(obj["caution_id"], str) and obj["caution_id"] in payload["caution_options"]
    return (obj, checks, "") if all(checks.values()) else (None, checks, "One or more grounding checks failed.")


def validate(text, payload):
    return check_response(text, payload)[0] is not None


def _sentence(text):
    text = text.strip()
    return text if not text or text.endswith((".", "!", "?")) else text + "."


def explanation_parts(win, second, amount, cat, selection=None):
    """Return checked reason and mandatory condition without exact repetition."""
    payload = build_payload(win, second, amount, cat)
    selection = selection or {}
    reason = payload["reason_options"].get(selection.get("reason_id"),
                                           payload["reason_options"]["eligibility"])
    issuer = _sentence(payload["caution_options"]["issuer_condition"])
    caution = _sentence(payload["caution_options"].get(selection.get("caution_id"),
                                                       issuer))
    if caution != issuer:
        caution = caution + " " + issuer
    return _sentence(reason), caution


def render_approved(selection, payload):
    r = payload["recommended"]
    return (
        f"{r['card']} offers an estimated {inr(r['benefit_inr'])} in "
        f"{r['reward_form'].lower()} for this purchase. "
        + _sentence(payload["reason_options"][selection["reason_id"]]) + " "
        + _sentence(payload["caution_options"][selection["caution_id"]])
    )


def _call_gemini(prompt, api_key, model):
    from google import genai
    from google.genai import types
    config = {"system_instruction": SYSTEM_PROMPT, "temperature": 0.1,
              "max_output_tokens": 400, "response_mime_type": "application/json"}
    if "2.5" in model and "flash" in model:
        config["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model, contents=prompt, config=types.GenerateContentConfig(**config)
    )
    return (response.text or "").strip()


def _error_category(exc):
    """Never display or log raw provider errors, keys or purchase data."""
    msg = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower() or "timed out" in msg or "deadline exceeded" in msg:
        return "AI request timed out. Your calculated card recommendation is still available."
    if isinstance(exc, ImportError):
        return "Gemini SDK is unavailable. Check requirements.txt."
    if "429" in msg or "quota" in msg or "resource_exhausted" in msg:
        return "Provider quota or rate limit reached."
    if any(x in msg for x in ("401", "403", "api key", "api_key_invalid", "permission")):
        return "Provider rejected the key or permissions."
    if "404" in msg or "not found" in msg:
        return "Configured Gemini model is unavailable."
    if getattr(exc, "code", None) == 400 or "invalid_argument" in msg or "400 bad request" in msg:
        return "Gemini rejected the request parameters (HTTP 400)."
    if isinstance(exc, (TypeError, AttributeError, ValueError)):
        return "Gemini SDK or request configuration error."
    if getattr(exc, "code", None) in (500, 502, 503, 504):
        return "Gemini service is temporarily unavailable."
    return "Provider request failed. Check Streamlit app configuration."


def ai_reword(win, second, amount, cat, api_key, model="gemini-3.5-flash-lite"):
    """Return (approved explanation or None, status, session-only diagnostics)."""
    diag = {"model": str(model), "api_response": False, "checks": {},
            "elapsed_ms": None, "message": ""}
    if not api_key or not str(api_key).strip():
        diag["message"] = "Gemini API key is not configured."
        return None, "no_key", diag
    try:
        diag["sdk_version"] = version("google-genai")
    except PackageNotFoundError:
        diag["sdk_version"] = "not installed"
    start = time.perf_counter()
    try:
        payload = build_payload(win, second, amount, cat)
        text = _call_gemini(json.dumps(payload, ensure_ascii=False), str(api_key).strip(), model)
        diag["api_response"] = True
        selection, checks, message = check_response(text, payload)
        diag["checks"] = checks
        diag["message"] = message
        if selection is not None:
            diag["reason_id"] = selection["reason_id"]
            diag["caution_id"] = selection["caution_id"]
            return render_approved(selection, payload), "ok", diag
        return None, "mismatch", diag
    except Exception as exc:
        diag["message"] = _error_category(exc)
        code = getattr(exc, "code", None)
        if type(code) is int and 400 <= code <= 599:
            diag["http_status"] = code
        # Only fixed category labels and numeric status; never raw messages.
        diag["failure_type"] = "provider HTTP error" if "http_status" in diag else ("SDK/configuration" if isinstance(exc, (ImportError, TypeError, AttributeError, ValueError)) else "transport or runtime")
        print("Gemini explanation failed: " + diag["message"])
        return None, "error", diag
    finally:
        diag["elapsed_ms"] = round((time.perf_counter()-start)*1000)


def explain_comparison(ranked, amount, cat, enabled, api_key=None, model="gemini-3.5-flash-lite"):
    """Run at most one AI request for an explicit, eligible comparison.

    Called only by the Compare button, never by ordinary widget rerenders.
    Do not send data if AI is disabled or a reliable positive unique result
    cannot be established. The existing rules result is never modified.
    """
    if not enabled:
        return None, "disabled", {}
    eligible = [r for r in ranked if r.available]
    if not eligible or any(not r.comparable for r in eligible):
        return None, "skipped", {}
    win = eligible[0]
    if win.benefit <= 0.005 or any(abs(r.benefit-win.benefit)<0.005 for r in eligible[1:]):
        return None, "skipped", {}
    second = eligible[1] if len(eligible)>1 else None
    return ai_reword(win, second, amount, cat, api_key, model)
