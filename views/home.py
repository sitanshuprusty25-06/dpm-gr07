"""Product-first landing page."""
import streamlit as st
from cards import CARDS
from results import panel_html,others_html
from rules_engine import rank
from ui import grid,section
from visuals import card_art
st.markdown('<div class="fin-eyebrow">Compare before you pay</div>',unsafe_allow_html=True)
left,right=grid(2,desktop=[5,5],gap="large")
with left:
    st.markdown('<div class="fin-heading">Make every payment count.</div><div class="fin-copy">The right card depends on what you buy, where you pay and which reward caps remain. Compare your own cards before checkout.</div>',unsafe_allow_html=True)
    st.write("")
    if st.button("Compare my cards",type="primary",use_container_width=True):
        st.switch_page("views/compare.py")
    st.markdown('<span class="fin-pill">No bank login</span><span class="fin-pill">No saved wallet</span><span class="fin-pill">Issuer-linked terms</span>',unsafe_allow_html=True)
    st.caption("Independent academic MVP · indicative estimates, not guaranteed rewards.")
with right:
    sample=[c for c in CARDS if c["id"] in ("swiggy_ornge","swiggy_blck","sbi_cashback")]
    ranked=rank(sample,"dining",1200,channel="online",merchant_type="swiggy")
    st.caption("Live worked example · eligible ₹1,200 Swiggy order · unused caps")
    st.markdown(panel_html(ranked[0],ranked[1],1200,"dining"),unsafe_allow_html=True)
    st.markdown(others_html(ranked,True),unsafe_allow_html=True)
section("Recognise your cards","Choose from 10 supported products. Card images are for identification only.")
for i in range(0,len(CARDS),4):
    batch=CARDS[i:i+4]
    for slot,c in zip(grid(4,mobile=1),batch):
        with slot:
            st.markdown(card_art(c),unsafe_allow_html=True)
            st.markdown("**"+c["name"]+"**")
            st.caption(c.get("headline",""))
if st.button("Browse the card library"):
    st.switch_page("views/supported_cards.py")
section("One purchase. Three steps.")
for slot,(title,detail) in zip(grid(3),[
    ("01 · Know","Choose the cards you already own."),
    ("02 · Compare","Enter amount, category and the relevant merchant route."),
    ("03 · Decide","See the reward estimate, restrictions and optional Gemini explanation.")
]):
    slot.markdown(f'<div class="cca-card"><h3>{title}</h3><p>{detail}</p></div>',unsafe_allow_html=True)
