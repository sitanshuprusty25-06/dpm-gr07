"""The single GenAI capability: reword a computed result in plain language.

GenAI does not calculate, rank or recommend. It only rewords facts the rules engine has
already produced. Every number in its text is checked against those facts. If anything
differs, the user keeps the rule-based explanation.
"""

import json
import re

from rules_engine import category_label, key_condition, rnd

NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

SYSTEM_PROMPT = (
    "You explain a credit card recommendation to a shopper in 2 or 3 short, plain "
    "sentences. Use ONLY the facts in the JSON. Do not calculate anything yourself. "
    "Every number you write must appear in the JSON exactly as given; write no other "
    "digits (no dates, counts or ordinals). Use the recommended card's name exactly as "
    "given. Call the figure an estimate. Say why this card gives the most benefit among "
    "the cards the shopper selected, and state its key condition. Do not claim it is the "
    "best card overall. Do not give general financial advice. Plain text only: no "
    "markdown, no bullet points."
)


def build_payload(win, second, amount, cat):
    """The only facts the model is allowed to use."""
    facts = {"base_rate_pct": win.card["base"]}
    rule = win.rule
    if rule:
        facts["bonus_rate_pct"] = rule["rate"]
        for key, name in (("cap", "monthly_cap_inr"), ("min", "min_purchase_inr"), ("max", "max_per_purchase_inr")):
            if rule.get(key):
                facts[name] = rule[key]
    if win.cap_left_after is not None:
        facts["cap_left_after_inr"] = rnd(win.cap_left_after)
    if win.points is not None:
        facts["points"] = rnd(win.points)
        facts["point_value_inr"] = win.card["point_value"]
    payload = {
        "recommended": {
            "card": win.card["name"],
            "issuer": win.card["issuer"],
            "benefit_inr": rnd(win.benefit),
            "reason": win.reason,
            "condition": key_condition(win),
        },
        "purchase": {"amount_inr": amount, "category": category_label(cat)},
        "facts": facts,
        "next_best": None,
    }
    if second:
        payload["next_best"] = {
            "card": second.card["name"],
            "benefit_inr": rnd(second.benefit),
            "advantage_inr": rnd(win.benefit - second.benefit),
        }
    return payload


def numbers_in(text):
    return [float(m.replace(",", "")) for m in NUMBER_RE.findall(text)]


def validate(text, payload):
    """True only if the text names the recommended card and every number in it appears
    in the payload."""
    allowed = numbers_in(json.dumps(payload, ensure_ascii=False))
    for n in numbers_in(text):
        if not any(abs(n - a) < 0.005 for a in allowed):
            return False
    return payload["recommended"]["card"] in text


def _call_gemini(prompt, api_key, model):
    from google import genai
    from google.genai import types

    config = {"system_instruction": SYSTEM_PROMPT, "temperature": 0.2, "max_output_tokens": 600}
    if "2.5" in model and "flash" in model:
        # Short rewording does not need "thinking"; it would use up the output budget.
        config["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config),
    )
    return (resp.text or "").strip()


def _hint(e, api_key):
    """A short, key-free description of why the call failed, plus what to try."""
    msg = str(e).replace(api_key, "***")[:300]
    low = msg.lower()
    if isinstance(e, ImportError):
        advice = "The google-genai package is not installed. Check requirements.txt and reboot the app."
    elif "api key" in low or "api_key_invalid" in low or "401" in low or "403" in low or "permission" in low:
        advice = "Google rejected the key. Check it was copied fully, has no spaces, and is enabled."
    elif "429" in low or "quota" in low or "resource_exhausted" in low or "rate" in low:
        advice = "Rate or quota limit reached. Wait a minute and try again."
    elif "404" in low or "not found" in low or "model" in low:
        advice = "The model name was not accepted. Add GEMINI_MODEL = \"gemini-2.0-flash\" to Secrets."
    elif "location" in low or "not supported" in low:
        advice = "Gemini API may not be available for this key or region."
    else:
        advice = "See Manage app logs for details."
    return f"{type(e).__name__}: {msg}. {advice}"


def ai_reword(win, second, amount, cat, api_key, model="gemini-2.5-flash"):
    """Return (text, status, detail). status is "ok", "no_key", "error" or "mismatch".
    text is None unless status is "ok". detail explains an "error" (never contains the key)."""
    if not api_key:
        return None, "no_key", ""
    api_key = str(api_key).strip()
    payload = build_payload(win, second, amount, cat)
    try:
        text = _call_gemini(json.dumps(payload, ensure_ascii=False, indent=2), api_key, model)
    except Exception as e:
        detail = _hint(e, api_key)
        print(f"Gemini call failed: {detail}")  # also in the Streamlit "Manage app" logs
        return None, "error", detail
    if text and validate(text, payload):
        return text, "ok", ""
    return None, "mismatch", ""
