"""How it works: the rules / AI / checker design, in plain language."""

import streamlit as st

from ui import grid, section

st.markdown("## How a recommendation is made")
st.caption("The maths is done by rules. AI is used for one thing only: wording.")

c1, c2, c3 = st.columns(3)
steps = [
    ("1", "Rules decide",
     "A rules engine reads each card's bonus rate, monthly cap, minimum spend, per-purchase limit and "
     "excluded categories, then works out the rupee benefit. No AI is involved in the maths, so the "
     "same input always gives the same answer."),
    ("2", "AI explains (optional)",
     "If you press “Reword with AI”, the computed result is sent to a language model (Google Gemini). "
     "It may only reword the facts it is given. It does not calculate, rank or recommend."),
    ("3", "A checker verifies",
     "Every number in the AI text must match the rules output, and the card must be named correctly. "
     "If anything differs, you keep the rule-based explanation."),
]
for col, (n, title, body) in zip((c1, c2, c3), steps):
    col.markdown(
        f'<div class="cca-card"><span class="cca-num">{n}</span><h3>{title}</h3><p>{body}</p></div>',
        unsafe_allow_html=True,
    )

section("A worked example")
st.markdown(
    "You hold a card that gives **5%** on online shopping, up to **₹500** of bonus a month, and "
    "**1%** otherwise. You buy something for **₹12,000**."
)
st.markdown(
    "- The first ₹10,000 earns 5%, which is ₹500 and uses up the monthly cap.\n"
    "- The remaining ₹2,000 earns 1%, which is ₹20.\n"
    "- **Total: about ₹520**, not the ₹600 a flat 5% would suggest. That gap is why the cap is shown as the "
    "“Watch out” condition."
)

section("What the app promises, and what it does not")
a, b = st.columns(2)
with a:
    st.markdown(
        '<div class="cca-card"><h3>It does</h3><ul>'
        "<li>Compare only the cards you say you hold</li>"
        "<li>Show the key condition before you pay</li>"
        "<li>Show when the card terms were last checked, and the source</li>"
        "<li>Break exact ties by the lower annual fee</li></ul></div>",
        unsafe_allow_html=True,
    )
with b:
    st.markdown(
        '<div class="cca-card"><h3>It does not</h3><ul>'
        "<li>Ask for card numbers, expiry or CVV</li>"
        "<li>Link to your bank or read your transactions</li>"
        "<li>Take payment from banks or merchants to change the order</li>"
        "<li>Guarantee the reward: results are estimates</li></ul></div>",
        unsafe_allow_html=True,
    )

if st.button("Try it now", type="primary"):
    st.switch_page("views/compare.py")
