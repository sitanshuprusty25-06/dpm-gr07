"""Public catalogue with consistent card sections and official sources."""
import streamlit as st
from cards import CARDS,MARKET
from rules_engine import highlight,inr
from ui import grid
from visuals import library_card,IMAGES
st.markdown('<div class="fin-eyebrow">Reference catalogue</div><div class="fin-heading">Explore supported cards.</div><div class="fin-copy">Compare the reward structures, annual fees and conditions of each supported product.</div>',unsafe_allow_html=True)
issuer=st.selectbox("Filter by issuer",["All issuers"]+list(dict.fromkeys(c["issuer"] for c in CARDS)))
shown=[c for c in CARDS if issuer=="All issuers" or c["issuer"]==issuer]
st.caption(f"{len(shown)} of {len(CARDS)} supported cards · listed annual fees before tax; waivers and current terms may vary.")
st.caption("Browsing order: published product adoption first, then issuer footprint. This is not a complete product popularity ranking.")
with st.expander("Market data and ordering method"):
    st.write(MARKET["method"])
    for cid,evidence in MARKET["product_disclosures"].items():
        card=next(c for c in CARDS if c["id"]==cid)
        st.write(card["name"]+": "+evidence["label"]+" ("+evidence["period"]+")")
        st.link_button("Product adoption source · "+card["name"],evidence["source"])
    st.caption("RBI issuer totals, September 2026 · all credit-card products, not this individual card")
    st.table([{"Issuer":issuer_name,"Cards outstanding (million)":count} for issuer_name,count in MARKET["issuer_cards_million"].items()])
    st.link_button("RBI bank-wise statistics",MARKET["issuer_source"])
    st.link_button("RBI data cross-check",MARKET["issuer_crosscheck"])
    st.caption("Market figures do not influence purchase recommendations.")
if st.button("Compare cards I own",type="primary"):
    st.switch_page("views/compare.py")
for i in range(0,len(shown),3):
    batch=shown[i:i+3]
    for slot,c in zip(grid(3,mobile=1),batch):
        with slot:
            with st.container(border=True):
                st.markdown(library_card(c,highlight(c),inr(c["fee"])),unsafe_allow_html=True)
                evidence=MARKET["product_disclosures"].get(c["id"])
                if evidence:
                    st.caption(evidence["label"]+" · "+evidence["period"])
                with st.expander("Conditions and source"):
                    st.write(c["caveat"])
                    st.caption("Issuer source review: "+c["last_verified"])
                    for j,source in enumerate(c["sources"],1):
                        st.link_button(f"Issuer terms {j}",source)
                    st.link_button("Card image reference",IMAGES[c["id"]]["source"])
st.caption("Product imagery and issuer icons are for identification. Independent academic MVP; no bank affiliation. Unavailable artwork uses a labeled illustration. Actual merchant eligibility and issuer terms apply.")
