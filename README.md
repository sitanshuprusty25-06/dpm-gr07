# GenAI Card Choice Assistant (V1)

Digital Product Management, Group 07, EMBA 2025-27, IIM Visakhapatnam.

**Live app:** _paste your Streamlit Cloud URL here_

## What it does
One user (a selective comparer), one problem (choosing among your own cards at payment is slow
and uncertain), one use case (check a specific purchase before paying).

1. Select the supported cards you hold.
2. Enter the purchase amount and category (optionally, bonus already used this month).
3. A rules engine applies each card's dated rules and ranks the cards by estimated rupee benefit.
4. The top card's key condition (cap, minimum, per-purchase limit or exclusion) is shown.
5. GenAI writes a plain-language explanation of the computed result.

## How GenAI is used (one capability)
GenAI only writes the explanation. It does not calculate, rank or recommend.
A checker compares every number in its text with the rules output and requires the top card's
name. On any mismatch, error or missing API key, the app shows a plain template built from the
rules instead, and labels which one it is showing.

## Not in V1 (see PRD roadmap)
Login and saved wallet, monthly cap tracking, bank or transaction linking, browser extension,
net benefit after fees, partner integration. No database; nothing the user enters is stored.

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit screen and workflow |
| `cards.py` | Dated catalogue of supported cards (KNOW layer) |
| `rules_engine.py` | Benefit calculation and ranking (no GenAI) |
| `explain.py` | Gemini explanation, number checker, template fallback |
| `test_rules.py` | Hand-checked tests of rules and checker |

## Important: card data
The five cards in `cards.py` are **illustrative samples with made-up terms**. Replace them with
real cards, verified against the issuer's published terms, and update `last_verified` and
`source` before any user testing.

## Run locally
```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then add your Gemini key
streamlit run app.py
python -m unittest -v            # run the tests
```

## Deploy
Streamlit Community Cloud, main file `app.py`; add `GEMINI_API_KEY` under App settings > Secrets.

## AI use disclosure
_Team to complete: which AI tools were used (for example, to help write this code), for what,
and what the team verified itself. Required by the project guidelines._
