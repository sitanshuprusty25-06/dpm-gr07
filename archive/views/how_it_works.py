"""Explain the actual comparison workflow and its limits."""
import streamlit as st
from cards import CARDS
from rules_engine import evaluate,inr,key_condition
from ui import page_heading
page_heading("How it works")
st.write("Compare the supported cards you already own for one purchase. The tool estimates rewards; you choose how to pay.")
st.markdown("### 1 · Enter your purchase")
st.write("Select your exact card variants, amount, category and payment method. Confirm merchant eligibility when asked. Adjust reward caps if you already earned rewards this cycle.")
st.markdown("### 2 · Compare the issuer rules")
st.write("Python calculates eligible reward estimates using the dated catalogue, minimum spends, exclusions and applicable caps. When the reward cannot be established, the app does not declare a winner.")
st.markdown("### 3 · Understand the decision")
st.write("Gemini can select an approved reason and caution from the computed facts. It does not calculate or change the ranking. Six checks validate its response; if the request fails, a rules-based explanation remains available. AI can be switched off before comparison.")
st.caption("No bank login, card number or payment initiation. With AI enabled, computed purchase facts are shared with Google Gemini.")
st.markdown("### Example: caps matter")
card=next(c for c in CARDS if c["id"]=="sbi_cashback")
example=evaluate(card,"dining",50000,channel="online")
st.write(f"For an eligible ₹50,000 online purchase with an unused cap, {card['name']} estimates {inr(example.benefit)} in cashback.")
st.write(key_condition(example))
st.link_button("Issuer terms for this example",card["source"])
st.markdown("### When there is no clear winner")
st.write("A tie, zero reward, unsupported payment route or unresolved merchant or cap condition is not a reason to invent a recommendation. Compare the available facts, and check the issuer terms.")
st.caption("Only supported domestic non-EMI credit-card purchases are modeled. Reward forms differ; fees, interest and promotional offers are excluded.")
if st.button("Compare my cards",type="primary"):
    st.switch_page("views/compare.py")
