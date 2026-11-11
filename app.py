"""GenAI Card Choice Assistant: V1 (Group 07, DPM, IIM Visakhapatnam).

One user (selective comparer), one problem, one use case (check a purchase before
paying), one workflow, one AI capability (plain-language explanation).
"""

import os

import streamlit as st

from cards import CARDS, CATEGORIES
from explain import build_explanation
from rules_engine import evaluate_all, inr

st.set_page_config(page_title="Card Choice Assistant", page_icon="💳", layout="centered")

SOURCE_LABELS = {
    "ai": "Written by GenAI. Every number was checked against the rules.",
    "template_no_key": "Standard explanation built from the rules (GenAI is not configured).",
    "template_ai_error": "Standard explanation built from the rules (GenAI was unavailable).",
    "template_check_failed": (
        "Standard explanation built from the rules (the GenAI text failed the number check)."
    ),
    "template_no_reward": "Standard explanation built from the rules.",
}


def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


cards_by_name = {c["name"]: c for c in CARDS}

st.title("Card Choice Assistant")
st.write(
    "Check a purchase before you pay. Pick the cards you hold, enter the purchase, and see "
    "which of them gives the most benefit and why."
)
st.info(
    "V1 compares only the sample cards listed below, using dated rules. It does not link "
    "to your bank, and it never asks for a card number, expiry or CVV."
)

# Step 1: cards held
st.subheader("1. Which cards do you hold?")
selected_names = st.multiselect(
    "Supported cards",
    options=list(cards_by_name.keys()),
    help="Other cards are not compared.",
)

# Step 2: purchase
st.subheader("2. What are you about to buy?")
col_a, col_b = st.columns(2)
amount = col_a.number_input("Purchase amount (₹)", min_value=0.0, step=100.0, format="%.0f")
category = col_b.selectbox("Category", CATEGORIES)

cap_used_by_card = {}
with st.expander("Optional: bonus already used this month"):
    st.caption(
        "V1 does not track your spending. If you leave this at 0, it assumes the monthly "
        "bonus cap is unused."
    )
    for name in selected_names:
        cap_used_by_card[cards_by_name[name]["id"]] = st.number_input(
            f"{name}: bonus already earned this month (₹)",
            min_value=0.0,
            step=50.0,
            format="%.0f",
            key=f"used_{cards_by_name[name]['id']}",
        )
    if not selected_names:
        st.caption("Select a card first.")

if st.button("Compare my cards", type="primary"):
    if not selected_names:
        st.error("Select at least one card.")
        st.session_state.pop("result", None)
    elif amount <= 0:
        st.error("Enter a purchase amount greater than 0.")
        st.session_state.pop("result", None)
    else:
        selected = [cards_by_name[n] for n in selected_names]
        ranked = evaluate_all(selected, amount, category, cap_used_by_card)
        with st.spinner("Applying card rules..."):
            text, source = build_explanation(
                ranked,
                amount,
                category,
                api_key=get_secret("GEMINI_API_KEY"),
                model=get_secret("GEMINI_MODEL", "gemini-2.5-flash"),
            )
        st.session_state["result"] = {
            "ranked": ranked,
            "amount": amount,
            "category": category,
            "text": text,
            "source": source,
        }

# Step 3: result
result = st.session_state.get("result")
if result:
    ranked = result["ranked"]
    top = ranked[0]
    st.divider()
    st.subheader("3. Result")
    st.caption(f"{inr(result['amount'])} on {result['category']}")

    with st.container(border=True):
        if top.benefit > 0:
            st.markdown(f"**Most beneficial eligible card: {top.name}**")
            st.metric("Estimated benefit", inr(top.benefit))
        else:
            st.markdown("**None of your selected cards earns a reward on this purchase.**")
        st.markdown(f"**Key condition:** {top.key_condition}")

    st.markdown("**All your selected cards, ranked by estimated rupee benefit**")
    for i, r in enumerate(ranked, start=1):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"{i}. **{r.name}**  \n{r.reason}")
        c2.markdown(f"**{inr(r.benefit)}**")

    st.markdown("**Why**")
    st.write(result["text"])
    st.caption(SOURCE_LABELS[result["source"]])

    st.caption(
        f"Rules last verified {top.last_verified}. Source: {top.source}. Results are "
        "estimates for the supported cards and dated rules, not a guarantee of reward. "
        "Only your own selected cards are compared; no card issuer or sponsor can change "
        "this order."
    )

st.divider()
st.caption(
    "Group 07, Digital Product Management, IIM Visakhapatnam. Nothing you enter is stored."
)
