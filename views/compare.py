"""Stateless purchase comparison: selectors live only in Streamlit session state."""
import streamlit as st
from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, highlight, inr, rank
from ui import is_mobile, keep, remember

cat_ids = [cid for cid, _ in CATEGORIES]
for card in CARDS:
    keep(f"w_{card['id']}", card["id"] in DEFAULT_WALLET)
keep("amount")
keep("cat","dining")
keep("channel","online")
keep("merchant_type","unknown")

st.markdown("## Compare my cards")
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
        if st.session_state["cat"]=="shopping":
            st.selectbox("Shopping merchant",["unknown","marketplace"],
                         format_func=lambda v:"Other / not sure (MCC not confirmed)" if v=="unknown" else "Amazon / Flipkart / Myntra",
                         key="merchant_type",
                         help="HSBC boosted shopping eligibility depends on the issuer's merchant category code.")
            remember("merchant_type")
        st.caption("For a domestic, non-EMI purchase only. Issuer exclusions and merchant MCCs still apply.")
        emi = st.checkbox("This is an EMI transaction",value=False,key="emi")
        remember("amount");remember("cat");remember("channel")

        used_by_card={}
        capped=[]
        for c in selected:
            if c["model"]=="channel_capped" and st.session_state["cat"] not in c.get("excl",{}):
                capped.append((c,c["channel_rules"][st.session_state["channel"]]["cap"],
                               "cashback already earned in this channel during the current statement cycle"))
            elif c["model"]=="shared_category_cap" and st.session_state["cat"] in c["rules"]:
                capped.append((c,1200,"accelerated cashback already earned across ALL boosted categories this billing cycle"))
        if capped:
            with st.expander("Optional: cashback already earned this cycle"):
                st.caption("The app cannot track prior rewards. A zero input assumes the relevant cap is unused.")
                for c,cap,description in capped:
                    used_by_card[c["id"]]=st.number_input(
                        f"{c['name']}: {description} (₹)",
                        min_value=0,max_value=int(cap),step=50,value=0,format="%d",
                        key=f"used_{c['id']}_{st.session_state['channel'] if c['model']=='channel_capped' else 'shared'}")
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
        st.info("Your estimated comparison will appear here. Start by choosing the cards you actually hold.")
