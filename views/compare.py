"""Stateless purchase comparison: selectors live only in Streamlit session state."""
import streamlit as st
from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, rank, reward_bucket
from ui import is_mobile, keep, remember
from visuals import card_art

cat_ids = [cid for cid, _ in CATEGORIES]
by_id = {card["id"]: card for card in CARDS}
# Preserve existing selections during a session, including after an upgrade
# from the previous checkbox layout. No wallet is written to disk.
legacy = [c["id"] for c in CARDS if st.session_state.get("p_w_" + c["id"], c["id"] in DEFAULT_WALLET)]
keep("compare_wallet_ids", legacy)
# A catalogue change must not leave an invalid multiselect option.
st.session_state["compare_wallet_ids"] = [cid for cid in st.session_state.get("compare_wallet_ids", []) if cid in by_id]
keep("amount")
keep("cat","dining")
keep("channel","online")
keep("merchant_type","unknown")

st.markdown('<div class="fin-eyebrow">Smart card comparison</div><div class="fin-heading">Which card should you use?</div><div class="fin-copy">Choose the cards you own, enter one purchase, and see the estimated reward and conditions.</div>',unsafe_allow_html=True)
st.caption("One domestic, non-EMI purchase. No card numbers or bank login.")

mobile = is_mobile()
left, right = (st.container(), st.container()) if mobile else st.columns([1,1],gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="fin-step">01 / Your cards</div>',unsafe_allow_html=True)
        selected_ids = st.multiselect(
            "Cards you own", options=list(by_id), format_func=lambda cid: by_id[cid]["name"],
            key="compare_wallet_ids", placeholder="Search and select your cards",
            help="Type a bank or card name to find any of the ten supported cards."
        )
        remember("compare_wallet_ids")
        selected = [by_id[cid] for cid in selected_ids]
        st.caption(f"{len(selected)} selected · only your selected cards are compared")
        if selected:
            # Bound previews independently of wallet size; names of every selected
            # card remain visible in the native multiselect above.
            previews = "".join(card_art(card, compact=True) for card in selected[:3])
            st.markdown('<div class="fin-wallet-preview">'+previews+'</div>',unsafe_allow_html=True)
            if len(selected)>3:
                st.caption(f"+ {len(selected)-3} more selected")
        else:
            st.page_link("views/supported_cards.py",label="View supported cards and terms")
    with st.container(border=True):
        st.markdown('<div class="fin-step">02 / Purchase details</div>',unsafe_allow_html=True)
        # Keep the amount field full-width: native numeric controls and input
        # instructions need room even on narrow desktop layouts.
        st.number_input("Amount (₹)",min_value=0,step=100,value=None,format="%d",key="amount",placeholder="e.g. 1200")
        st.caption("Type the amount, then press Enter or move to the next field.")
        st.selectbox("Payment method",["online","offline","upi"],
                     format_func=lambda v:{"online":"Online card / checkout","offline":"Card at store","upi":"Merchant UPI QR"}[v],
                     key="channel")
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
        if channel=="online" and cat=="hotel":
            merchants["scapia_travel"]="Eligible travel booking inside Scapia app"
        if channel=="online" and "kiwi_yes_klick" in [c["id"] for c in selected]:
            merchants["kiwi_online"]="Eligible online merchant payment via Kiwi app"
        if channel=="upi":
            merchants={"kiwi_qr":"Eligible merchant QR via Kiwi app / credit on UPI","other":"Eligible merchant QR via another UPI app"}
        if channel=="offline":
            merchant="other"
        else:
            merchant=st.selectbox("Merchant / payment route",list(merchants),format_func=merchants.get,
                                  key=f"route_{cat}_{channel}",help="Only choose a route if the purchase meets its issuer terms. Otherwise choose Not sure.")
        st.session_state["merchant_type"]=merchant
        st.caption("Merchant eligibility and issuer exclusions apply.")
        emi = st.checkbox("This is EMI, gift card, wallet load, international or otherwise excluded spending",value=False,key="emi")
        remember("amount");remember("cat");remember("channel")

        kiwi_remaining=None
        if any(c["id"]=="kiwi_yes_klick" for c in selected) and merchant in ("kiwi_qr","kiwi_online"):
            with st.expander("Kiwi · remaining monthly reward cap",expanded=False):
                st.caption("Enter the remaining Kiwi reward allowance converted to rupees (4 Kiwis = ₹1). Leave blank if unknown; Kiwi will remain unranked rather than assuming an unlimited reward.")
                kiwi_remaining=st.number_input("Remaining Kiwi reward value (₹)",min_value=0.0,value=None,step=1.0,key="kiwi_remaining")
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
            st.caption("Default estimate: applicable cashback caps are unused. Adjust if you have already earned rewards this cycle.")
            with st.expander("Optional · adjust previous cashback earned",expanded=False):
                st.caption("Zero assumes the relevant cap is unused. SBI uses statement cycles, HDFC/HSBC billing cycles, and Axis accelerated categories separate statement-quarter caps.")
                for c,cap,bucket_name in capped:
                    used_by_card[c["id"]]=st.number_input(
                        f"{c['name']} · {bucket_name} cashback already earned (₹)",
                        min_value=0,max_value=int(cap),step=50,value=0,format="%d",
                        key=f"used_{c['id']}_{bucket_name}")
        if any(c["id"]=="kiwi_yes_klick" for c in selected) and merchant in ("kiwi_qr","kiwi_online") and kiwi_remaining is None:
            st.caption("Kiwi will remain unranked until its remaining monthly reward allowance is entered.")
        use_ai = st.checkbox("Include AI-assisted explanation",value=True,key="compare_use_ai",
                             help="If enabled, the comparison sends computed purchase facts to Google Gemini. No card numbers or banking credentials are requested.")
        st.caption("With AI enabled, Compare shares the selected product names and computed purchase facts with Gemini. Uncheck to compare using local rules only.")
        current_sig=repr((tuple(c["id"] for c in selected),st.session_state.get("amount"),
                          st.session_state["cat"],st.session_state["channel"],
                          st.session_state.get("merchant_type","unknown"),emi,sorted(used_by_card.items()),kiwi_remaining,use_ai))
        if st.session_state.get("last") and st.session_state["last"].get("signature")!=current_sig:
            st.session_state.pop("last",None)
            st.caption("Inputs changed — compare again for an updated result.")
        go=st.button("Compare with AI" if use_ai else "Compare my cards",type="primary",use_container_width=True)
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
                            merchant_type=st.session_state.get("merchant_type","unknown"),kiwi_remaining=kiwi_remaining)
                st.session_state["last"]={
                    "ranked":ranked,"win":ranked[0],"second":ranked[1] if len(ranked)>1 else None,
                    "amount":amount,"cat":st.session_state["cat"],
                    "ai_text":None,"ai_status":None if use_ai else "disabled","ai_detail":{},"ai_enabled":use_ai,"signature":current_sig,"channel":st.session_state["channel"],"merchant_label":merchants.get(merchant,merchant),"cap_assumed":bool(capped) and any(x==0 for x in used_by_card.values()),
                }
with right:
    st.markdown('<div class="fin-step">03 / Your result</div>',unsafe_allow_html=True)
    if error:
        st.error(error)
    elif st.session_state.get("last"):
        render_result(st.session_state["last"], request_ai=go)
    else:
        st.markdown('<div class="cca-empty"><h3>Your comparison appears here</h3><p>Choose your cards, enter the purchase and select Compare. We will show the estimated rewards and any conditions that affect the decision.</p></div>',unsafe_allow_html=True)
