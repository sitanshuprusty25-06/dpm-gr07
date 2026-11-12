"""Product-first landing page."""
import streamlit as st
from cards import CARDS
from results import panel_html,others_html
from rules_engine import rank
from ui import grid,section,page_heading
from visuals import card_art
left,right=grid(2,desktop=[5,5],gap="large")
with left:
    page_heading("Choose a card with less guesswork.","Compare the rewards on cards you already own for one purchase, before checkout.")
    if st.button("Compare my cards",type="primary",use_container_width=True):
        st.switch_page("views/compare.py")
    st.markdown('<span class="fin-pill">No bank login</span><span class="fin-pill">No saved wallet</span><span class="fin-pill">Issuer-linked terms</span>',unsafe_allow_html=True)
    st.caption("Independent academic MVP · indicative estimates, not guaranteed rewards.")
with right:
    sample=[c for c in CARDS if c["id"] in ("swiggy_ornge","swiggy_blck","sbi_cashback")]
    ranked=rank(sample,"dining",1200,channel="online",merchant_type="swiggy")
    st.caption("Worked example · eligible ₹1,200 Swiggy order · unused caps")
    st.markdown(panel_html(ranked[0],ranked[1],1200,"dining"),unsafe_allow_html=True)
    st.markdown(others_html(ranked,True),unsafe_allow_html=True)
section("One purchase. Three steps.")
for slot,(title,detail) in zip(grid(3),[
    ("01 · Know","Choose the cards you already own."),
    ("02 · Compare","Enter amount, category and the relevant merchant route."),
    ("03 · Decide","See the reward estimate, optional checked AI explanation and restrictions in one result.")
]):
    slot.markdown(f'<div class="cca-card"><h3>{title}</h3><p>{detail}</p></div>',unsafe_allow_html=True)

section("Supported cards","Browse the catalogue to find your exact card.")
featured=CARDS[:3]
for slot,c in zip(grid(3,mobile=1),featured):
    with slot:
        st.markdown(card_art(c),unsafe_allow_html=True)
        st.markdown("**"+c["name"]+"**")
if st.button("Browse all supported cards",use_container_width=True):
    st.switch_page("views/supported_cards.py")
