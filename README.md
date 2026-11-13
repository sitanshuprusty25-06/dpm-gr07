# GenAI Card Choice Assistant — Group 07

IIM Visakhapatnam · EMBA 2025–27 · Digital Product Management

**Live MVP:** https://card-choice-assistant.streamlit.app/

**Source:** https://github.com/sitanshuprusty25-06/dpm-gr07

## Product scope

One user: the multi-card holder who selectively compares payment benefits.
One problem: effort and uncertainty in choosing a card before a purchase.
One use case: compare supported cards already owned for one domestic, non-EMI purchase.
One workflow: choose cards → enter amount (rupees and paise), category and payment context → compare → understand the result.
One GenAI capability: select an approved reason and caution for a calculated result.

The landing page is **Compare my cards**. The only other primary page is **Supported cards**, a reference catalogue with exact product variants, reward descriptions, fees, conditions and issuer links. A compact, theme-inheriting shared collapsible sidebar shows the value proposition, three-step workflow, privacy and key limitations. Detailed help is collapsed inside the sidebar. Native Streamlit auto mode shows it on larger screens and hides it initially on small devices; users can toggle it. The main footer retains only a short disclaimer. The five retired supporting pages are preserved under [`archive/`](archive/README.md) for development history only; they are not part of active navigation. Future features belong in the team's PRD and roadmap, not the running MVP.

## Calculation and AI

- The deterministic Python engine calculates modeled eligibility, reward rates, minimum spends, caps and rankings from dated issuer reference material.
- A unique positive and comparable result can trigger an optional Gemini request on the explicit Compare action. Gemini selects a reason and caution from approved facts; six checks validate response format, recommended card, amount, reward type, reason and caution.
- Rules-based output remains available without AI or if the provider fails. A tie, unresolved applicable reward, unsupported route or zero reward does not trigger AI.
- The app renders the calculated result before requesting AI. A changed input invalidates the previous result; ordinary reruns do not trigger another request.
- Rewards are conditional estimates, not guaranteed cashback. Actual merchant MCC/MID, issuer posting, exclusions, caps, refunds and settlement may affect rewards. Restricted redemption values are not cash. Fees, interest and unmodeled promotions are excluded.
- Zero prior cashback assumes an unused applicable cap. The input area shows a visible assumption summary for applicable capped cards; the optional adjustment uses plain-language reward buckets and cycle-specific help. Kiwi requires a known remaining reward allowance. Where terms cannot establish an applicable reward, the engine withholds a definitive winner.

The ten supported products are Amazon Pay ICICI, Flipkart Axis, original Swiggy HDFC, Swiggy BLCK, Swiggy ORNGE, CASHBACK SBI, Kiwi YES BANK Klick (standard non-Neon), Scapia Federal Visa, Scapia Federal RuPay and HSBC Live+. Catalogue browsing order is market-informed but never affects the purchase ranking. See `card_catalog/market_order.json`, `card_catalog/fine_print_review.md` and `card_catalog/link_review.md` for evidence and limitations. The fine-print review is dated 12 November 2026; supporting notes and the register reflect the current implementation, including Axis remaining-cap handling, Amazon travel and digital routes, HDFC variant-specific eligibility and Kiwi's required remaining allowance. The team must independently verify issuer accuracy.

## Privacy and limits

No login, bank credentials, card numbers, database, payment initiation or persistent user wallet. Temporary Streamlit session state holds selections and purchase context, including route and excluded-spending choices when switching pages. The version-controlled catalogue contains public issuer reference data, not user data. AI is off by default for new sessions. Opting in sends computed purchase facts and relevant card names to Google Gemini on eligible comparisons. The Compare my cards action remains the same with or without AI; an existing session retains its choice. Hosting and AI providers have their own policies; no claim is made about their retention. This is an independent academic prototype, not financial advice or a bank-endorsed service.

## Main files

- `app.py` — two-page navigation
- `views/compare.py` — purchase inputs and comparison
- `views/supported_cards.py` — reference catalogue
- `ui.py`, `.streamlit/config.toml` — shared sidebar guidance, native light/dark theme and layout
- `cards.py`, `card_catalog/` — read-only data, issuer sources and caveats
- `rules_engine.py` — modeled calculations and ranking
- `explain.py`, `results.py` — approved AI explanation, validation, fallback and result presentation
- `assets/card_images.json`, `assets/README.md` — product artwork provenance and current layout
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

Smoke test: open the root URL, select Swiggy BLCK HDFC and CASHBACK SBI, enter ₹1,200, online, dining, eligible Swiggy food delivery and unused caps. Expected modeled estimates are ₹120 and ₹60. Change BLCK Swiggy cashback already earned to ₹1,440 for a ₹60/₹60 tie, then ₹1,470 for ₹30/₹60 with SBI leading. SBI online cap must remain unused. These are expected model outcomes, not executed live tests. For an AI-assisted run, first opt in to the AI explanation, compare, and check the six PASS results under AI verification. Repeat with AI disabled, navigate to Supported cards and back, and check that the inputs persist. Test a fractional purchase amount (e.g. ₹1,200.50), a partially used cap (e.g. ₹1,999.75), a tie, an unconfirmed route, a zero reward, and both light/dark modes on desktop and phone. Verify that the sidebar appears on larger screens, can be collapsed, is initially hidden on small devices, and does not obstruct the comparison. Check the visible cap assumption, Not sure merchant recovery, restricted reward-form notice, planned-purchase caution and reporting link. These are proposed checks, not claims of completed testing.

## Course evidence and maintenance

The simplified information architecture reflects the course emphasis on the smallest useful workflow, feature criticality and usability. It is an iteration based on interface review, not evidence of completed user validation. Document the two to three real-user tests required by the project, actual observations and changes made, and compare understanding with versus without AI. Keep proposed monetization, future integrations and additional features in the PRD.

Check issuer documents and add regression tests before changing the financial rules. The team must understand and verify the code, document AI-assisted coding and follow the instructor's AI-use policy for all submitted artifacts. Do not submit AI-generated report/PRD text, images or tables unless the instructor expressly permits them.

## Repository synchronization

The official deployment is the root URL above; the reference catalogue is https://card-choice-assistant.streamlit.app/cards. The active application has two pages. Artwork identifiers, card catalogue IDs, browsing order and issuer register are maintained together. Historical pages are archived. Current source-level consistency tests do not establish live issuer accuracy, real-user validation or successful deployment.

## Final UX alignment (13 November 2026)

The comparison remains the only primary task: tighter spacing, clearer merchant labels without relaxing eligibility, a visible cap assumption and a consistent Compare my cards button. Unresolved results explain next steps; material reward-form differences and planned-purchase cautions are visible before technical diagnostics. Official sources precede AI verification. The optional `FEEDBACK_URL` Streamlit Secret can point to a team-approved feedback form; without it, the app offers the repository's public GitHub issue creation page with a warning not to share personal data or transaction details. The app itself does not collect feedback or save a wallet. No new payment, subscription, tracking, login or ranking feature has been added. These are design-review refinements, not claims of observed customer testing. Issuer rules and Gemini validation are unchanged.
