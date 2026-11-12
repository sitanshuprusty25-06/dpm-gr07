"""One grounded AI capability: select a useful reason and caution.

The rules engine alone determines financial facts. No arbitrary model prose
is rendered. The response and diagnostics remain in temporary session state.
"""
import json
import time
from importlib.metadata import version, PackageNotFoundError

from rules_engine import category_label, key_condition, inr

SYSTEM_PROMPT = (
    "Help the shopper understand this purchase decision. Choose the most useful "
    "reason and caution from the supplied options, based on the purchase and reward. "
    "Prefer a reason explaining why the card leads or qualifies, and a caution "
    "about the most relevant constraint or redemption type. Return ONLY a JSON "
    "object containing exactly card_id, benefit_inr, reward_form, reason_id, "
    "caution_id. Copy card_id, benefit_inr and reward_form exactly from recommended. "
    "Choose one reason_id and one caution_id from their respective option maps. "
    "Do not calculate, invent claims, change the recommendation or add prose."
)


def build_payload(win, second, amount, cat):
    form = win.card.get("reward_label", "Cashback")
    reasons = {"eligibility": win.reason}
    if second and second.comparable and getattr(second, "available", True) and win.benefit > second.benefit:
        reasons["advantage"] = (
            f"For this purchase, the estimated reward is {inr(win.benefit-second.benefit)} "
            f"higher than {second.card['name']}."
        )
    if win.cap_left_after is not None:
        reasons["remaining_cap"] = (
            f"Based on the entered cap usage, the estimated remaining applicable "
            f"reward allowance after this purchase is {inr(win.cap_left_after)}."
        )
    cautions = {"issuer_condition": key_condition(win)}
    if form == "Amazon Pay balance":
        cautions["redemption"] = "The reward is Amazon Pay balance, not cash credited to your bank."
    elif form.startswith("Scapia Coins"):
        cautions["redemption"] = "The estimate is Scapia travel redemption value, not cash."
    elif form.startswith("Kiwis"):
        cautions["redemption"] = "Kiwi rewards depend on eligible Kiwi payments and your remaining monthly allowance."
    return {
        "recommended": {"card_id": win.card["id"], "card": win.card["name"],
                        "benefit_inr": round(float(win.benefit), 2), "reward_form": form},
        "purchase": {"amount_inr": amount, "category": category_label(cat), "channel": win.channel},
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


def render_approved(selection, payload):
    r = payload["recommended"]
    return (
        f"{r['card']} offers an estimated {inr(r['benefit_inr'])} in "
        f"{r['reward_form'].lower()} for this purchase. "
        + payload["reason_options"][selection["reason_id"]] + " "
        + payload["caution_options"][selection["caution_id"]]
    )


AI_REQUEST_TIMEOUT_MS = 6000
GEMINI_API_VERSION = "v1beta"


def _generation_options(model):
    """Choose low latency settings without changing financial grounding."""
    config = {"system_instruction": SYSTEM_PROMPT, "temperature": 0.1,
              "max_output_tokens": 400, "response_mime_type": "application/json"}
    if model.startswith(("gemini-3.8-flash", "gemini-3.7-flash")):
        # 3.8 Flash defaults to medium and deprecates custom sampling.
        config.pop("temperature", None)
        config["thinking_config"] = {"thinking_level": "low"}
        config["max_output_tokens"] = 1024
    elif "2.5" in model and "flash" in model:
        config["thinking_config"] = {"thinking_budget": 0}
    return config


def _call_gemini(prompt, api_key, model):
    from google import genai
    from google.genai import types
    config = _generation_options(model)
    if "thinking_config" in config:
        config["thinking_config"] = types.ThinkingConfig(**config["thinking_config"])
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            api_version=GEMINI_API_VERSION,
            timeout=AI_REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    response = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(**config)
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
    diag["api_version"] = GEMINI_API_VERSION
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
