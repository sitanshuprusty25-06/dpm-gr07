# GenAI Card Choice Assistant (V1)

Digital Product Management, Group 07, EMBA 2025-27, IIM Visakhapatnam.

**Live app:** _paste your Streamlit Cloud URL here_

## What it does
One user (a selective comparer), one problem (choosing among your own cards at payment is slow
and uncertain), one use case (check a specific purchase before paying). The screens follow
`Card_Choice_Assistant_Prototype.html`, laid out as a small website (Home, Compare my cards, Supported cards, How it works, Roadmap, FAQ, About & contact).

1. **Compare my cards** page, left side: select the supported cards you hold.
2. Enter the amount and category (optionally, bonus already used this month). The result appears on the right.
3. A rules engine applies each card's dated rules and ranks the cards by estimated rupee benefit.
4. The top card, its benefit, a **Watch out** key condition and a rule-based explanation are shown.
5. **Reword with AI** (optional) asks Gemini to reword the explanation in plain language.

A **Theme** switch at the top gives Auto (follows your device), Light and Dark.

## How GenAI is used (one capability)
GenAI only rewords. It does not calculate, rank or recommend. The default explanation is built
from the rules. When the user clicks **Reword with AI**, Gemini receives only the computed facts.
A checker requires the card's name and that every number in the AI text appears in those facts.
On any mismatch, error or missing API key, the rule-based explanation stays and the screen says why.

## Not in V1 (see PRD roadmap)
Login and saved wallet, automatic monthly cap tracking, bank or transaction linking, browser
extension, net benefit after fees, partner integration. No database; nothing is stored.

## Files
The app is a small website: a header with a Theme switch, top navigation, pages, and a footer.

| File | Purpose |
|---|---|
| `app.py` | Entrypoint: wide layout, top navigation, shared header and footer |
| `ui.py` | Theme (Auto/Light/Dark), CSS, header, footer |
| `results.py` | Result panel, watch-out box, explanation and AI button shared by Home and Compare |
| `views/home.py` | Landing page with a live example |
| `views/compare.py` | The product: pick cards, enter a purchase, see the result |
| `views/supported_cards.py` | The card catalogue with dates and sources |
| `views/how_it_works.py` | Rules / AI / checker explained |
| `views/roadmap.py` | What V1 does and what is left for later |
| `views/faq.py` | Common questions |
| `views/about.py` | About and contact (team details are placeholders to fill in) |
| `cards.py` | Dated catalogue of supported cards (KNOW layer). **Edit this to change cards** |
| `rules_engine.py` | Benefit calculation, ranking, key condition (no GenAI) |
| `explain.py` | Gemini rewording and the number checker |
| `test_rules.py` | Hand-checked tests of rules and checker |
| `.streamlit/config.toml` | Optional accent colour |

Dummy items (Sign in, Blog, Privacy policy, Terms of use) are shown as "coming soon" and do nothing.

**Phone vs desktop.** Streamlit serves one app, so there is no separate mobile site. Instead `ui.py` reads the
browser's User-Agent (`detect_device`) and the pages switch layout: columns stack, the category picker becomes a
dropdown, and the header and footer are compacted. CSS media queries also adapt to narrow windows. The footer has a
**View as** switch (Auto / Mobile / Desktop) so you can preview the phone layout on a laptop. Tablets get the desktop layout.
Keep `views/` together with `app.py` when uploading to GitHub.
## How to replace the sample cards
The cards in `cards.py` are **fictional samples from the prototype**. For user testing, use real ones.

1. Pick 5 to 8 real cards your interviewees actually hold. Open each issuer's official
   "Most Important Terms and Conditions" or rewards page. Note the page link and today's date.
2. For each card, in `cards.py`, copy one `{ ... }` block in `CARDS` and edit:
   - `id` (short, no spaces), `name`, `issuer`, `chip` (a coloured-square emoji), `hue` (hex colour), `fee` (annual fee).
   - `base`: reward as a percent of spend on ordinary purchases. Convert points to rupees first:
     rupees per point x points per Rs 100 = percent. Example: 4 points per Rs 150 at Rs 0.25 per point
     is about 0.67%. Set `point_value` only if you want points shown.
   - `rules`: one entry per bonus category, for example `"dining": {"rate": 5, "cap": 500}`.
     `rate` is a percent. `cap` is the most bonus in rupees per month. `min` is the smallest purchase that earns
     the bonus. `max` is the largest part of one purchase that earns it. Leave out any that do not apply.
   - `excl`: categories with no reward, with the reason, for example `"fuel": "No rewards on fuel"`.
   - `last_verified` (today's date) and `source` (the link you used).
3. Category ids you can use: `dining, groceries, travel, shopping, fuel, bills, entertainment, other`.
   To add one, add a line to `CATEGORIES` in `cards.py`.
4. Set `SAMPLE_DATA = False` (removes the "sample data" labels) and set `DEFAULT_WALLET = []`
   so testers choose their own cards.
5. Run `python -m unittest -v`. The tests in `test_rules.py` that name the sample cards will fail once the
   samples are gone. Update them to your real cards or delete them. `test_every_rule_category_exists`
   should keep passing: it catches mistyped category ids.
6. Commit to GitHub. Streamlit Cloud redeploys automatically.

Do not claim exact rewards: card terms change, and the app shows the verification date for this reason.

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
Streamlit Community Cloud, main file `app.py`. To switch on AI rewording, add `GEMINI_API_KEY`
under App settings > Secrets. The app works without it (rule-based explanation only).
Optional secret `FEEDBACK_URL` (for example a Google Form link) adds a "Report wrong info" button.

## AI use disclosure
_Team to complete: which AI tools were used (for example, to help write this code), for what,
and what the team verified itself. Required by the project guidelines._
