"""Explain the narrow rules-versus-GenAI separation."""
import streamlit as st
st.markdown("## How the decision is made")
st.markdown(
    "**Know:** dated issuer data is stored in a version-controlled reference catalogue. "
    "**Decide:** Python evaluates eligible rewards deterministically. "
    "**Explain:** Gemini selects a useful reason and caution from approved computed facts; the app validates the selection and renders only approved statements. Gemini never calculates rewards."
)
st.markdown("### A documented example")
st.write(
    "CASHBACK SBI Card: an eligible ₹50,000 online purchase would earn 5% before its cap, "
    "but the online statement-cycle cap is ₹2,000. If the cap was unused, the estimated cashback is ₹2,000, "
    "not ₹2,500. After the online cap is reached, further eligible online transactions earn no cashback in that cycle."
)
st.markdown("### Why the app sometimes refuses to rank")
st.write(
    "HSBC's boosted cashback has a shared cap, and shopping or utility eligibility may depend on the merchant MCC. "
    "When the catalogue cannot support a reliable numerical comparison, the app shows the uncertainty instead of inventing a winner."
)
st.caption("Only domestic, non-EMI transactions from the supported categories are modeled; issuer rules and exclusions apply.")
if st.button("Compare my selected cards",type="primary"):
    st.switch_page("views/compare.py")

st.markdown("### Another example: merchant context matters")
st.write("An eligible ₹10,000 Myntra transaction, with an unused quarterly cap, earns an estimated ₹750 on Flipkart Axis. An eligible ₹10,000 Flipkart purchase earns ₹500. These are separate issuer buckets. We do not combine them into one cap.")
