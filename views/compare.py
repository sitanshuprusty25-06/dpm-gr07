"""Stateless purchase comparison: selectors live only in Streamlit session state."""
import streamlit as st
from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, highlight, inr, rank, reward_bucket
from ui import is_mobile, keep, remember

cat_ids = [cid for cid, _ in CATEGORIES]
for card in CARDS:
    keep(f"w_{card['id']}", card["id"] in DEFAULT_WALLET)
keep("amount")
keep("cat","dining")
keep("channel","online")
keep("merchant_type","unknown")

st.markdown('<div class="cca-sec"><h2>Compare your cards</h2><p>One purchase. A clearer decision.</p></div>',unsafe_allow_html=True)
st.caption("Choose the cards you own and describe one domestic, non-EMI purchase. No card numbers or bank login.")

mobile = is_mobile()
left, right = (st.container(), st.container()) if mobile else st.columns([1,1],gap="large")
with left:
    with st.container(border=True):
        st.markdown("**1. Select your cards**")
        cols = None if mobile else st.columns(2)
        for i, c in enumerate(CARDS):
            with (st.container() if mobile else cols[i%2]):
                st.checkbox(f"{c['chip']} {c['name']}",key=f"w_{c['id']}")
                st.caption(c["issuer"]+" · "+highlight(c))
            remember(f"w_{c['id']}")
        selected = [c for c in CARDS if st.session_state.get(f"w_{c['id']}")]
        if not selected:
            st.info("Select one or more cards; only those selected will be compared.")
    with st.container(border=True):
        st.markdown("**2. Describe this purchase**")
        st.number_input("Amount (₹)",min_value=0,step=100,value=None,format="%d",key="amount",placeholder="e.g. 8000")
        st.radio("Purchase channel",["online","offline"],format_func=lambda v:"Online" if v=="online" else "Physical store",horizontal=True,key="channel")
        st.selectbox("Purchase category",cat_ids,format_func=category_label,key="cat")
        merchants={"unknown":"Not sure / merchant not classified","other":"Other eligible ordinary purchase (not a special merchant)","swiggy":"Swiggy eligible food / Instamart / Dineout","amazon_prime":"Amazon India shopping · Prime","amazon_nonprime":"Amazon India shopping · non-Prime","marketplace":"Flipkart / Myntra shopping","amazon_pay":"Eligible Amazon Pay partner checkout","eligible_online":"Other issuer-listed eligible online merchant"}
        st.selectbox("Merchant / payment context",list(merchants),format_func=merchants.get,key="merchant_type",
                     help="Choose a listed merchant only if the transaction meets its issuer's eligibility. Otherwise choose Not sure.")
        remember("merchant_type")
        st.caption("For a domestic, non-EMI purchase only. Issuer exclusions and merchant MCCs still apply.")
        emi = st.checkbox("This is an EMI transaction",value=False,key="emi")
        remember("amount");remember("cat");remember("channel")

        used_by_card={}
        capped=[]
        for c in selected:
            if st.session_state["cat"] in c.get("excl",{}):
                continue
            bucket=reward_bucket(c,st.session_state["cat"],st.session_state["channel"],st.session_state["merchant_type"])
            if bucket and bucket[2] is not None:
                name,rate,cap,minimum=bucket
                capped.append((c,cap,name))
        if capped:
            with st.expander("Optional: cashback already earned this cycle"):
                st.caption("The app cannot track prior rewards. A zero input assumes the relevant cap is unused.")
                for c,cap,bucket_name in capped:
                    used_by_card[c["id"]]=st.number_input(
                        f"{c['name']}: already earned in {bucket_name} bucket (₹)",
                        min_value=0,max_value=int(cap),step=50,value=0,format="%d",
                        key=f"used_{c['id']}_{bucket_name}")
        current_sig=repr((tuple(c["id"] for c in selected),st.session_state.get("amount"),
                          st.session_state["cat"],st.session_state["channel"],
                          st.session_state.get("merchant_type","unknown"),emi,sorted(used_by_card.items())))
        if st.session_state.get("last") and st.session_state["last"].get("signature")!=current_sig:
            st.session_state.pop("last",None)
            st.info("Inputs changed. Run the comparison again.")
        go=st.button("Compare my selected cards",type="primary",use_container_width=True)
        error=None
        if go:
            amount=st.session_state.get("amount")
            if not selected:
                error="Select at least one card."
            elif not amount or amount<=0:
                error="Enter a purchase amount greater than zero."
            elif amount>10000000:
                error="The supported amount limit is ₹1,00,00,000."
            elif emi:
                error="EMI transactions are outside the supported reward comparison."
            if error:
                st.session_state.pop("last",None)
            else:
                ranked=rank(selected,st.session_state["cat"],amount,used_by_card,
                            channel=st.session_state["channel"],
                            merchant_type=st.session_state.get("merchant_type","unknown"))
                st.session_state["last"]={
                    "ranked":ranked,"win":ranked[0],"second":ranked[1] if len(ranked)>1 else None,
                    "amount":amount,"cat":st.session_state["cat"],
                    "ai_text":None,"ai_status":None,"signature":current_sig,
                }
with right:
    if error:
        st.error(error)
    elif st.session_state.get("last"):
        render_result(st.session_state["last"])
    else:
        st.markdown('<div class="cca-empty"><h3>Your decision starts here</h3><p>Select your cards and enter a purchase to see the estimated reward, key conditions and comparison.</p></div>',unsafe_allow_html=True)
