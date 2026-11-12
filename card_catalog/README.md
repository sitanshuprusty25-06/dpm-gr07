# Card rules reference catalogue

This directory is **reference data**, not a database of users. The Streamlit app reads `cards.json` at runtime; Git records changes to issuer rules. No user's selected cards, amount, session information or bank account is saved here.

- `cards.json`: card records, calculation model, categories, source dates and official URLs.
- `source_register.csv`: auditable summary of issuer evidence and status.
- `source_notes/`: issuer-specific qualifications that a simple numerical rule cannot capture.

## Update procedure
1. Open the issuer's current product page, FAQ and service guide, not an aggregator's estimate.
2. Confirm the reward rate, time period, cap-sharing rule, merchant category codes, exclusions and reward *after* the cap.
3. Change the structured entry **only** for rules you can establish, and update its source and verification date.
4. Run `python -m unittest -v`. Add a hand-checked example for every materially new rule.
5. Keep uncertain situations unavailable to rank until supported by verified issuer guidance.
6. Commit the change; Streamlit Cloud then redeploys the application.

The 2026-11-12 source review was prepared using publicly visible issuer documents. It is **not** a claim that the Group 07 students independently verified the entries. They should review the linked issuer documents before using this in their assessed submission. Merchant MCC and statement/billing-cycle usage remain unknown unless entered or independently checked.


Market data is stored separately in `market_order.json` and governs browsing only. The dated public evidence is not an input to any reward rule or recommendation. Issuer totals must not be attributed to a specific card variant. Update the display order and sources together, and rerun the catalogue tests when changing products.
