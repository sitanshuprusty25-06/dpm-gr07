# CASHBACK SBI Card — current modeled rules

Evidence review: 2026-11-12. This note describes the current MVP model, not a fresh issuer confirmation.

## Issuer references
- https://www.sbicard.com/en/faq/cashback-sbi-card-faq.page
- https://www.sbicard.com/en/personal/credit-cards/cashback-sbi-card.html
- https://www.sbicard.com/sbi-card-en/assets/docs/pdf/cashback-revised.pdf

## Modeled treatment and limitations
- Effective 1 April 2026, 5% eligible online and 1% eligible in-store POS cashback, with separate ₹2,000 caps per statement cycle (₹4,000 aggregate).
- A transaction earns at most its remaining applicable channel cap; later transactions after exhaustion earn zero for that channel. Previously earned cashback input is for the selected channel, not prior spend.
- Fuel and utility categories are excluded by the model. The issuer also excludes insurance, rent, wallets, education, jewellery, railways, gaming, tolls, government transactions and merchant/Flexipay EMI; the scope control excludes such purchases.
- Actual MCC and statement posting determine eligibility. Explicitly unconfirmed routes are not ranked. Annual fee ₹999 before tax.

Team must independently verify current terms, actual merchant eligibility and settled rewards. See [fine-print review](../fine_print_review.md) and [structured catalogue](../cards.json).
