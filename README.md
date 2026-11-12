# GenAI Card Choice Assistant — Group 07

IIM Visakhapatnam, EMBA 2025–27, Digital Product Management.

**Working application:** https://dpm-gr07-vhiacq5l6mcewqexuxwvl2.streamlit.app/

**Repository:** https://github.com/sitanshuprusty25-06/dpm-gr07

## Scope and use
One user (a multi-card selective comparer), one problem (choosing a card for one purchase), one workflow (select cards → enter purchase amount, category and supported payment context (online, physical card, or merchant UPI QR) → apply issuer rules → read conditional comparison and optional Gemini-assisted grounded explanation together).

- The application is **stateless with respect to permanent user storage**. Streamlit temporarily holds user inputs in session state. No login, database or transaction linking.
- `card_catalog/` is **persistent reference data**, with issuer terms, source links, review dates and caveats. It is not user data.
- Ten supported products: CASHBACK SBI, HSBC Live+, original Swiggy HDFC, Swiggy ORNGE, Swiggy BLCK, Amazon Pay ICICI, Flipkart Axis Bank, Kiwi YES BANK Klick, Scapia Federal Visa and Scapia Federal RuPay. Read their `card_catalog/source_notes/` before changing the rules.
- Merchant MCCs are generally unknown at checkout; results are estimates. HSBC boosted categories are sometimes intentionally marked **not comparable** when eligibility or after-cap cashback is unresolved. This protects users against false precision.
- Only domestic, non-EMI transactions in the supported categories are considered. Transaction fees, interest, international charges and most promotional offers are out of scope.

## Main files
- `card_catalog/cards.json` — structured card data; `source_register.csv` and `source_notes/` record evidence
- `cards.py` — load read-only issuer reference data
- `rules_engine.py` — deterministic cashback, exclusions, caps and rankings
- `views/compare.py` — session-only inputs, optional prior-cap usage, comparison form
- `results.py` — conditional recommendation / uncertainty output
- `explain.py` — Gemini selects approved explanation facts; checks response schema, card, amount, reward form, reason and caution; safe fallback
- `test_rules.py` — hand-checked issuer examples and validation tests
- `app.py` — Streamlit top navigation and other pages

## Install, test, launch locally
```bash
python -m pip install -r requirements.txt
python -m unittest -v
streamlit run app.py
```

## Streamlit deployment and secrets
Deploy from the `main` branch using `app.py`. Streamlit Cloud will redeploy after commits.

To enable optional Gemini output, put `GEMINI_API_KEY` into the app's **Streamlit Cloud Secrets** (not into GitHub). The fallback works without Gemini. `.gitignore` excludes `.streamlit/secrets.toml` and `.env`.

## Update card terms safely
Check current issuer FAQs and full card T&Cs. Document the MCC, cap period, prior cashback usage, reward after cap and exclusions. Update `card_catalog/cards.json` and its source note, write a regression test, run tests, then commit.

The official issuer documents were reviewed on 2026-11-12 for this draft. **Group 07 must independently check accuracy and any changes before submitting.** Never present sample estimates as guaranteed financial returns.

## Course AI-use disclosure
The course permits assistance with Phase-2 coding under its rules. The team must document the AI tools used and personally verify and explain the code. **Do not submit AI-generated report/PRD text, images or tables unless the instructor expressly permits them.**

## UX update
Reference product pictures, issuer-site icons, mobile-aware card selection, conditional merchant fields, a clear result hierarchy, comparison bars, cap assumptions and source links. The full image register is `assets/card_images.json`; fallback art is explicitly labeled. All marks belong to their owners. See `assets/README.md`. No bank affiliation. No new account/database or user history.

BLCK and original Swiggy are separate; 10% tier requires ₹249 minimum. Flipkart Axis uses distinct statement-quarter caps for eligible Flipkart, Myntra and Cleartrip; if the remaining accelerated cap is insufficient the engine withholds a definitive winner. Confirm issuer rules independently before use.

Live app: https://dpm-gr07-vhiacq5l6mcewqexuxwvl2.streamlit.app/

## Catalogue and consistent UI update
Ten cards: existing seven plus Kiwi YES BANK Klick (standard non-Neon) and Federal Scapia Visa / RuPay. The library uses consistent artwork, issuer, reward and fee sections. UPI QR is separate from physical card payments; incompatible cards are labeled unavailable. Kiwi requires a known remaining monthly reward cap to rank; no credit limit is collected. Scapia coins are converted at 5 coins per rupee of redemption value, not cash. Exactly ₹500 on Scapia RuPay is unresolved due to issuer wording differences. The Amazon Pay reference picture now uses the actual card-specific product image URL, with a labelled fallback if unreachable. No persistent user data. All rules require team verification.

## Compare page usability iteration
The ten-product catalogue revealed that displaying all card tiles before purchase inputs creates avoidable vertical scrolling. The comparison page now uses a native searchable multi-select, compact purchase inputs without selected-card previews, and collapsed cap adjustments. The full card library is unchanged. The recommendation follows the primary action on mobile and remains alongside the inputs on desktop. Material cap assumptions and unresolved Kiwi eligibility remain visible. This is an implementation refinement, not a new use case or evidence of completed user testing. Selection is held in temporary session state only. Re-test task completion, time to decision, confusion and understanding of the result with real users.

## Verify the AI capability
- In Compare, select Swiggy BLCK HDFC and CASHBACK SBI; ₹1,200, online, dining, eligible Swiggy, unused caps. Expected estimates ₹120 and ₹60.
- Leave **Include AI-assisted explanation** enabled and click **Compare with AI**, then open **AI verification · request status and checks**. A successful live request shows provider response received, six PASS checks and elapsed time. The ranking and reward figures stay unchanged. A missing key, provider failure or rejected response is labelled and preserves the rules-based explanation.
- Run `python -m unittest -v` and `python -m compileall -q app.py cards.py rules_engine.py explain.py results.py views ui.py visuals.py`. Mocked API tests cover successful and rejected responses, invalid JSON, missing key and provider error without contacting Gemini. A live request is a separate test.

Gemini chooses a relevant reason and caution from approved statements; arbitrary model prose is never displayed. These checks establish consistency with our computed facts, not independent verification of issuer terms, model perfection, or evidence of customer value. The diagnostics are temporary session state. No API key or raw provider error is displayed. The team should independently verify the rules, live API and user value before assessed submission.

## AI-first results (one explicit action)
The Compare page defaults to an AI-assisted explanation with a visible disclosure before submission. Uncheck **Include AI-assisted explanation** for local rules only. Clicking **Compare with AI** calculates and ranks first, then calls Gemini at most once for a reliable, unique, positive result. Ties, unresolved comparisons and zero rewards never trigger an AI request. The result displays the winning card and estimated reward, followed immediately by the checked AI explanation (or local fallback) and mandatory issuer conditions. Diagnostics remain available below the comparison. Widget reruns never send another request; inputs changed invalidate the previous result. The default model is `gemini-3.5-flash-lite`, which the team previously confirmed working; Streamlit Secrets can override it. No new API key, repository, database or deployment required.

### Reliability configuration
The Compare action renders the calculated recommendation and mandatory condition before calling Gemini. The SDK client and generation settings are restored to the original request configuration used in the successful Flash-Lite live test. The SDK selects its default endpoint; no custom timeout, retry policy or model-specific 3.x thinking configuration is imposed. The verification panel retains SDK version and sanitized errors. The result remains available on provider failure. Re-test with gemini-3.5-flash-lite before submission.

### Compact comparison flow
The Compare page focuses on the decision: one input panel, full-width amount, payment method and category paired on wide screens, conditional merchant/rail and cap inputs, and a single Compare action. Card artwork is retained on Home and Supported cards, not fetched during the critical comparison path. The result prioritizes estimated reward, checked AI explanation and material conditions; the first three comparison rows are visible and the full selected set is expandable. Monetary formatting preserves paise where applicable. All underlying issuer rules, the previously successful Gemini client configuration and the six grounding checks remain unchanged. Vertical scrolling remains possible on mobile, small displays and large wallets; validate actual layout and task completion with users rather than claiming a no-scroll guarantee.

### All-page review
Home introduces the purchase decision and a clearly labelled worked example; the full catalogue is on Supported cards. How it works follows the actual input → rules → explanation flow. Equal highest rewards are shown without picking a single winner. Zero, unsupported and unresolved outcomes retain access to issuer sources and a clear AI-skip reason. Selected cap inputs and the AI preference are retained in temporary session state, not stored permanently. The footer avoids duplicating the navigation. The working Gemini client is unchanged. The team should verify these changes with the live app, desktop/mobile and real users; no test or customer outcome is claimed by this commit.

### Market-informed catalogue order
`card_catalog/market_order.json` records the display order, methodology, date and public evidence. Amazon Pay ICICI (over 5 million customers, October 2025) and Flipkart Axis (4.2 million cards in force, Q2 FY27) appear first. Remaining products follow RBI September 2026 issuer-level outstanding-card totals, not a claimed product-by-product ranking. Variants within an issuer use a fixed browse order; older product and partner-wide counts are recorded only as context. The Home featured cards, catalogue, issuer filter and Compare selector all draw from the same ordered CARDS list. The results are still ranked by computed eligible purchase rewards, and ties remain neutral. No card, reward rule or Gemini setting has been changed.

### MVP UI and accessibility refinement
Market-informed order remains a catalogue implementation choice, not a customer-facing claim or ranking feature. Adoption badges, market tables and ordering explanations are removed from the interface; evidence stays in `card_catalog/market_order.json`. The purchase ranking is unchanged. Native Streamlit Light/Dark/System themes are configured in `.streamlit/config.toml`; use the top-right menu → Settings → Appearance/Theme. Custom HTML inherits theme text colours, uses neutral borders, a consistent navy result panel with light text, and a neutral mat for product photos. A common header, page heading and footer are shared across the seven pages. The separate theme and layout switches and conflicting native-widget colour overrides are removed. This is a UX refinement, not a new product feature. Browser verification in both native themes and on mobile remains required.

### Compact result explanation
The result shows the reward once, then a single Why this card? panel containing the selected checked reason and key issuer condition. The rules-only fallback follows the same layout. Duplicate issuer-condition text is removed; distinct selected cautions cannot hide mandatory conditions. The SBI cap-hit reason explains pre-cap arithmetic. The Gemini client, schema and six grounding checks are unchanged. Live rendering and automated tests still require verification.
