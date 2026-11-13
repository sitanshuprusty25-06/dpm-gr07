# Card Choice Assistant — Group 07

IIM Visakhapatnam · EMBA 2025–27 · Digital Product Management

**Live MVP:** https://card-choice-assistant.streamlit.app/  
**Repository:** https://github.com/sitanshuprusty25-06/dpm-gr07

## Product and scope

**Value proposition:** Help multi-card holders choose which card they already own to use for a planned purchase, without checking several apps or websites.

One user, one purchase decision, one workflow: select owned cards → enter purchase amount, category and payment route → compare → decide. Domestic, non-EMI purchases only. The landing page **Compare my cards** and the **Supported cards** reference catalogue are the only active pages. Independent academic decision-support disclosure is visible at the top of both pages. The shared sidebar retains the three-step onboarding guide (select cards, enter purchase details, compare and decide). No payment execution, application for new cards, wallet storage, bank connection or product recommendation beyond the selected cards.

Ten supported products: Amazon Pay ICICI, Flipkart Axis, Swiggy HDFC (original), Swiggy BLCK, Swiggy ORNGE, CASHBACK SBI, YES BANK Klick (Kiwi standard plan), Scapia Federal Visa, Scapia Federal RuPay and HSBC Live+.

## Decision and GenAI capability

- Python evaluates eligible spend, rates, minimums, exclusions, cashback caps and redemption values using the dated issuer catalogue. Rankings use modeled rupee-equivalent value, not necessarily cash.
- Navy: highest calculated reward among comparable cards. Purple (AI opt-in only): Gemini selects a locally approved recommendation or conditional alternative based on reward form. Both panels display computed facts; the user decides.
- A unique positive leader among comparable cards can receive AI guidance even if others are unresolved. Ties, no positive comparable result and unconfirmed high-value UPI routes do not trigger AI. Unresolved cards are never treated as zero or offered as AI choices.
- Eight grounding checks: exact response schema, approved option, card identity, calculated amount, reward form, approved rationale, issuer reference and positive eligible comparison. The selected option is bound to the current payload fingerprint. No generated financial prose is rendered. A failed or interrupted request leaves the rule-based decision intact; explicit retry is available.
- Top three comparisons remain visible, with the complete selection expandable. The UPI view focuses on the two modeled RuPay cards. Unconfirmed UPI shows conditional estimates, not a ranked decision; above ₹1 lakh the user must check actual applicable limits. The threshold is a UI precaution, not a universal UPI limit.
- Zero prior cashback assumes unused allowance. Kiwi needs an actual remaining monthly cap to rank positive rewards; its issuer Rewardz points and optional Neon/Boost memberships are not valued.

## Privacy and limitations

No login, card number, banking credential, payment initiation, database or persistent wallet. Temporary session state keeps selections. Gemini is off by default and receives approved purchase/reward context only on explicit opt-in comparison or retry. Provider policies apply; no promises about provider retention. No API credentials are committed.

Reward estimates are conditional on actual merchant classification, payment acceptance, credit limits, issuer posting and applicable terms. Fees, interest, unmodeled promotions and redemption fees are excluded. Sources are dated public references, not live issuer verification. Do not spend more simply to earn rewards. Review the official evidence in `card_catalog/` before assessment or real use.

## Repository structure

| File | Purpose |
| --- | --- |
| `app.py`, `views/`, `ui.py` | Two-page Streamlit interface |
| `cards.py`, `card_catalog/` | Ten card products, issuer rules, sources and evidence |
| `rules_engine.py` | Deterministic calculations and UPI scenario previews |
| `ai_guidance.py`, `explain.py` | Approved options, grounding checks and shared explanation/provider helpers |
| `results.py`, `display_text.py` | Result presentation and conditions |
| `visuals.py`, `assets/` | Reference images and labeled fallback |
| `test_rules.py`, `test_guidance.py`, `test_result_rendering.py` | Regression coverage |
| `.streamlit/config.toml`, `requirements.txt` | Deployment configuration |

Retired prototype pages and the obsolete PDF-artwork extractor were removed from the active tree. Git history retains their earlier versions. The legacy explanation tests remain as regression evidence for shared helpers; the active recommendation path uses `ai_guidance.py`.

## Run and verify

GitHub Actions runs the regression suite and syntax checks on pushes and pull requests. Tests mock provider responses; they do not establish live Gemini or issuer accuracy.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v
python -m compileall -q app.py cards.py rules_engine.py explain.py ai_guidance.py results.py views ui.py visuals.py
streamlit run app.py
```

Deploy `app.py` from `main` on Streamlit Community Cloud. Configure `GEMINI_API_KEY` and optionally `GEMINI_MODEL` in Streamlit Secrets; default model `gemini-3.5-flash-lite`. Never put a real key in test code or Git. Optional `FEEDBACK_URL` points to a team-approved form; otherwise reporting uses a public GitHub issue with a privacy warning.

### Regression and live smoke cases

All values below are modeled expectations, not claims of executed user tests or confirmed issuer settlements. Assume unused applicable caps unless stated.

| Scenario | Expected |
| --- | --- |
| ₹1,200 eligible Swiggy food delivery, BLCK + SBI | ₹120 vs ₹60; BLCK leads |
| Same, BLCK prior Swiggy cashback ₹1,440 | ₹60 tie; no forced AI choice |
| ₹4,500 eligible Myntra, all ten cards | Axis ₹337.50; SBI and BLCK ₹225; eligible AI guidance with partial scope |
| ₹5,60,000 eligible Myntra, all ten cards | Scapia Visa ₹11,200 travel value; HSBC ₹8,400 cashback; approved conditional alternative |
| ₹2,50,000 dining UPI, route/limits unconfirmed | Kiwi ₹3,750 before cap; Scapia RuPay ₹2,500 travel value; preview only |
| AI off / invalid AI response | Calculated result remains; no unchecked AI claims |

Verify on desktop and phone, light and dark mode, all result states, navigation, cap inputs, opt-in, failure/retry, official links and the eight checks. Keep actual user observations and professor-required testing evidence separate from expected scenarios. Check the hosted deployment's commit and provider availability before final submission.

## Course evidence

The MVP prioritizes the single purchase decision, feature criticality, constrained GenAI and a clear user-controlled choice. The team should record actual real-user tests, changes made, and evidence of how AI guidance affects understanding. Future features belong in the PRD, not this release. Follow the instructor's AI-use policy and independently verify the source code and issuer evidence. Git history is the development log; no duplicate historical release notes are maintained in this README.
