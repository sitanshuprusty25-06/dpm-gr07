"""Read-only public issuer card catalogue and evidence links."""
import html
import streamlit as st
from cards import CARDS,CATEGORIES
from rules_engine import highlight,inr
from ui import grid,is_mobile

st.markdown("## Supported cards and issuer sources")
st.caption("Five issuer products, with dated reference rules and recorded limitations. No customer information is stored in this catalogue.")
NCOLS=1 if is_mobile() else 3
cols=grid(NCOLS)
for i,c in enumerate(CARDS):
    with cols[i%NCOLS]:
        st.markdown(f'<div class="cca-card"><h3>{html.escape(c["name"])}</h3>'
                    f'<p>{html.escape(c["issuer"])} · {html.escape(highlight(c))}</p>'
                    f'<p>Annual card fee (not deducted per purchase): {inr(c["fee"])}. '
                    f'Source review: {c["last_verified"]}.</p>'
                    f'<p>{html.escape(c["caveat"])}</p></div>',unsafe_allow_html=True)
        st.link_button(f"Official source: {c['issuer']}",c["source"])
        with st.expander(f"Additional source links for {c['name']}"):
            for source in c["sources"]:
                st.write(source)
st.info("Reference terms do not replace checking your issuer statement and merchant MCC. "
        "Group 07 should independently reconfirm every card rule before assessed submission.")
