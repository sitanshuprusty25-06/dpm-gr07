# HSBC Live+ Credit Card — current modeled rules

Evidence review: 2026-11-12. This note describes the current MVP model, not a fresh issuer confirmation.

## Issuer references
- https://www.hsbc.bank.in/credit-cards/products/live-plus/
- https://www.hsbc.co.in/content/dam/hsbc/in/documents/credit-cards/live-plus-credit-card-services-guide.pdf

## Modeled treatment and limitations
- Current issuer product material describes 10% on eligible dining, food delivery, grocery, shopping and utility spends sharing a ₹1,200 billing-cycle cap; 1.5% on most other eligible domestic spend.
- Amazon, Flipkart and Myntra are modeled at 1.5%. Unconfirmed shopping MCCs and utilities remain unresolved.
- The older service-guide illustration uses a different ₹1,000 cap; the treatment of amounts beyond the remaining accelerated cap is not established in this catalogue. Such transactions remain unranked rather than assuming base cashback.
- Enter prior accelerated cashback across all boosted categories in the billing cycle, not only one category. Annual fee ₹999 before tax.

Team must independently verify current terms, actual merchant eligibility and settled rewards. See [fine-print review](../fine_print_review.md) and [structured catalogue](../cards.json).
