# Flipkart Axis Bank Credit Card — current modeled rules

Evidence review: 2026-11-12. This note describes the current MVP model, not a fresh issuer confirmation.

## Issuer references
- https://cug.axisbank.com/cards/credit-card/flipkart-axisbank-credit-card
- https://www.axisbank.com/docs/default-source/default-document-library/cashback-tncs---final.pdf
- https://campaign.axis.bank.in/generic/terms-and-conditions-generic-all.pdf
- https://www.axis.bank.in/docs/default-source/default-document-library/cashback-tncs---final.pdf
- https://www.axisbank.com/docs/default-source/default-document-library/credit-card-tnc/terms-and-conditions-for-flipkart-credit-card.pdf
- https://www.axis.bank.in/docs/default-source/default-document-library/flipkart-axis-bank-credit-card-preferred-merchants.pdf

## Modeled treatment and limitations
- Eligible Myntra: 7.5%; Flipkart and Cleartrip hotel: 5%; each has a separate ₹4,000 statement-quarter cap.
- Issuer worked examples establish that immediate reward is limited to the remaining cap. Excess is not credited as base cashback; surplus is retained only for specified refund/EMI adjustments (not tracked).
- Confirmed preferred merchants: 4%, uncapped. Eligible Swiggy food delivery qualifies; Instamart and Dineout do not qualify for that preferred rate and are modeled at 1% when otherwise eligible. A generic Swiggy route is unresolved.
- Other eligible spend: 1%. Flipkart Health is not modeled as eligible Flipkart shopping. MID and exclusions apply; annual fee ₹500 before tax; offers and fees excluded from the purchase ranking.

Team must independently verify current terms, actual merchant eligibility and settled rewards. See [fine-print review](../fine_print_review.md) and [structured catalogue](../cards.json).
