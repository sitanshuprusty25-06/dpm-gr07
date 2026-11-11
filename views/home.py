"""Landing page with a live, eligible example sourced from the same rule engine."""
import streamlit as st
from cards import CARDS
from results import others_html,panel_html
from rules_engine import rank,inr,category_label
from ui import grid,section

ranked=rank(CARDS,"dining",8000,channel="online")
left,right=grid(2,desktop=[6,5],gap="large")
with left:
    st.markdown('<div class="cca-hero"><div class="kicker">A focused card-decision assistant</div>'
                '<h1>Know which of your cards to use, <em>before</em> you pay.</h1>'
                '<p>Select cards you already own. Enter one purchase. Compare indicative eligible cashback and see the conditions.</p></div>',
                unsafe_allow_html=True)
    if st.button("Compare my cards",type="primary",use_container_width=True):
        st.switch_page("views/compare.py")
    st.caption("No bank login, no saved wallet, no transaction-history integration.")
with right:
    st.caption(f"Worked example: {inr(8000)} in {category_label('dining').lower()}, online, cap assumed unused.")
    st.markdown(panel_html(ranked[0],ranked[1],8000,"dining"),unsafe_allow_html=True)
    st.markdown(others_html(ranked,True),unsafe_allow_html=True)

section("How it works","One purchase-level workflow")
for col,(title,desc) in zip(grid(3),[
    ("1 · Pick your cards","Choose from the supported issuer products."),
    ("2 · Enter the purchase","Amount, category and online/in-store channel; optionally specify already earned cashback."),
    ("3 · Read the result","Rule-based cashback and its key limitation; Gemini can optionally explain the result.")
]):
    col.markdown(f'<div class="cca-card"><h3>{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
st.warning("Card terms are conditional on issuer classifications. Some ambiguous purchases are intentionally not ranked.")
