"""Public card library; issuer source and visual attribution are separate."""
import streamlit as st
from cards import CARDS
from rules_engine import highlight,inr
from ui import grid
from visuals import card_art,IMAGES
st.markdown('<div class="fin-eyebrow">Reference catalogue</div><div class="fin-heading">Explore supported cards.</div><div class="fin-copy">Seven products with distinct reward rules. Review the issuer terms before relying on an estimate.</div>',unsafe_allow_html=True)
issuer=st.selectbox("Filter by issuer",["All issuers"]+sorted({c["issuer"] for c in CARDS}))
shown=[c for c in CARDS if issuer=="All issuers" or c["issuer"]==issuer]
for i in range(0,len(shown),3):
    batch=shown[i:i+3]
    for slot,c in zip(grid(len(batch),mobile=1),batch):
        with slot:
            with st.container(border=True):
                st.markdown(card_art(c),unsafe_allow_html=True)
                st.markdown("**"+c["name"]+"**")
                st.write(highlight(c))
                st.caption("Annual fee before tax: "+inr(c["fee"])+" · "+c.get("reward_label","Cashback"))
                with st.expander("Conditions and source"):
                    st.write(c["caveat"])
                    st.caption("Issuer source review: "+c["last_verified"])
                    for j,source in enumerate(c["sources"],1):
                        st.link_button(f"Issuer terms {j}",source)
                    st.link_button("Card image reference",IMAGES[c["id"]]["source"])
st.caption("Card imagery and issuer website icons are for identification. All marks belong to their owners. Not affiliated with any issuer. Missing images use a labeled illustration. Review issuer terms and actual merchant classification.")
