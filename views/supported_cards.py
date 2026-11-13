"""Public catalogue with consistent card sections and official sources."""
import streamlit as st
from cards import CARDS
from rules_engine import highlight,inr
from ui import grid,page_heading
from visuals import library_card
from display_text import review_date
page_heading("Supported cards","Find your exact card and check its reward structure, fees and issuer terms.")
issuer=st.selectbox("Filter by issuer",["All issuers"]+list(dict.fromkeys(c["issuer"] for c in CARDS)))
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
                    st.caption("Issuer terms reviewed: "+review_date(c["last_verified"])+" · Links checked: "+review_date(c.get("links_checked_on",c["last_verified"])))
                    for j,source in enumerate(c["sources"],1):
                        labels=c.get("source_labels",[])
                        st.link_button(labels[j-1] if j<=len(labels) else f"Issuer terms {j}",source)
st.caption("Product imagery and issuer icons are for identification. Independent academic MVP; no bank affiliation. Unavailable artwork uses a labeled illustration. Actual merchant eligibility and issuer terms apply.")
