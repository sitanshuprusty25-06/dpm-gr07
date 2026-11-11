"""Supported cards: the catalogue the rules engine reads (the KNOW layer), with dates and sources."""

import html

import streamlit as st

from cards import CARDS, CATEGORIES, SAMPLE_DATA
from rules_engine import category_label, inr, pct
from ui import grid, is_mobile


st.markdown("## Supported cards")
st.caption(
    "Only these cards are compared in V1. Each one shows the rules the app uses, the date they "
    "were last checked and where they came from."
)
if SAMPLE_DATA:
    st.info("These are fictional sample cards used to demonstrate the product. They are not real issuer terms.")

options = ["All categories"] + [label for _, label in CATEGORIES]
choice = st.selectbox("Show cards with a bonus on", options)
cat_id = next((cid for cid, label in CATEGORIES if label == choice), None)

shown = [c for c in CARDS if cat_id is None or cat_id in c["rules"]]
if not shown:
    st.markdown('<div class="cca-empty">No supported card has a bonus in this category yet.</div>',
                unsafe_allow_html=True)

NCOLS = 1 if is_mobile() else 4
cols = [st.container()] * NCOLS if is_mobile() else grid(NCOLS)
for i, c in enumerate(shown):
    items = []
    for cat, r in c["rules"].items():
        bits = [f"{pct(r['rate'])} on {category_label(cat).lower()}"]
        if r.get("cap"):
            bits.append(f"cap {inr(r['cap'])} a month")
        if r.get("min"):
            bits.append(f"min {inr(r['min'])}")
        if r.get("max"):
            bits.append(f"first {inr(r['max'])} per purchase")
        items.append("<li>" + html.escape(", ".join(bits)) + "</li>")
    items.append(f"<li>{pct(c['base'])} on everything else</li>")
    if c["excl"]:
        names = ", ".join(category_label(k).lower() for k in c["excl"])
        items.append(f"<li>No reward on {html.escape(names)}</li>")
    fee = "No annual fee" if c["fee"] == 0 else f"Annual fee {inr(c['fee'])}"
    cols[i % NCOLS].markdown(
        '<div class="cca-card">'
        f'<div class="cca-chiprow"><span class="cca-swatch" style="background:{c["hue"]}"></span>'
        f'<div><div class="cca-cn">{html.escape(c["name"])}</div>'
        f'<div class="cca-cs">{html.escape(c["issuer"])} · {fee}</div></div></div>'
        f'<ul>{"".join(items)}</ul>'
        f'<p style="margin-top:10px;font-size:.88rem">Checked {c["last_verified"]}. '
        f'{html.escape(c["source"])}</p></div>',
        unsafe_allow_html=True,
    )
    cols[i % NCOLS].write("")

st.markdown("### Missing a card?")
st.write(
    "V1 supports a small, hand-checked set of cards. Each added card must be verified against the "
    "issuer's published terms first. Adding more cards is on the roadmap."
)
st.page_link("views/roadmap.py", label="See the roadmap")
