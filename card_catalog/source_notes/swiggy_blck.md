# Swiggy BLCK HDFC Bank — current modeled rules

Evidence review: 2026-11-12. This note describes the current MVP model, not a fresh issuer confirmation.

## Issuer references
- https://www.hdfc.bank.in/credit-cards/swiggy-blck-hdfc-bank-credit-card
- https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/personal-banking/discover-products/cards/credit-cards/swiggy-blck-hdfc-bank-credit-card/pdf/t-and-cs-swiggy-black-hdfc-bank-credit-card.pdf

## Modeled treatment and limitations
- Eligible Swiggy: 10%, ₹1,500 billing-cycle cap, ₹249 minimum.
- Eligible online: 5%, separate ₹1,500 cap, ₹100 minimum. Myntra is explicitly listed for BLCK.
- Other eligible: 1%, separate ₹1,000 cap, ₹100 minimum. Annual fee ₹1,000 before tax.
- Generic online merchant eligibility is not inferred. Welcome membership and temporary Cleartrip/Nykaa offers are not modeled. HDFC settlement rounding is an estimate, not independently confirmed.

Team must independently verify current terms, actual merchant eligibility and settled rewards. See [fine-print review](../fine_print_review.md) and [structured catalogue](../cards.json).
