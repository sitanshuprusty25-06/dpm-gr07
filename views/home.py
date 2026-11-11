"""Home: what the product is, how it works, a live example, and a way in."""

import streamlit as st

from cards import CARDS, DEFAULT_WALLET
from results import others_html, panel_html, watch_html
from rules_engine import category_label, inr, rank
from ui import grid, is_mobile, section

st.markdown(
    '<div class="cca-hero"><div class="kicker">For people who hold more than one credit card</div>'
    "<h1>Know which card to pay with, <em>before</em> you pay.</h1>"
    "<p>Pick the cards you already hold, enter a purchase, and see which one gives the most "
    "benefit in rupees, what to watch out for, and why.</p></div>",
    unsafe_allow_html=True,
)
b1, b2 = grid(2, mobile=1) if is_mobile() else st.columns([2, 2, 5])[:2]
if b1.button("Compare my cards", type="primary", use_container_width=True):
    st.switch_page("views/compare.py")
if b2.button("How it works", use_container_width=True):
    st.switch_page("views/how_it_works.py")

st.markdown(
    '<div class="cca-trust"><span>No card numbers, ever</span>'
    "<span>Only your own cards are ranked</span>"
    "<span>No bank or merchant can change the order</span>"
    "<span>Nothing you enter is stored</span></div>",
    unsafe_allow_html=True,
)

section("How it works", "Three steps, about thirty seconds.")
c1, c2, c3 = st.columns(3)
steps = [
    ("1", "Pick your cards", "Choose which of the supported cards you hold. We never ask for numbers, expiry or CVV."),
    ("2", "Enter the purchase", "Type the amount and choose a category, such as dining, travel or fuel."),
    ("3", "See the best card and why",
     "Get the card with the highest rupee benefit, the one condition to watch out for, and a plain explanation."),
]
for col, (n, title, body) in zip((c1, c2, c3), steps):
    col.markdown(
        f'<div class="cca-card"><span class="cca-num">{n}</span><h3>{title}</h3><p>{body}</p></div>',
        unsafe_allow_html=True,
    )

# Live example computed by the same rules engine the Compare page uses.
wallet = [c for c in CARDS if c["id"] in DEFAULT_WALLET] or CARDS[:4]
if len(wallet) < 2:
    wallet = CARDS
EX_AMOUNT, EX_CAT = 12000, "shopping"
if len(wallet) >= 2 and any(EX_CAT in c["rules"] for c in wallet):
    ranked = rank(wallet, EX_CAT, EX_AMOUNT)
    if ranked[0].benefit > 0.005:
        section("See it in action", "A real calculation from the rules engine, not a mock-up.")
        left, right = grid(2, desktop=[5, 6], gap="large")
        with left:
            st.markdown(
                f'<div class="cca-card"><h3>{inr(EX_AMOUNT)} on {category_label(EX_CAT).lower()}</h3>'
                f"<p>You hold {len(wallet)} cards. Several look similar, but their bonus rates, "
                "monthly caps and minimum spends are different. The winner is not always the card "
                "with the biggest headline rate.</p></div>",
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(panel_html(ranked[0], ranked[1], EX_AMOUNT, EX_CAT), unsafe_allow_html=True)
            st.markdown(watch_html(ranked[0]), unsafe_allow_html=True)
            st.markdown(others_html(ranked, True), unsafe_allow_html=True)

section("What you get")
f1, f2, f3 = st.columns(3)
features = [
    ("A rupee figure, not a guess", "Rewards are converted to rupees, including points, so cards can be compared on one scale."),
    ("The condition that matters", "Caps, minimum spends, per-purchase limits and excluded categories are shown before you pay."),
    ("A plain-language reason", "A short explanation of why this card wins. Optional AI wording is checked against the numbers."),
]
for col, (title, body) in zip((f1, f2, f3), features):
    col.markdown(f'<div class="cca-card"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)

section("Ready to try it?")
if st.button("Compare my cards now", type="primary", key="cta_bottom"):
    st.switch_page("views/compare.py")
