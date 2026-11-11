"""FAQ: honest answers to the questions a first-time visitor will have."""

import streamlit as st

st.markdown("## Frequently asked questions")

faqs = [
    ("Who is this for?",
     "People who hold more than one credit card and want to be sure they are using the right one "
     "for a particular purchase. It is for individuals checking their own cards. It is not a tool "
     "for banks or merchants."),
    ("Do you need my card number?",
     "No. You only pick the card names you hold. The app never asks for a card number, expiry date or CVV."),
    ("Is the answer a guarantee?",
     "No. The figure is an estimate based on the card terms we have on file and the date they were checked. "
     "Issuers change terms, and some conditions (such as merchant codes) cannot be known in advance."),
    ("Which cards are supported?",
     "Only the cards on the Supported cards page. Cards outside that list are not compared."),
    ("Can a bank or merchant pay to be ranked higher?",
     "No. Only the cards you say you hold are ranked, purely by estimated rupee benefit. "
     "Exact ties go to the card with the lower annual fee."),
    ("What does the AI do?",
     "Only rewords. The rules engine does all the calculating and ranking. If you ask for AI wording, "
     "every number in it is checked against the rules output. If anything differs, you see the "
     "rule-based explanation instead."),
    ("Does it track my monthly spending?",
     "Not in V1. If you already used part of a monthly bonus cap, you can enter that amount yourself. "
     "Automatic tracking is on the roadmap."),
    ("Is my data stored?",
     "No. Nothing you enter is saved. Your choices are kept only while your browser tab stays open."),
    ("I think a card's terms are wrong. What do I do?",
     "Use the contact details on the About page. A one-click “Report wrong info” flow is planned."),
]
for q, a in faqs:
    with st.expander(q):
        st.write(a)
