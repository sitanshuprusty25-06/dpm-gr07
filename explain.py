"""The single GenAI capability: write a plain-language explanation of a computed result.

GenAI does not calculate, rank or recommend. Every number in its text is checked
against the rules output. On any mismatch (or any failure) we fall back to a
template built directly from the rules output.
"""

import json
import re

from rules_engine import inr

NUMBER_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?")

SYSTEM_PROMPT = (
    "You explain the result of a credit card benefit calculation to a customer in plain, "
    "friendly English. Strict rules: "
    "(1) Use only the facts provided. Do not calculate anything yourself. "
    "(2) Every number you write (rupee amounts and percentages) must appear in the facts "
    "exactly as given. Write no other digits: no dates, no ordinals, no counts. "
    "(3) Name the top card exactly as given. "
    "(4) Explain WHY it gives the highest benefit, state its key condition, and say what "
    "could change the result. "
    "(5) Call the figure an estimate. "
    "(6) Do not claim it is the best card overall; it is the most beneficial among the "
    "cards the user selected. "
    "(7) 2 to 4 short sentences, plain text, no bullet points, no markdown."
)


def _numbers_in(text):
    return [float(m.replace(",", "")) for m in NUMBER_RE.findall(text)]


def allowed_numbers(ranked):
    allowed = set()
    for r in ranked:
        for v in r.facts.values():
            if isinstance(v, (int, float)):
                allowed.add(round(float(v), 2))
    return allowed


def numbers_match(text, ranked, top_name):
    """True if the text names the top card and every number in it is an allowed fact."""
    if top_name not in text:
        return False
    cleaned = text.replace(top_name, " ")
    allowed = allowed_numbers(ranked)
    for n in _numbers_in(cleaned):
        if not any(abs(n - a) < 0.005 for a in allowed):
            return False
    return True


def template_explanation(ranked, amount, category):
    """Plain explanation built only from the rules output."""
    top = ranked[0]
    if top.benefit <= 0:
        reasons = "; ".join(f"{r.name}: {r.reason}" for r in ranked)
        return (
            f"None of the cards you selected earns a reward on this {inr(amount)} "
            f"{category} purchase. {reasons}"
        )
    text = (
        f"For this {inr(amount)} {category} purchase, {top.name} gives the most benefit "
        f"among your selected cards: about {inr(top.benefit)} (an estimate). "
        f"{top.reason} {top.key_condition}"
    )
    if len(ranked) > 1:
        nxt = ranked[1]
        text += f" The next best is {nxt.name} at about {inr(nxt.benefit)}."
    return text


def _build_prompt(ranked, amount, category):
    top = ranked[0]
    payload = {
        "purchase": {"amount_rupees": amount, "category": category},
        "top_card": {
            "name": top.name,
            "estimated_benefit_rupees": top.benefit,
            "reason": top.reason,
            "key_condition": top.key_condition,
            "facts": top.facts,
        },
    }
    if len(ranked) > 1:
        nxt = ranked[1]
        payload["next_card"] = {
            "name": nxt.name,
            "estimated_benefit_rupees": nxt.benefit,
            "reason": nxt.reason,
        }
    return "Facts (JSON):\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def _call_gemini(prompt, api_key, model):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=400,
        ),
    )
    return (resp.text or "").strip()


def build_explanation(ranked, amount, category, api_key=None, model="gemini-2.5-flash"):
    """Return (text, source). source is one of:
    "ai" (verified GenAI text), "template_no_key", "template_ai_error",
    "template_check_failed", "template_no_reward".
    """
    template = template_explanation(ranked, amount, category)
    if ranked[0].benefit <= 0:
        return template, "template_no_reward"
    if not api_key:
        return template, "template_no_key"
    try:
        text = _call_gemini(_build_prompt(ranked, amount, category), api_key, model)
    except Exception:
        return template, "template_ai_error"
    if text and numbers_match(text, ranked, ranked[0].name):
        return text, "ai"
    return template, "template_check_failed"
