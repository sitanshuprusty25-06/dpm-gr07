"""Public catalogue with consistent card sections and official sources."""
import streamlit as st
from cards import CARDS
from rules_engine import highlight,inr
from ui import grid
from visuals import library_card,IMAGES
st.markdown('<div class="fin-eyebrow">Reference catalogue</div><div class="fin-heading">Explore supported cards.</div><div class="fin-copy">Compare the reward structures, annual fees and conditions of each supported product.</div>',unsafe_allow_html=True)
issuer=st.selectbox("Filter by issuer",["All issuers"]+sorted({c["issuer"] for c in CARDS}))
shown=[c for c in CARDS if issuer=="All issuers" or c["issuer"]==issuer]
st.caption(f"{len(shown)} of {len(CARDS)} supported cards · listed annual fees before tax; waivers and current terms may vary.")
if st.button("Compare cards I own",type="primary"):
    st.switch_page("views/compare.py")
for i in range(0,len(shown),3):
    batch=shown[i:i+3]
    for slot,c in zip(grid(3,mobile=1),batch):
        with slot:
            with st.container(border=True):
                st.markdown(library_card(c,highlight(c),inr(c["fee"])),unsafe_allow_html=True)
                with st.expander("Conditions and source"):
                    st.write(c["caveat"])
                    st.caption("Issuer source review: "+c["last_verified"])
                    for j,source in enumerate(c["sources"],1):
                        st.link_button(f"Issuer terms {j}",source)
                    st.link_button("Card image reference",IMAGES[c["id"]]["source"])
st.caption("Product imagery and issuer icons are for identification. Independent academic MVP; no bank affiliation. Unavailable artwork uses a labeled illustration. Actual merchant eligibility and issuer terms apply.")
