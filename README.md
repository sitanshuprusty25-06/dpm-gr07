# GenAI Card Choice Assistant — Group 07

IIM Visakhapatnam · EMBA 2025–27 · Digital Product Management

**Live MVP:** https://card-choice-assistant.streamlit.app/

**Source:** https://github.com/sitanshuprusty25-06/dpm-gr07

## Product scope

One user: the multi-card holder who selectively compares payment benefits.
One problem: effort and uncertainty in choosing a card before a purchase.
One use case: compare supported cards already owned for one domestic, non-EMI purchase.
One workflow: choose cards → enter amount (rupees and paise), category and payment context → compare → understand the result.
One GenAI capability: select an approved reason, caution and practical decision tip for a calculated result.

The landing page is **Compare my cards**. The only other primary page is **Supported cards**, a reference catalogue with exact product variants, reward descriptions, fees, conditions and issuer links. A compact, theme-inheriting shared collapsible sidebar shows the value proposition, three-step workflow, privacy and key limitations. Detailed help is collapsed inside the sidebar. Native Streamlit auto mode shows it on larger screens and hides it initially on small devices; users can toggle it. The main footer retains only a short disclaimer. The five retired supporting pages are preserved under [`archive/`](archive/README.md) for development history only; they are not part of active navigation. Future features belong in the team's PRD and roadmap, not the running MVP.

## Calculation and AI

- The deterministic Python engine calculates modeled eligibility, reward rates, minimum spends, caps and rankings from dated issuer reference material.
- A unique positive result in a complete comparison can trigger an optional Gemini request on the explicit Compare action. Gemini selects a reason, caution and practical decision tip from approved options; seven checks validate response format, recommended card, amount, reward type, reason, caution and decision tip.
- Rules-based output remains available without AI or if the provider fails. A tie, unresolved applicable reward, unsupported route or zero reward does not trigger AI.
- The app renders the calculated result before requesting AI. A changed input invalidates the previous result; ordinary reruns do not trigger another request.
- Rewards are conditional estimates, not guaranteed cashback. Actual merchant MCC/MID, issuer posting, exclusions, caps, refunds and settlement may affect rewards. Restricted redemption values are not cash. Fees, interest and unmodeled promotions are excluded.
- Zero prior cashback assumes an unused applicable cap. The input area shows a visible assumption summary for applicable capped cards; the optional adjustment uses plain-language reward buckets and cycle-specific help. Kiwi requires a known remaining reward allowance. Where terms cannot establish an applicable reward, the app suggests the best positive comparable card, clearly marked provisional; unresolved rewards are not treated as zero.

The ten supported products are Amazon Pay ICICI, Flipkart Axis, original Swiggy HDFC, Swiggy BLCK, Swiggy ORNGE, CASHBACK SBI, YES BANK Klick RuPay Credit Card (Kiwi) (standard plan, no Neon/Boost), Scapia Federal Visa, Scapia Federal RuPay and HSBC Live+. Catalogue browsing order is market-informed but never affects the purchase ranking. See `card_catalog/market_order.json`, `card_catalog/fine_print_review.md` and `card_catalog/link_review.md` for evidence and limitations. The fine-print review is dated 12 November 2026, with a Kiwi update on 13 November; supporting notes and the register reflect the current implementation, including Axis remaining-cap handling, Amazon travel and digital routes, HDFC variant-specific eligibility and Kiwi's required remaining allowance. The team must independently verify issuer accuracy.

## Privacy and limits

No login, bank credentials, card numbers, database, payment initiation or persistent user wallet. Temporary Streamlit session state holds selections and purchase context, including route choices when switching pages. The version-controlled catalogue contains public issuer reference data, not user data. AI is off by default for new sessions. Opting in sends relevant card names, purchase details (amount, category and payment method), estimated rewards and applicable reward conditions to Google Gemini on eligible comparisons. The Compare my cards action remains the same with or without AI; an existing session retains its choice. Hosting and AI providers have their own policies; no claim is made about their retention. This is an independent academic prototype, not financial advice or a bank-endorsed service.

## Main files

- `app.py` — two-page navigation
- `views/compare.py` — purchase inputs and comparison
- `views/supported_cards.py` — reference catalogue
- `ui.py`, `.streamlit/config.toml` — shared sidebar guidance, native light/dark theme and layout
- `cards.py`, `card_catalog/` — read-only data, issuer sources, caveats and supported payment choices
- `rules_engine.py` — modeled calculations and ranking
- `explain.py`, `results.py` — approved AI explanation, validation, fallback and result presentation
- `assets/card_images.json`, `assets/README.md`, `assets/kiwi-yes-klick-green.webp` — product artwork provenance, local Kiwi artwork and current layout
- `card_catalog/source_register.csv`, `card_catalog/source_notes/` — synchronized issuer evidence and modeled limitations
- `archive/` — retired prototype pages, not deployed as active views
- `test_rules.py` — issuer and AI regression tests

## Run and test

```bash
python -m pip install -r requirements.txt
python -m unittest -v
python -m compileall -q app.py cards.py rules_engine.py explain.py results.py views ui.py visuals.py
streamlit run app.py
```

Deploy `app.py` from `main` on Streamlit Community Cloud. Use Streamlit Secrets for `GEMINI_API_KEY` and optional `GEMINI_MODEL`; never commit credentials. The default `gemini-3.5-flash-lite` was previously verified in the live app with SDK 3.2.0. This refinement preserves the provider client, dependency requirements, issuer rates and eligibility rules. INR inputs accept two decimal places; modeled amounts are normalized to paise with decimal arithmetic and half-up rounding. Existing HDFC whole-rupee and Scapia coin rounding stages are retained. Issuer settlement rounding may differ. The hosted app's installed SDK and deployed commit must be checked separately.

Smoke test: open the root URL, select Swiggy BLCK HDFC and CASHBACK SBI, enter ₹1,200, online, dining, eligible Swiggy food delivery and unused caps. Expected modeled estimates are ₹120 and ₹60. Change BLCK Swiggy cashback already earned to ₹1,440 for a ₹60/₹60 tie, then ₹1,470 for ₹30/₹60 with SBI leading. SBI online cap must remain unused. These are expected model outcomes, not executed live tests. For an AI-assisted run, first opt in to the AI explanation, compare, and check the seven PASS results and the purchase-specific decision tip under AI verification. Repeat with AI disabled, navigate to Supported cards and back, and check that the inputs persist. Test a fractional purchase amount (e.g. ₹1,200.50), a partially used cap (e.g. ₹1,999.75), a tie, an unconfirmed route, a zero reward, and both light/dark modes on desktop and phone. Verify that the sidebar appears on larger screens, can be collapsed, is initially hidden on small devices, and does not obstruct the comparison. Check the visible cap assumption, Not sure merchant recovery, supported-purchase notice in the heading and exclusion list next to Compare, restricted reward-form notice, planned-purchase caution and reporting link. These are proposed checks, not claims of completed testing.

## Course evidence and maintenance

The simplified information architecture reflects the course emphasis on the smallest useful workflow, feature criticality and usability. It is an iteration based on interface review, not evidence of completed user validation. Document the two to three real-user tests required by the project, actual observations and changes made, and compare understanding with versus without AI. Keep proposed monetization, future integrations and additional features in the PRD.

Check issuer documents and add regression tests before changing the financial rules. The team must understand and verify the code, document AI-assisted coding and follow the instructor's AI-use policy for all submitted artifacts. Do not submit AI-generated report/PRD text, images or tables unless the instructor expressly permits them.

## Repository synchronization

The official deployment is the root URL above; the reference catalogue is https://card-choice-assistant.streamlit.app/cards. The active application has two pages. Artwork identifiers, card catalogue IDs, browsing order and issuer register are maintained together. Historical pages are archived. Current source-level consistency tests do not establish live issuer accuracy, real-user validation or successful deployment.

## Final UX alignment (13 November 2026)

The comparison remains the only primary task: tighter spacing, clearer merchant labels without relaxing eligibility, a visible cap assumption and a consistent Compare my cards button. Unresolved results explain next steps; material reward-form differences and planned-purchase cautions are visible before technical diagnostics. Official sources precede AI verification. The optional `FEEDBACK_URL` Streamlit Secret can point to a team-approved feedback form; without it, the app offers the repository's public GitHub issue creation page with a warning not to share personal data or transaction details. The app itself does not collect feedback or save a wallet. No new payment, subscription, tracking, login or ranking feature has been added. These are design-review refinements, not claims of observed customer testing. Issuer rules and Gemini validation are unchanged.

### Explanation and cap-label polish (13 November 2026)

Amazon Pay reasons identify the modeled purchase route and Prime status where relevant. For Amazon Pay, Scapia and Kiwi, the approved redemption caution uses the mandatory issuer condition rather than repeating the same restriction. Both AI-assisted and rules-only views retain that condition. The ORNGE input names cashback already earned in the 5% category; its tooltip explains the shared cap. Reward-form capitalization is preserved in the result. No rates, limits, eligibility, monetary calculations, AI response schema or six grounding checks have changed. AI remains opt-in by default for new sessions; update submission documentation accordingly. Additional regression definitions cover the ₹74,230.33 eligible Amazon Prime example (₹3,711.52 Amazon Pay balance versus ₹300 ORNGE, assuming ₹1,200 of its ₹1,500 shared cap already earned), route-specific reasons and non-repetitive conditions. These are modeled expectations, not independent issuer confirmation or executed live tests.

### Contextual recommendation explanations (13 November 2026)

The approved reason options now describe modeled causes of a higher reward rather than restating the difference already displayed in the result panel. When the runner-up has a binding, verified-in-model cashback cap, every available reason (including rules-only fallback) includes its entered remaining allowance. Equal rates, uncapped applicable tiers and two binding caps are described only when supported by the calculated result objects. No claim is made about a cap when the comparator is unresolved or its cap does not bind. The existing response schema, six checks, issuer conditions and financial engine are unchanged. The ₹31,253.52 eligible Amazon Prime example should show ₹1,562.68 Amazon Pay balance versus ₹300 ORNGE cashback (₹1,200 previously earned), explaining the equal 5% rates and different remaining allowances. The Slide 11 SBI-leading scenario is also covered. These are regression expectations, not completed live provider or customer tests.

### Comparison display polish (13 November 2026)

The reward comparison uses plain-language cashback descriptions, a separate reward-form line, and a binding-cap label where the model confirms a cap limits the reward. Issuer review dates use a readable format without implying a fresh review. Redemption guidance is specific to selected card forms. `display_text.py` contains presentation-only helpers; six regression test definitions cover the changes. No financial rules or AI validation changes. Live rendering and test execution remain to be verified.

### Contextual AI decision guidance (13 November 2026)

The full factual comparison and mandatory issuer caution remain available without AI. An opted-in, successfully validated Gemini response additionally selects a practical decision tip from options grounded in the computed purchase, reward forms and applicable cap. The tip appears under What this means for you. The response schema adds `tip_id`; a seventh check rejects unknown or missing tip choices. No unrestricted model prose is rendered. The earlier six-check descriptions in historical change notes refer to previous versions. No issuer rules, calculation, ranking, provider configuration or data persistence changed. This is a testable hypothesis about incremental decision value, not proof of customer benefit. Compare the two modes with real users and update Slide 9 and the PRD to describe the actual seven checks and bounded tip selection. No API key changes are required.

### Test Case 1 — usability refinements (13 November 2026)

The sidebar removes the redundant opening label and uses shorter workflow and privacy wording. The AI checkbox explains sharing with Google Gemini in plain language and remains opt-in. The initial excluded-purchase checkbox refinement was superseded by the scope notice in the page heading and a collapsed unsupported-purchases list next to Compare; there is no separate exclusion checkbox. Merchant QR / UPI is offered only when YES BANK Klick RuPay Credit Card (Kiwi) or Scapia Federal RuPay is selected; the Kiwi-specific QR route appears only with Kiwi. Removing the last supported RuPay card resets UPI to Online, clears the previous result and updates the temporary session selection. Invalid saved merchant routes are reset to Not sure when their options disappear. The shared support predicate is identical to the prior engine eligibility guard; no reward rates, calculations, AI checks or scope have changed. Five regression definitions cover the payment-choice behavior. Retest these observations with the participant; this commit records implemented refinements, not a completed retest.

### Test Case 1 — purchase-scope simplification (13 November 2026)

Removed the standalone EMI/international/excluded-purchase checkbox and its obsolete session-state and validation branches. The supported domestic, non-EMI purchase scope is stated in the page subtitle, with the collapsed unsupported-purchases list next to the Compare button. A collapsed list and shared sidebar help explain unsupported purchases. The app continues to apply modeled issuer/category exclusions, but cannot automatically detect EMI, international payments or unsupported spend disguised as an eligible category; users must follow the stated scope. No new confirmation widget, financial rule change or AI change. Retest whether the participant notices and understands the restored heading scope notice before comparing.

### Kiwi official-source refresh (13 November 2026)
Updated the YES BANK Klick RuPay Credit Card (Kiwi) identity, source links, fee and reward conditions; initially replaced third-party artwork with issuer-guide artwork (superseded by the latest team-supplied green YES BANK RuPay image). The Kiwi application page is a marketing reference, not a blanket reward rule. The standard single-purchase engine is unchanged: 1.5% eligible QR and 0.5% eligible online, completed ₹100 blocks and a confirmed remaining rupee allowance. The optional Neon and Boost memberships are documented but not compared. The policy/FAQ cap-unit discrepancy is disclosed; redemption is in 500-Kiwi blocks. No customer testing or live image-render validation is claimed by this update.

### Result-first layout — usability refinement (13 November 2026)
Step 03 now starts directly with the highlighted decision (or the appropriate unresolved/unavailable state), followed by the reward comparison and the relevant cap/conditional-estimate note. The AI or rules-only explanation appears below the comparison; both the highlighted decision and comparison render before a Gemini request. Removed the duplicated category, payment-method and merchant chips above the result. The actual purchase selectors remain in Step 02; the first three ranked cards and full-list expander are retained. No financial logic, AI validation, consent, or issuer-source changes. Confirm the new order on desktop and mobile, with AI enabled and disabled; live rendering has not been tested in this update.

### Input heading spacing refinement
Added explicit spacing below the Step 01 and Step 02 headings (10px), plus 12px above Step 02 to separate it from the card selector. Scoped to the purchase panel and applied on desktop and mobile. Step 03, native widget behavior, result ordering, reward logic and AI consent/validation are unchanged. Browser rendering still needs visual confirmation.

### Kiwi green artwork correction
The Supported cards catalogue previously used the green Kiwi promotional screenshot; that asset has since been replaced by the specific green YES BANK RuPay card image supplied by the team. The prior blue YES BANK guide image is no longer used for card art; the guide remains an issuer terms reference. This is a visual-only change; card identity, virtual-card scope, reward rules and comparison behavior are unchanged. The local asset avoids dependency on external image hosts; live browser rendering remains to be checked.

### Comparable-card suggestions and Kiwi issuer evidence
A positive comparable reward now produces a provisional highlighted suggestion even if another selected card is unresolved. All selected cards appear in partial comparisons, with unresolved cards identified and a note that the outcome may change. Ties remain ties; when no positive comparable reward exists, no reward-based recommendation is fabricated. Partial suggestions use the existing deterministic explanation; Gemini is not called for incomplete comparisons. Added the official YES BANK Klick product page and disclosed separate non-UPI YES Rewardz points (not valued or modeled). Kiwi QR/online UPI rates remain unchanged. The supplied green YES BANK RuPay image replaces the earlier promotional image. Live UI validation remains pending.

### Repository synchronization — 13 November 2026
The active catalogue uses the specific green YES BANK RuPay image (`assets/kiwi-yes-klick-green.webp`); the superseded promotional asset has been removed from the active tree. Catalogue, source register, artwork register and current documentation agree. Added result-rendering regression tests for provisional suggestions, ties and no positive comparable rewards, and a local artwork integrity check. For the ₹50,099 Myntra scenario with unused applicable caps, the modeled comparison is SBI ₹2,000, Scapia Visa ₹1,002 (rounded coins), Amazon Pay ₹500.99 and Kiwi unresolved; SBI is the provisional suggestion. No live customer test or provider verification is implied.
