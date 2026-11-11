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
st.link_button("Open working app","https://dpm-gr07-vhiacq5l6mcewqexuxwvl2.streamlit.app/")
st.markdown("### Group 07")
for name in ["Gunjan Kumar Singh","Meghana Muthavarapu","Samanth Kumar Gangala Reddy",
             "Sitanshu Prusty","Kumar Bala Naveen Singh Kshtri"]:
    st.write("• "+name)
st.caption("No contact address or contribution role is invented here; add confirmed details separately if needed.")
