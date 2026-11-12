# GenAI Card Choice Assistant — Group 07

IIM Visakhapatnam, EMBA 2025–27, Digital Product Management.

**Working application:** https://dpm-gr07-vhiacq5l6mcewqexuxwvl2.streamlit.app/

**Repository:** https://github.com/sitanshuprusty25-06/dpm-gr07

## Scope and use
One user (a multi-card selective comparer), one problem (choosing a card for one purchase), one workflow (select cards → enter purchase amount, category and online/offline context → apply issuer rules → read conditional comparison → optional Gemini rewording).

- The application is **stateless with respect to permanent user storage**. Streamlit temporarily holds user inputs in session state. No login, database or transaction linking.
- `card_catalog/` is **persistent reference data**, with issuer terms, source links, review dates and caveats. It is not user data.
- The five supported issuer products are CASHBACK SBI Card, HSBC Live+, Swiggy ORNGE HDFC, original Swiggy HDFC and Amazon Pay ICICI. Read their `card_catalog/source_notes/` before changing the rules.
- Merchant MCCs are generally unknown at checkout; results are estimates. HSBC boosted categories are sometimes intentionally marked **not comparable** when eligibility or after-cap cashback is unresolved. This protects users against false precision.
- Only domestic, non-EMI transactions in the supported categories are considered. Transaction fees, interest, international charges and most promotional offers are out of scope.

## Main files
- `card_catalog/cards.json` — structured card data; `source_register.csv` and `source_notes/` record evidence
- `cards.py` — load read-only issuer reference data
- `rules_engine.py` — deterministic cashback, exclusions, caps and rankings
- `views/compare.py` — session-only inputs, optional prior-cap usage, comparison form
- `results.py` — conditional recommendation / uncertainty output
- `explain.py` — Gemini rewording (optional), numerical/card-name checks and fallback
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
