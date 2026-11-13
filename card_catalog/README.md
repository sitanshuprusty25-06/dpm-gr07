# Card rules reference catalogue — current MVP

This is version-controlled public reference data, not a user database. `cards.py` reads the structured catalogue and applies the browsing order. `rules_engine.py` evaluates the supported purchase rules; no customer selections, amounts or bank credentials are saved here.

- `cards.json`: canonical card identities, models, summaries, fee values, source dates, primary and additional issuer references.
- `market_order.json`: all ten IDs in market-informed browsing order; not a purchase recommendation input.
- `source_register.csv`: one row per product, matching the canonical ID, name, issuer, primary source and review date.
- `source_notes/`: current modeled treatment, issuer sources and limitations; one shared note for Scapia Visa/RuPay.
- `link_review.md`: current customer-facing issuer-reference availability and removed/replaced links.
- `fine_print_review.md`: detailed evidence review and unresolved issues from 12 November 2026, with Kiwi updates from 13 November.

## Maintenance

Verify current official product terms, FAQs and applicable service guides. Confirm merchant MCC/MID, rates, minimum spends, cap period and sharing, exclusions and after-cap treatment. Change only established rules; preserve unresolved classifications. Update the relevant code, catalogue entry, source note, register and regression tests together. Run `python -m unittest -v` and compile the active modules before deploying. Validate actual browser behavior and issuer examples independently.

The dated review was based on publicly visible issuer material, not bank confirmation or proof that Group 07 independently validated the terms. Some newer documents were not fully retrievable. Actual MCC, posting and prior cap usage remain uncertain without confirmation. Market figures are discovery evidence only and must not be interpreted as product-level popularity or affect ranking.
