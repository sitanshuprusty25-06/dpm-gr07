"""Scope, privacy and reward FAQ."""
import streamlit as st
st.markdown("## Frequently asked questions")
questions=[
("Which Swiggy card do I select?","The original, ORNGE and BLCK cards have different terms. Select the exact product shown in your wallet. BLCK has separate Swiggy, online and other billing-cycle buckets."),
("What is a statement-quarter cap?","Flipkart Axis has separate accelerated cashback caps for Myntra, Flipkart and Cleartrip per statement quarter. Enter previously earned cashback for the specific merchant bucket."),
("Do the bank logos mean the banks endorse this app?","No. Product images and website icons are for identification. This is an independent academic project."),
("Do you need my card number?","No. Select issuer card names only. We never request CVV, expiry, OTP, PIN or bank credentials."),
("Does the application save my wallet?","No accounts or persistent wallet are created. Selections and inputs remain in temporary Streamlit session state while you use the app."),
("Does Gemini receive my data?","Only if you click the Gemini rewording button. It receives selected card names and computed purchase facts needed to form an explanation. Check the provider's data-handling terms."),
("Are rewards guaranteed?","No. Card terms and merchant MCC classifications can change. Rewards shown are conditional estimates using dated official issuer source material."),
("Why do you sometimes decline to recommend a card?","When eligibility or post-cap reward treatment is unresolved, showing a definitive winner would be misleading."),
("What does 'already earned cashback' mean?","For SBI, it is the cashback already earned in the selected online/offline channel during the current statement cycle. For HSBC enter combined accelerated cashback; HDFC ORNGE uses a shared boosted bucket, while original Swiggy HDFC has separate Swiggy, online and base buckets. Amazon Pay ICICI has no modeled reward cap."),
("Does the app track spending?","No. Previous eligible rewards have to be entered manually; leaving the field at zero assumes the relevant cycle cap has not been used."),
("What is GenAI used for?","Gemini only rephrases computed results. The rules engine makes the financial calculation and ranking; a failed AI call falls back to the deterministic explanation."),
("What is excluded from this comparison?","EMI, international transactions, unsupported categories, some merchant MCCs, transaction fees and issuer promotions not encoded in the catalogue."),
]
for q,a in questions:
    with st.expander(q):st.write(a)
