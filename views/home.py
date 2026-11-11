"""Home: what the product is, a live example, how it works, and a way in."""

import streamlit as st

from cards import CARDS, DEFAULT_WALLET
from results import others_html, panel_html, watch_html
from rules_engine import category_label, inr, rank
from ui import grid, section

HERO = (
    '<div class="cca-hero"><div class="kicker">For people who hold more than one credit card</div>'
    "<h1>Know which card to pay with, <em>before</em> you pay.</h1>"
    "<p>Pick the cards you already hold, enter a purchase, and see which one gives the most "
    "benefit in rupees, what to watch out for, and why.</p></div>"
)

# Live example computed by the same rules engine the Compare page uses.
wallet = [c for c in CARDS if c["id"] in DEFAULT_WALLET] or CARDS[:4]
if len(wallet) < 2:
    wallet = CARDS
EX_AMOUNT, EX_CAT = 12000, "shopping"
ranked = rank(wallet, EX_CAT, EX_AMOUNT) if len(wallet) >= 2 else []
has_live = bool(ranked) and ranked[0].benefit > 0.005 and any(EX_CAT in c["rules"] for c in wallet)

if has_live:
    hero_col, live_col = grid(2, desktop=[6, 5], gap="large")
else:
    hero_col, live_col = st.container(), None

with hero_col:
    st.markdown(HERO, unsafe_allow_html=True)
    b1, b2 = st.columns(2)
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

if live_col is not None:
    with live_col:
        st.caption(
            f"Live example: {inr(EX_AMOUNT)} on {category_label(EX_CAT).lower()}, calculated by the "
            "same rules engine as the Compare page."
        )
        st.markdown(panel_html(ranked[0], ranked[1], EX_AMOUNT, EX_CAT), unsafe_allow_html=True)
        st.markdown(watch_html(ranked[0]), unsafe_allow_html=True)
        st.markdown(others_html(ranked, True), unsafe_allow_html=True)

section("How it works", "Three steps, about thirty seconds.")
c1, c2, c3 = grid(3)
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

section("What you get")
f1, f2, f3 = grid(3)
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
