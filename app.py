"""GenAI Card Choice Assistant: V1 (Group 07, DPM, IIM Visakhapatnam).

One user (selective comparer), one problem, one use case (check a purchase before
paying), one workflow, one AI capability (plain-language rewording of a computed result).
Flow follows Card_Choice_Assistant_Prototype.html.
"""

import html
import os

import streamlit as st

from cards import CARDS, CATEGORIES, DEFAULT_WALLET, SAMPLE_DATA
from explain import ai_reword
from rules_engine import category_label, highlight, inr, key_condition, rank, template_explain

st.set_page_config(page_title="Card Choice Assistant", page_icon="💳", layout="centered")

# ---------------------------------------------------------------- theme

PALETTES = {
    "light": {
        "bg": "#E9F0EF", "surface": "#FFFFFF", "ink": "#0B2E33", "muted": "#46666D",
        "line": "#CFDDDB", "brand": "#0F5C63", "brand_ink": "#FFFFFF", "soft": "#E3EEEC",
        "panel": "#0F3D44", "panel_ink": "#EAF7F4", "panel_muted": "#A8CBC7",
        "accent": "#F2A93B", "warn_bg": "#FCEBEC", "warn_ink": "#8E2433", "ok": "#1C7C5A",
    },
    "dark": {
        "bg": "#081A1D", "surface": "#102A2E", "ink": "#E6F2F0", "muted": "#9BB8B4",
        "line": "#22444A", "brand": "#7FD1B9", "brand_ink": "#06282B", "soft": "#16373B",
        "panel": "#175057", "panel_ink": "#F0FBF8", "panel_muted": "#B6D9D4",
        "accent": "#F2A93B", "warn_bg": "#3A1A20", "warn_ink": "#F3B4BC", "ok": "#6FD3A8",
    },
}


def effective_theme(choice):
    """Auto follows the Streamlit theme (Settings menu / system); otherwise the user's pick."""
    if choice == "Light":
        return "light"
    if choice == "Dark":
        return "dark"
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def custom_css(p):
    """Styles for our own HTML blocks. Always injected."""
    return f"""
:root {{ --bg:{p['bg']}; --surface:{p['surface']}; --ink:{p['ink']}; --muted:{p['muted']};
  --line:{p['line']}; --brand:{p['brand']}; --brand-ink:{p['brand_ink']}; --soft:{p['soft']};
  --panel:{p['panel']}; --panel-ink:{p['panel_ink']}; --panel-muted:{p['panel_muted']};
  --accent:{p['accent']}; --warn-bg:{p['warn_bg']}; --warn-ink:{p['warn_ink']}; --ok:{p['ok']}; }}
.cca-panel {{ background:var(--panel); border-radius:20px; padding:20px; margin-top:12px; position:relative; }}
.cca-panel .kicker {{ font-size:.85rem; color:var(--panel-muted); }}
.cca-panel .cname {{ font-size:1.5rem; font-weight:700; color:var(--panel-ink); margin-top:2px; }}
.cca-panel .issuer {{ font-size:.88rem; color:var(--panel-muted); }}
.cca-panel .figure {{ font-size:3.2rem; line-height:1.05; font-weight:700; color:var(--accent); margin:14px 0 4px; }}
.cca-panel .delta {{ font-size:.95rem; color:var(--panel-ink); }}
.cca-panel .swatch {{ position:absolute; right:18px; top:18px; width:54px; height:36px; border-radius:7px;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.3); }}
.cca-watch {{ background:var(--warn-bg); border-radius:14px; padding:12px 14px; margin-top:12px; }}
.cca-watch .wt {{ font-weight:700; color:var(--warn-ink); }}
.cca-watch .wb {{ color:var(--warn-ink); }}
.cca-explain {{ border:1.5px solid var(--line); border-radius:14px; padding:14px; margin-top:12px; }}
.cca-explain .tag {{ display:inline-block; font-size:.75rem; border-radius:999px; padding:2px 9px;
  background:var(--soft); color:var(--muted); margin-bottom:6px; }}
.cca-explain .tag.ai {{ background:var(--ok); color:var(--surface); }}
.cca-explain .txt {{ color:var(--ink); }}
.cca-others {{ margin-top:6px; }}
.cca-row {{ display:flex; align-items:center; gap:10px; padding:10px 0; border-top:1px solid var(--line); }}
.cca-row:first-child {{ border-top:0; }}
.cca-row .dot {{ flex:none; width:12px; height:12px; border-radius:50%; }}
.cca-row .nm {{ flex:1; min-width:0; color:var(--ink); }}
.cca-row .nm b {{ font-weight:650; }}
.cca-row .why {{ display:block; font-size:.8rem; color:var(--muted); }}
.cca-row .amt {{ font-weight:700; font-size:1.05rem; color:var(--ink); }}
.cca-row.best .amt {{ color:var(--ok); }}
.cca-flag {{ font-size:.75rem; color:var(--muted); border:1px solid var(--line); border-radius:999px;
  padding:3px 10px; white-space:nowrap; display:inline-block; }}
.cca-step {{ border:1.5px solid var(--line); border-radius:14px; padding:12px 14px; margin:8px 0; color:var(--ink); }}
.cca-step span {{ color:var(--muted); font-size:.9rem; }}
"""


def streamlit_override_css(p):
    """Re-colours Streamlit's own widgets. Injected only when Light or Dark is forced, so
    that the page is consistent whatever theme Streamlit itself is using."""
    return f"""
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{p['bg']}; color:{p['ink']}; }}
[data-testid="stHeader"] {{ background:{p['bg']}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label,
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] {{ color:{p['ink']}; }}
[data-testid="stCaptionContainer"] {{ color:{p['muted']}; }}
.stApp input, .stApp textarea {{ background:{p['surface']}; color:{p['ink']}; }}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
[data-testid="stNumberInputContainer"] {{ background:{p['surface']}; border-color:{p['line']}; }}
[data-testid="stNumberInputContainer"] button {{ background:{p['soft']}; color:{p['ink']}; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {{ background:{p['surface']}; color:{p['ink']}; }}
.stButton > button, .stLinkButton > a {{ background:{p['surface']}; color:{p['ink']}; border:1px solid {p['line']}; }}
.stButton > button p, .stLinkButton > a p {{ color:inherit; }}
.stButton > button[kind="primary"] {{ background:{p['brand']}; color:{p['brand_ink']}; border-color:{p['brand']}; }}
[data-baseweb="tab"] {{ color:{p['muted']}; }}
[data-baseweb="tab"][aria-selected="true"] {{ color:{p['ink']}; }}
[data-testid="stExpander"] details {{ background:{p['surface']}; border-color:{p['line']}; }}
[data-testid="stAlert"] {{ background:{p['soft']}; color:{p['ink']}; }}
"""


def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


# ---------------------------------------------------------------- state

if "init" not in st.session_state:
    st.session_state["init"] = True
    for c in CARDS:
        st.session_state[f"w_{c['id']}"] = c["id"] in DEFAULT_WALLET
    st.session_state["cat"] = "travel"
    st.session_state["theme"] = "Auto"

cat_ids = [cid for cid, _ in CATEGORIES]


def pick_example(amount, cat):
    st.session_state["amount"] = amount
    st.session_state["cat"] = cat
    st.session_state["run"] = True


# ---------------------------------------------------------------- header + theme

head_l, head_r = st.columns([3, 2])
with head_l:
    st.title("Card Choice Assistant")
with head_r:
    st.radio(
        "Theme", ["Auto", "Light", "Dark"], horizontal=True, key="theme",
        help="Auto follows your device or the Streamlit Settings menu.",
    )

theme_name = effective_theme(st.session_state["theme"])
palette = PALETTES[theme_name]
css = custom_css(palette)
if st.session_state["theme"] != "Auto":
    css += streamlit_override_css(palette)
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

if SAMPLE_DATA:
    st.markdown('<span class="cca-flag">Prototype · sample data</span>', unsafe_allow_html=True)
st.write("Check a purchase before you pay. Pick the cards you hold, enter the purchase, and see which of them gives the most benefit and why.")

tab_wallet, tab_pay, tab_about = st.tabs(["1. Wallet", "2. Check a purchase", "How it works"])

# ---------------------------------------------------------------- wallet

with tab_wallet:
    st.subheader("Which cards do you hold?")
    st.caption("Pick them from the list. We never ask for card numbers, expiry or CVV.")
    for c in CARDS:
        st.checkbox(f"{c['chip']} **{c['name']}** · {c['issuer']}", key=f"w_{c['id']}")
        st.caption(highlight(c))
    n_sel = sum(1 for c in CARDS if st.session_state.get(f"w_{c['id']}"))
    if n_sel == 0:
        st.warning("Select at least one card to continue.")
    else:
        note = " Sample wallet preselected for the demo." if SAMPLE_DATA else ""
        st.caption(f"{n_sel} card{'s' if n_sel > 1 else ''} selected.{note} Then open the next tab.")
    st.caption("Only the cards listed here are compared. Other cards are not.")

selected = [c for c in CARDS if st.session_state.get(f"w_{c['id']}")]

# ---------------------------------------------------------------- result rendering


def others_html(ranked, mark_best):
    rows = []
    for i, r in enumerate(ranked):
        best = " best" if mark_best and i == 0 else ""
        rows.append(
            f'<div class="cca-row{best}"><span class="dot" style="background:{r.card["hue"]}"></span>'
            f'<span class="nm"><b>{html.escape(r.card["name"])}</b>'
            f'<span class="why">{html.escape(r.reason)}</span></span>'
            f'<span class="amt">{inr(r.benefit)}</span></div>'
        )
    return '<div class="cca-others">' + "".join(rows) + "</div>"


def render_result(L):
    win, second, ranked, amount, cat = L["win"], L["second"], L["ranked"], L["amount"], L["cat"]
    label = category_label(cat).lower()
    if win.benefit <= 0.005:
        st.markdown(
            '<div class="cca-panel"><div class="kicker">No bonus on this purchase</div>'
            '<div class="cname">None of your cards earn rewards here</div>'
            '<div class="delta" style="margin-top:10px;color:var(--panel-muted)">'
            "Pay with whichever card is most convenient. Reasons are listed below.</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("**All your cards**")
        st.markdown(others_html(ranked, False), unsafe_allow_html=True)
        return

    if second and win.benefit - second.benefit > 0.005:
        delta = f"{inr(win.benefit - second.benefit)} more than {html.escape(second.card['name'])}"
    elif second:
        delta = f"Same as {html.escape(second.card['name'])}; lower annual fee wins"
    else:
        delta = "Add a second card to compare"

    st.markdown(
        f'<div class="cca-panel"><span class="swatch" style="background:{win.card["hue"]}"></span>'
        f'<div class="kicker">Use this card</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated benefit on this {inr(amount)} {label} purchase</div>'
        f'<div class="delta">{delta}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cca-watch"><div class="wt">Watch out</div>'
        f'<div class="wb">{html.escape(key_condition(win))}</div></div>',
        unsafe_allow_html=True,
    )

    # Explanation: rule-based by default, AI wording on request.
    box = st.empty()

    def draw_explanation():
        if L.get("ai_text"):
            tag, tag_cls, text = "AI wording · numbers verified", "tag ai", L["ai_text"]
        else:
            tag, tag_cls, text = "Rule-based explanation", "tag", template_explain(win, second, amount, cat)
        box.markdown(
            f'<div class="cca-explain"><span class="{tag_cls}">{tag}</span>'
            f'<div class="txt">{html.escape(text)}</div></div>',
            unsafe_allow_html=True,
        )

    draw_explanation()
    if st.button("Reword with AI", key="ai_btn"):
        with st.spinner("Rewording..."):
            text, status = ai_reword(
                win, second, amount, cat,
                api_key=get_secret("GEMINI_API_KEY"),
                model=get_secret("GEMINI_MODEL", "gemini-2.5-flash"),
            )
        L["ai_text"], L["ai_status"] = text, status
        draw_explanation()
    notes = {
        "no_key": "AI rewording is not set up in this deployment (no Gemini key). The rule-based explanation stays.",
        "error": "AI rewording is not available right now. The rule-based explanation stays.",
        "mismatch": "The AI text did not match the rules output, so the rule-based explanation stays.",
    }
    if L.get("ai_status") in notes:
        st.caption(notes[L["ai_status"]])

    st.markdown("**All your cards**")
    st.markdown(others_html(ranked, True), unsafe_allow_html=True)
    st.caption(
        f"Rules last verified {win.card['last_verified']}. Source: {win.card['source']}. "
        "Results are estimates for the supported cards and dated rules, not a guarantee of reward. "
        "Only your own selected cards are compared; no bank or merchant can change this order."
    )
    feedback_url = get_secret("FEEDBACK_URL")
    if feedback_url:
        st.link_button("Report wrong info", feedback_url)


# ---------------------------------------------------------------- check a purchase

with tab_pay:
    st.subheader("What are you buying?")
    if selected:
        st.caption(f"Comparing {len(selected)} card{'s' if len(selected) > 1 else ''} from your wallet.")
    else:
        st.caption("Add cards in the Wallet tab first.")

    st.caption("Try an example")
    ex_cols = st.columns(4)
    examples = [("₹8,000 travel", 8000, "travel"), ("₹12,000 online", 12000, "shopping"),
                ("₹800 dining", 800, "dining"), ("₹3,000 fuel", 3000, "fuel")]
    for col, (lbl, amt, ex_cat) in zip(ex_cols, examples):
        col.button(lbl, key=f"ex_{amt}_{ex_cat}", on_click=pick_example, args=(amt, ex_cat), use_container_width=True)

    st.number_input("Amount (₹)", min_value=0, step=100, value=None, format="%d", key="amount",
                    placeholder="e.g. 8000")
    st.radio("Category", cat_ids, format_func=category_label, horizontal=True, key="cat")

    # Optional: bonus already used this month, only for cards that have a capped bonus here.
    capped = [c for c in selected if c["rules"].get(st.session_state["cat"], {}).get("cap")]
    used_by_card = {}
    if capped:
        with st.expander("Optional: bonus already used this month"):
            st.caption("V1 does not track your spending. Leave these at 0 and it assumes each monthly cap is unused.")
            for c in capped:
                cap = c["rules"][st.session_state["cat"]]["cap"]
                used_by_card[c["id"]] = st.number_input(
                    f"{c['name']}: bonus already earned this month (₹, cap {inr(cap)})",
                    min_value=0, max_value=int(cap), step=50, value=0, format="%d",
                    key=f"used_{c['id']}_{st.session_state['cat']}",
                )

    go = st.button("Find my best card", type="primary", use_container_width=True)
    run = go or st.session_state.pop("run", False)

    if run:
        amount = st.session_state.get("amount")
        cat = st.session_state["cat"]
        error = None
        if not amount or amount <= 0:
            error = "Enter the purchase amount in rupees, for example 8000."
        elif amount > 10000000:
            error = "That amount is above the limit this app handles (₹1,00,00,000)."
        elif not selected:
            error = "Add at least one card in the Wallet tab to get a recommendation."
        if error:
            st.error(error)
            st.session_state.pop("last", None)
        else:
            ranked = rank(selected, cat, amount, used_by_card)
            st.session_state["last"] = {
                "ranked": ranked, "win": ranked[0],
                "second": ranked[1] if len(ranked) > 1 else None,
                "amount": amount, "cat": cat, "ai_text": None, "ai_status": None,
            }

    if st.session_state.get("last"):
        st.divider()
        render_result(st.session_state["last"])

# ---------------------------------------------------------------- how it works

with tab_about:
    st.subheader("How a recommendation is made")
    st.markdown(
        '<div class="cca-step"><b>1. Rules decide</b><br><span>A rules engine reads each card\'s rate, cap, '
        "minimum spend and exclusions, then works out the rupee benefit. No AI is involved in the maths.</span></div>"
        '<div class="cca-step"><b>2. AI explains</b><br><span>On request, the result is passed to a language model '
        "(Google Gemini) that only rewords it in plain language.</span></div>"
        '<div class="cca-step"><b>3. A checker verifies</b><br><span>Every number in the AI text must match the '
        "rules output. If anything differs, you keep the rule-based explanation.</span></div>",
        unsafe_allow_html=True,
    )
    st.subheader("About this version")
    bullets = []
    if SAMPLE_DATA:
        bullets.append("Card names, banks and terms are fictional and for demonstration only. They are not real issuer terms.")
    bullets += [
        "Benefit is estimated per purchase. You can enter bonus already used this month; the app does not track it for you.",
        "Nothing is saved: your choices reset when the page reloads.",
        "Results are estimates for the supported cards and dated rules, not a guarantee of reward.",
    ]
    st.markdown("\n".join(f"- {b}" for b in bullets))
    st.subheader("Neutrality")
    st.write("Only cards you own are ranked. No bank or merchant can pay to change the order.")

st.divider()
st.caption("Group 07, Digital Product Management, IIM Visakhapatnam.")
