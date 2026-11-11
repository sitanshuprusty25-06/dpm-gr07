"""About & contact: who built this and why. Team details are placeholders to fill in."""

import streamlit as st

from ui import grid, section

st.markdown("## About & contact")

a, b = grid(2, desktop=[3, 2], gap="large")
with a:
    st.markdown(
        '<div class="cca-card"><h3>Why we built this</h3>'
        "<p>Many people hold two or more credit cards, each with different bonus rates, monthly caps and "
        "exclusions. Picking the right one at the moment of payment is slow and uncertain, so most people "
        "just use whatever is on top. Card Choice Assistant checks a purchase against the cards you "
        "already hold and tells you which one is worth using, what to watch out for, and why.</p></div>",
        unsafe_allow_html=True,
    )
    section("This project")
    st.markdown(
        "Built by **Group 07** for **Digital Product Management**, EMBA 2025-27, "
        "**Indian Institute of Management Visakhapatnam**. This is an academic V1 (minimum viable product), "
        "not a commercial service, and it is not financial advice."
    )
with b:
    st.markdown(
        '<div class="cca-card"><h3>Contact</h3>'
        "<p>Team email: <i>add your group email here</i><br>"
        "Feedback form: <i>add your form link here</i><br>"
        "Source code: <i>add your GitHub link here</i></p></div>",
        unsafe_allow_html=True,
    )

section("The team")
cols = grid(5, mobile=2)
for i, col in enumerate(cols, start=1):
    col.markdown(
        f'<div class="cca-card"><div class="cca-cn">Team member {i}</div>'
        '<div class="cca-cs">Name and role to be added</div></div>',
        unsafe_allow_html=True,
    )
