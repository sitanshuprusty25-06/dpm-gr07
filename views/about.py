"""Academic team and project information; no placeholder contact details."""
import streamlit as st
st.markdown("## About the project")
st.write(
    "GenAI Card Choice Assistant is a Group 07 Digital Product Management EMBA project at "
    "IIM Visakhapatnam. It is a small, non-commercial demonstration of a purchase-level "
    "card decision using issuer reference rules and optional Gemini explanation."
)
st.write(
    "Five initial interviews showed that some cardholders compare offers selectively, "
    "while others prefer a default card. This V1 is designed for the first group, not for every cardholder."
)
st.link_button("Source repository","https://github.com/sitanshuprusty25-06/dpm-gr07")
st.write("There is no sponsored ranking, bank affiliation or card application. This is an academic decision-support demonstration, not financial advice.")
if st.button("Try the comparison",type="primary"):
    st.switch_page("views/compare.py")
st.markdown("### Group 07")
for name in ["Gunjan Kumar Singh","Meghana Muthavarapu","Samanth Kumar Gangala Reddy",
             "Sitanshu Prusty","Kumar Bala Naveen Singh Kshtri"]:
    st.write("• "+name)
st.caption("IIM Visakhapatnam · EMBA 2025–27 · Digital Product Management")
