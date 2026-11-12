"""Stateless purchase comparison: selectors live only in Streamlit session state."""
import streamlit as st
from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, highlight, inr, rank, reward_bucket
from ui import is_mobile, keep, remember, grid
from visuals import card_art

cat_ids = [cid for cid, _ in CATEGORIES]
for card in CARDS:
    keep(f"w_{card['id']}", card["id"] in DEFAULT_WALLET)
keep("amount")
keep("cat","dining")
keep("channel","online")
keep("merchant_type","unknown")

st.markdown('<div class="fin-eyebrow">Smart card comparison</div><div class="fin-heading">Which card should you use?</div><div class="fin-copy">Choose the cards you own, enter one purchase, and see the estimated reward and conditions.</div>',unsafe_allow_html=True)
st.caption("Choose the cards you own and describe one domestic, non-EMI purchase. No card numbers or bank login.")

mobile = is_mobile()
left, right = (st.container(), st.container()) if mobile else st.columns([1,1],gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="fin-step">01 / Your cards</div>',unsafe_allow_html=True)
        cols = None if mobile else st.columns(2)
        for i, c in enumerate(CARDS):
            with (st.container() if mobile else cols[i%2]):
                st.markdown(card_art(c,compact=True),unsafe_allow_html=True)
                st.checkbox(c["name"],key=f"w_{c['id']}")
                st.caption(c.get("headline",highlight(c)))
            remember(f"w_{c['id']}")
        selected = [c for c in CARDS if st.session_state.get(f"w_{c['id']}")]
        st.caption(f"{len(selected)} of {len(CARDS)} cards selected. Only your cards are compared.")
    with st.container(border=True):
        st.markdown('<div class="fin-step">02 / Purchase details</div>',unsafe_allow_html=True)
        st.number_input("Amount (₹)",min_value=0,step=100,value=None,format="%d",key="amount",placeholder="e.g. 8000")
        st.radio("Purchase channel",["online","offline"],format_func=lambda v:"Online" if v=="online" else "Physical store",horizontal=True,key="channel")
        st.selectbox("Purchase category",cat_ids,format_func=category_label,key="cat")
        cat, channel = st.session_state["cat"], st.session_state["channel"]
        merchants={"unknown":"Not sure about eligibility","other":"Other ordinary eligible purchase"}
        if channel=="online" and cat in ("dining","groceries"):
            merchants["swiggy"]="Eligible Swiggy app (food / Instamart / Dineout)"
        if channel=="online" and cat=="shopping":
            merchants.update({"flipkart":"Flipkart eligible shopping","myntra":"Myntra eligible shopping",
                              "amazon_prime":"Amazon India eligible goods · Prime",
                              "amazon_nonprime":"Amazon India eligible goods · non-Prime",
                              "eligible_online":"Other eligible HDFC-listed online merchant"})
        if channel=="online" and cat=="hotel":
            merchants["cleartrip"]="Eligible Cleartrip hotel booking"
        if channel=="online" and cat=="cinema":
            merchants["eligible_online"]="Eligible HDFC-listed online cinema merchant"
        if channel=="online" and "flipkart_axis" in [c["id"] for c in selected] and cat not in ("fuel","utilities"):
            merchants["axis_preferred"]="Confirmed Axis preferred merchant (check issuer list)"
        if channel=="online" and cat in ("dining","groceries","shopping","cinema","utilities") and "amazon_icici" in [c["id"] for c in selected]:
            merchants["amazon_pay"]="Eligible Login and Pay with Amazon partner checkout"
        if channel=="offline":
            merchant="other"
        else:
            merchant=st.selectbox("Merchant / payment route",list(merchants),format_func=merchants.get,
                                  key=f"route_{cat}",help="Only choose a route if the purchase meets its issuer terms. Otherwise choose Not sure.")
        st.session_state["merchant_type"]=merchant
        st.caption("Domestic personal purchases only. Merchant coding and issuer exclusions apply. Do not enter sensitive card details.")
        emi = st.checkbox("This is EMI, gift card, wallet load, international or otherwise excluded spending",value=False,key="emi")
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
            with st.expander("Optional · adjust previous cashback earned"):
                st.caption("Zero assumes the relevant cap is unused. SBI uses statement cycles, HDFC/HSBC billing cycles, and Axis accelerated categories separate statement-quarter caps.")
                for c,cap,bucket_name in capped:
                    used_by_card[c["id"]]=st.number_input(
                        f"{c['name']} · {bucket_name} cashback already earned (₹)",
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
                error="This transaction is outside the supported purchase scope."
            if error:
                st.session_state.pop("last",None)
            else:
                ranked=rank(selected,st.session_state["cat"],amount,used_by_card,
                            channel=st.session_state["channel"],
                            merchant_type=st.session_state.get("merchant_type","unknown"))
                st.session_state["last"]={
                    "ranked":ranked,"win":ranked[0],"second":ranked[1] if len(ranked)>1 else None,
                    "amount":amount,"cat":st.session_state["cat"],
                    "ai_text":None,"ai_status":None,"signature":current_sig,"channel":st.session_state["channel"],"merchant_label":merchants.get(merchant,merchant),"cap_assumed":bool(capped) and all(x==0 for x in used_by_card.values()),
                }
with right:
    st.markdown('<div class="fin-step">03 / Your result</div>',unsafe_allow_html=True)
    if error:
        st.error(error)
    elif st.session_state.get("last"):
        render_result(st.session_state["last"])
    else:
        st.markdown('<div class="cca-empty"><h3>Your comparison appears here</h3><p>Choose your cards, enter the purchase and select Compare. We will show the estimated rewards and any conditions that affect the decision.</p></div>',unsafe_allow_html=True)
