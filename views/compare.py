"""Stateless purchase comparison: selectors live only in Streamlit session state."""
import streamlit as st
from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, rank, reward_bucket, money, inr
from ui import is_mobile, keep, keep_money, remember, page_heading

cat_ids = [cid for cid, _ in CATEGORIES]
by_id = {card["id"]: card for card in CARDS}
# Preserve existing selections during a session, including after an upgrade
# from the previous checkbox layout. No wallet is written to disk.
legacy = [c["id"] for c in CARDS if st.session_state.get("p_w_" + c["id"], c["id"] in DEFAULT_WALLET)]
keep("compare_wallet_ids", legacy)
# A catalogue change must not leave an invalid multiselect option.
st.session_state["compare_wallet_ids"] = [cid for cid in st.session_state.get("compare_wallet_ids", []) if cid in by_id]
keep_money("amount")
keep("cat","dining")
keep("channel","online")
keep("merchant_type","unknown")

with st.container(key="compare_workspace"):
    page_heading("Which card should you use?")
    st.caption("Compare cards you own before paying. Domestic, non-EMI purchases only.")

    mobile = is_mobile()
    left, right = (st.container(), st.container()) if mobile else st.columns([1.12,1],gap="medium")
    with left:
        with st.container(border=True,key="purchase_inputs"):
            st.markdown('<div class="fin-step"><span class="step-number">01</span>Your cards</div>',unsafe_allow_html=True)
            selected_ids = st.multiselect(
                "Cards you own", options=list(by_id), format_func=lambda cid: by_id[cid]["name"],
                key="compare_wallet_ids", placeholder="Search and select your cards",
                help="Search by bank or card name. Select only cards you already own."
            )
            remember("compare_wallet_ids")
            selected = [card for card in CARDS if card["id"] in selected_ids]
            # Names remain visible in the native multiselect. Artwork lives in
            # the catalogue; do not fetch image assets while comparing a purchase.
            st.markdown('<div class="fin-step"><span class="step-number">02</span>Purchase details</div>',unsafe_allow_html=True)
            # Keep the amount field full-width so the editing controls have room.
            raw_amount=st.number_input("Amount (₹)",min_value=0.0,step=1.0,value=None,format="%.2f",key="amount",placeholder="e.g. 1200.50",help="Enter rupees and paise (up to two decimal places). Press Enter or move to the next field to apply.")
            amount=money(raw_amount) if raw_amount is not None else None
            # Short labels fit side by side on desktop; native columns stack
            # on narrower screens. Amount retains the full input width.
            methods,categories=(st.container(),st.container()) if mobile else st.columns(2)
            with methods:
                st.selectbox("Payment method",["online","offline","upi"],
                             format_func=lambda v:{"online":"Online","offline":"In-store","upi":"Merchant UPI QR"}[v],
                             key="channel")
            with categories:
                st.selectbox("Purchase category",cat_ids,
                             format_func=lambda cid:{"dining":"Dining / food delivery","shopping":"Shopping","cinema":"Cinema","utilities":"Utility bills"}.get(cid,category_label(cid)),
                             key="cat")
            cat, channel = st.session_state["cat"], st.session_state["channel"]
            merchants={"unconfirmed":"Not sure — check eligibility","other":"Other merchant — ordinary eligible purchase"}
            if channel=="online" and cat in ("dining","groceries"):
                if cat=="dining":
                    merchants["swiggy_food"]="Swiggy food delivery — eligible direct order"
                    merchants["swiggy_other"]="Swiggy Dineout — eligible payment"
                else:
                    merchants["swiggy_other"]="Swiggy Instamart — eligible order"
                    merchants["amazon_flipkart_grocery"]="Amazon / Flipkart groceries — grocery MCC confirmed"
            if channel=="online" and cat=="shopping":
                merchants.update({"flipkart":"Flipkart — eligible shopping","myntra":"Myntra — eligible shopping",
                                  "amazon_prime":"Amazon India — eligible goods (Prime)",
                                  "amazon_nonprime":"Amazon India — eligible goods (non-Prime)",
                                  "eligible_online":"Other HDFC partner — eligibility confirmed"})
            if channel=="online" and cat=="hotel":
                merchants["cleartrip"]="Cleartrip — eligible hotel booking"
                if "amazon_icici" in [c["id"] for c in selected]:
                    merchants["amazon_travel_prime"]="Amazon Pay hotel — eligible (Prime)"
                    merchants["amazon_travel_nonprime"]="Amazon Pay hotel — eligible (non-Prime)"
                if any(c["model"].startswith("hdfc") for c in selected):
                    merchants["eligible_online"]="HDFC partner hotel — eligibility confirmed"
            if channel=="online" and cat=="cinema":
                merchants["eligible_online"]="HDFC partner cinema — eligibility confirmed"
            if channel=="online" and "flipkart_axis" in [c["id"] for c in selected] and cat not in ("fuel","utilities"):
                merchants["axis_preferred"]="Axis partner merchant — eligibility confirmed"
            if channel=="online" and cat in ("dining","groceries","shopping","cinema","utilities") and "amazon_icici" in [c["id"] for c in selected]:
                merchants["amazon_pay"]="Amazon Pay partner checkout — eligible Login and Pay"
                if cat in ("shopping","utilities"):
                    merchants["amazon_digital"]="Amazon digital / bill payment — eligible (no gift card or wallet load)"
            if channel=="online" and cat=="hotel":
                merchants["scapia_travel"]="Scapia app — eligible travel booking"
            if channel=="online" and "kiwi_yes_klick" in [c["id"] for c in selected]:
                merchants["kiwi_online"]="Kiwi app — eligible online merchant payment"
            if channel=="upi":
                merchants={"unconfirmed":"Not sure — check eligibility","kiwi_qr":"Kiwi app — eligible merchant QR (credit on UPI)","other":"Other UPI app — eligible merchant QR"}
            if channel=="offline":
                merchant="other"
            else:
                route_key=f"route_{cat}_{channel}"
                keep(route_key)
                if route_key in st.session_state and st.session_state[route_key] not in merchants:
                    st.session_state.pop(route_key,None)
                merchant=st.selectbox("Where are you paying?",list(merchants),format_func=merchants.get,
                                      key=route_key,help="Choose the actual store or app only if its issuer eligibility is confirmed. For partner offers, check the relevant card terms in Supported cards. Grocery MCC means merchant category code 5411. If unsure, choose Not sure; no winner will be forced.")
                remember(route_key)
            st.session_state["merchant_type"]=merchant
            keep("emi",False)
            emi = st.checkbox("EMI, international or other excluded purchase",key="emi",help="Select for EMI, international spending, gift cards, wallet loads, rent, education, jewellery, insurance, tax/government, gaming, tolls, cash advances, railway, business expenses or other excluded spending. This MVP does not model these purchases.")
            remember("amount");remember("cat");remember("channel");remember("emi")

            kiwi_remaining=None
            if any(c["id"]=="kiwi_yes_klick" for c in selected) and merchant in ("kiwi_qr","kiwi_online"):
                with st.expander("Kiwi · remaining monthly allowance (needed for ranking)",expanded=False):
                    st.caption("Enter the remaining Kiwi reward allowance converted to rupees (4 Kiwis = ₹1). Leave blank if unknown; Kiwi will remain unranked rather than assuming an unlimited reward.")
                    keep_money("kiwi_remaining")
                    raw_kiwi=st.number_input("Remaining Kiwi reward value (₹)",min_value=0.0,value=None,step=1.0,format="%.2f",key="kiwi_remaining")
                    kiwi_remaining=money(raw_kiwi) if raw_kiwi is not None else None
                    remember("kiwi_remaining")
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
                with st.expander("Adjust cashback already earned",expanded=False):
                    st.caption("Enter cashback earned, not purchase spend. Zero assumes the full relevant cap is available.")
                    for card,cap,bucket_name in capped:
                        usage_key=f"used_{card['id']}_{bucket_name}"
                        keep_money(usage_key,0.0)
                        bucket_label={"online":"online","offline":"in-store","swiggy":"Swiggy","boost":"shared boosted","base":"other eligible","shared":"shared boosted","flipkart":"Flipkart","myntra":"Myntra","cleartrip":"Cleartrip"}.get(bucket_name,bucket_name)
                        cycle=("statement quarter" if card["model"]=="flipkart_axis" else
                               "statement cycle" if card["model"]=="channel_capped" else "billing cycle")
                        raw_used=st.number_input(
                            f"{card['name']} · {bucket_label} cashback earned (₹)",
                            min_value=0.0,max_value=float(cap),step=1.0,format="%.2f",
                            key=usage_key,help=f"Applicable limit: {inr(cap)} per {cycle}. Enter cashback already earned in this bucket, not spending.")
                        used_by_card[card["id"]]=money(raw_used)
                        remember(usage_key)
                unused_count=sum(value==0 for value in used_by_card.values())
                if unused_count:
                    st.caption(f"Cap assumption: full allowance for {unused_count} of {len(capped)} capped cards. Adjust above if already used.")
                else:
                    st.caption("Cap estimates use the cashback already earned that you entered.")
            if any(c["id"]=="kiwi_yes_klick" for c in selected) and merchant in ("kiwi_qr","kiwi_online") and kiwi_remaining is None:
                st.caption("Kiwi allowance unknown: enter it above to establish a complete comparison.")
            keep("compare_use_ai",False)
            use_ai = st.checkbox("Add AI explanation (shares computed purchase facts with Gemini)",key="compare_use_ai",
                                 help="Optional. On eligible comparisons, Gemini receives computed purchase facts and relevant card names. It selects an approved explanation; it does not calculate or rank rewards. No banking credentials are requested.")
            remember("compare_use_ai")
            current_sig=repr((tuple(c["id"] for c in selected),amount,
                              st.session_state["cat"],st.session_state["channel"],
                              st.session_state.get("merchant_type","unknown"),emi,sorted(used_by_card.items()),kiwi_remaining,use_ai))
            if st.session_state.get("last") and st.session_state["last"].get("signature")!=current_sig:
                st.session_state.pop("last",None)
                st.caption("Inputs changed — compare again for an updated result.")
            go=st.button("Compare my cards",type="primary",use_container_width=True)
            error=None
            if go:
                if not selected:
                    error="Select at least one card."
                elif not amount or amount<=0:
                    error="Enter a purchase amount greater than zero."
                elif amount>10000000:
                    error="The supported amount limit is ₹1,00,00,000."
                elif emi:
                    error="This purchase is outside the MVP scope. Compare only supported domestic, non-EMI purchases."
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
        st.markdown('<div class="fin-step result-step"><span class="step-number">03</span>Your result</div>',unsafe_allow_html=True)
        if error:
            st.error(error)
        elif st.session_state.get("last"):
            render_result(st.session_state["last"], request_ai=go)
        else:
            st.markdown('<div class="cca-empty"><h3>Ready when you are</h3><p>Choose your cards, enter your purchase and select Compare my cards. Your estimated rewards and conditions will appear here.</p></div>',unsafe_allow_html=True)
