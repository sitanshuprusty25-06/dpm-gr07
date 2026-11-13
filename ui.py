"""Shared look-and-feel for the Card Choice Assistant website: theme, CSS, header, footer.

Pages live in views/. app.py is the entrypoint that wires them into the top navigation.
"""

import os
import re

import streamlit as st

from cards import SAMPLE_DATA
from rules_engine import money

UNSUPPORTED_PURCHASES = (
    "Do not use this tool for EMI (instalments), international payments, gift cards, "
    "wallet top-ups, rent, education, jewellery, insurance, taxes or government payments, "
    "gaming, tolls, cash advances, railway payments, business expenses or other "
    "purchases excluded by your card issuer."
)

def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


# ---------------------------------------------------------------- device


def _user_agent():
    try:
        return st.context.headers.get("User-Agent", "") or ""
    except Exception:
        return ""


def detect_device():
    """'mobile' for phones, else 'desktop'. Tablets and laptops get the desktop layout.
    This reads the browser's User-Agent; the CSS media queries below also adapt to the
    real screen width, so a narrow window is handled even when detection says desktop."""
    ua = _user_agent()
    if re.search(r"iPhone|iPod|Windows Phone|Android.+Mobile|Mobile Safari|Mobile/", ua):
        return "mobile"
    return "desktop"


def is_mobile():
    """Use the phone layout for phones; native columns adapt to width."""
    return detect_device() == "mobile"


def grid(n, desktop=None, mobile=1, gap="small"):
    """n slots to fill in order. On desktop: columns (`desktop` may be a list of weights).
    On a phone: stacked, or `mobile` per row. Use slot[i] with `with`, or slot.markdown(...)."""
    if not is_mobile():
        return list(st.columns(desktop or n, gap=gap))
    if mobile <= 1:
        return [st.container() for _ in range(n)]
    slots = []
    for i in range(0, n, mobile):
        slots += list(st.columns(min(mobile, n - i)))
    return slots


# ---------------------------------------------------------------- state across pages
# Streamlit forgets a widget's value when its page is not shown. These two helpers copy
# the value into a plain key ("p_<key>") and restore it when the page is opened again.


def keep(key, default=None):
    """Call before creating the widget with this key."""
    if key not in st.session_state:
        saved = st.session_state.get("p_" + key)
        if saved is not None:
            st.session_state[key] = saved
        elif default is not None:
            st.session_state[key] = default


def keep_money(key, default=None):
    """Restore old whole-rupee widgets as floats before creating decimal inputs."""
    keep(key, default)
    if st.session_state.get(key) is not None:
        st.session_state[key] = money(st.session_state[key])


def remember(key):
    """Call after creating the widget with this key."""
    st.session_state["p_" + key] = st.session_state.get(key)


# ---------------------------------------------------------------- presentation
# Native Streamlit controls use .streamlit/config.toml; custom HTML inherits
# its text colour. Only the reward panel has an intentional fixed dark palette.
# No widget colour overrides, no duplicate theme toggle, no global text hacks.
CSS = """
.stApp .block-container {max-width:1240px;padding:3.75rem 2rem 2rem;}
.stApp .cca-brand {display:flex;align-items:center;gap:10px;font-size:1.2rem;font-weight:750;color:inherit;}
.stApp .cca-logo {display:grid;place-items:center;flex:none;width:32px;height:32px;border-radius:8px;background:#142C52;color:#FFDB96;font-weight:800;}
.stApp .cca-banner {border:1px solid currentColor;border-radius:10px;padding:10px 12px;}
.stApp .fin-heading {font-size:clamp(1.65rem,2.6vw,2.35rem);font-weight:750;line-height:1.18;letter-spacing:-.025em;margin:0 0 8px;color:inherit;}
.stApp .fin-copy {font-size:1rem;line-height:1.5;max-width:650px;color:inherit;}
.stApp .fin-pill {display:inline-block;padding:4px 9px;margin:2px 4px 2px 0;border-radius:8px;background:color-mix(in srgb,currentColor 9%,transparent);color:inherit;font-size:.82rem;}
.stApp .fin-step {font-size:.78rem;letter-spacing:.065em;font-weight:750;text-transform:uppercase;margin:0 0 3px;color:inherit;}
.stApp .cca-sec {margin:24px 0 4px;}
.stApp .cca-sec h2 {font-size:1.35rem;line-height:1.3;margin:0;padding:0;color:inherit;}
.stApp .cca-sec p {font-size:.95rem;line-height:1.45;margin:5px 0 0;color:inherit;}
.stApp .cca-card,.stApp .cca-explain,.stApp .cca-empty {border:1px solid color-mix(in srgb,currentColor 25%,transparent);border-radius:12px;padding:16px;color:inherit;}
.stApp .cca-card {height:100%;}
.stApp .cca-card h3,.stApp .cca-empty h3 {font-size:1.1rem;line-height:1.3;margin:0 0 6px;padding:0;color:inherit;}
.stApp .cca-card p,.stApp .cca-card li,.stApp .cca-empty p {font-size:.95rem;line-height:1.45;margin:0;color:inherit;}
.stApp .cca-card ul {padding-left:20px;margin:4px 0;}
.stApp .cca-card li {margin-bottom:4px;}
.stApp .cca-empty {text-align:center;padding:28px 18px;}
.stApp .cca-panel {background:#142C52;color:#F4F7FC;border-radius:14px;padding:20px;position:relative;overflow-wrap:anywhere;}
.stApp .cca-panel .kicker {font-size:.82rem;color:#D0DEEE;}
.stApp .cca-panel .cname {font-size:1.35rem;line-height:1.3;font-weight:750;color:#F4F7FC;margin:4px 0;}
.stApp .cca-panel .issuer {font-size:.9rem;color:#D0DEEE;}
.stApp .cca-panel .figure {font-size:2.65rem;line-height:1.1;font-weight:750;color:#FFDB96;margin:10px 0 4px;letter-spacing:-.03em;}
.stApp .cca-panel .delta {font-size:.95rem;line-height:1.45;color:#F4F7FC;}
.stApp .cca-watch {border:1px solid color-mix(in srgb,currentColor 30%,transparent);border-left:4px solid #B77916;border-radius:12px;padding:12px 14px;color:inherit;}
.stApp .cca-watch .wt {font-size:.95rem;font-weight:750;color:inherit;margin-bottom:4px;}
.stApp .cca-watch .wb,.stApp .cca-explain .txt {font-size:.95rem;line-height:1.5;color:inherit;}
.stApp .cca-explain .tag {display:block;font-size:.84rem;font-weight:750;color:inherit;margin-bottom:6px;}
.stApp .cca-explain .tag.ai {color:inherit;}
.stApp .cca-panel {margin-bottom:12px;}
.stApp .cca-dual {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-items:stretch;}
.stApp .cca-dual .cca-panel {margin-bottom:0;padding:14px;}
.stApp .cca-dual .cca-panel .cname {font-size:1.08rem;}
.stApp .cca-dual .cca-panel .figure {font-size:1.9rem;}
.stApp .cca-dual .cca-panel .delta {font-size:.85rem;margin-top:6px;}
.stApp .cca-ai-panel {background:#4B277A;color:#FFF7FF;}
.stApp .cca-ai-panel .kicker,.stApp .cca-ai-panel .issuer {color:#EEE0FF;}
.stApp .cca-ai-panel .figure {color:#FDE4A6;}
.stApp .cca-ai-panel a {color:#F2E5FF;text-decoration:underline;}
@media(max-width:1050px) {.stApp .cca-dual {grid-template-columns:1fr;}}
.stApp .cca-explain {margin:0 0 10px;}
.stApp .cca-explain .cca-condition {border-top:1px solid color-mix(in srgb,currentColor 20%,transparent);margin-top:12px;padding-top:12px;}
.stApp .cca-explain .wt {font-weight:750;font-size:.9rem;margin-bottom:4px;}
.stApp .cca-verified {font-size:.78rem;margin-top:12px;color:inherit;}
.stApp .cca-result-heading {font-size:1rem;font-weight:750;margin:8px 0 3px;}

.stApp .cca-row {display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid color-mix(in srgb,currentColor 18%,transparent);}
.stApp .cca-row:first-child {border-top:0;}
.stApp .cca-row .nm {flex:1;min-width:0;font-size:.96rem;overflow-wrap:anywhere;color:inherit;}
.stApp .cca-row .why {display:block;font-size:.85rem;color:inherit;line-height:1.4;}
.stApp .cca-row .reward-form {display:block;font-size:.80rem;color:inherit;line-height:1.35;margin-top:2px;}
.stApp .cca-row .amt {font-weight:700;font-size:1rem;color:inherit;text-align:right;max-width:38%;overflow-wrap:anywhere;}
.stApp .cca-row.best .amt {font-weight:800;}
.stApp .fin-resultbar {height:6px;background:color-mix(in srgb,currentColor 14%,transparent);border-radius:6px;overflow:hidden;margin:2px 0 5px;}
.stApp .fin-resultbar span {display:block;height:100%;border-radius:6px;background:#688FE8;}
.stApp .fin-art {position:relative;width:100%;max-width:280px;aspect-ratio:1.65;overflow:hidden;border-radius:10px;background:#F5F7FA;margin:0 auto;}
.stApp .fin-fallback {box-sizing:border-box;height:100%;padding:12px 14px;display:flex;flex-direction:column;justify-content:space-between;color:#FFFFFF;background:#142C52;font-size:13px;border-radius:12px;}
.stApp .fin-fallback strong {font-size:1rem;color:#FFFFFF;}
.stApp .fin-fallback small {font-size:.72rem;color:#FFFFFF;}
.stApp .fin-chip {display:block;width:28px;height:21px;background:#DCC495;border-radius:5px;border:1px solid #A99572;}
/* Neutral image mat preserves original product artwork in both themes. */
.stApp .fin-photo {position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#F5F7FA;padding:5px;box-sizing:border-box;}
.stApp .fin-issuer {display:flex;align-items:center;gap:7px;font-size:.82rem;font-weight:650;margin:8px 0;color:inherit;}
.stApp .fin-issuer-icon {width:20px;height:20px;object-fit:contain;border-radius:4px;background:#FFFFFF;padding:2px;box-sizing:border-box;}
.stApp .fin-library-card {display:flex;flex-direction:column;}
.stApp .fin-library-card .fin-issuer {box-sizing:border-box;min-height:36px;margin:10px 0 0;padding:0 0 9px;border-bottom:1px solid color-mix(in srgb,currentColor 18%,transparent);}
.stApp .fin-library-title {box-sizing:border-box;font-size:1.05rem;font-weight:750;line-height:1.3;min-height:3.6rem;padding:10px 0 4px;color:inherit;overflow-wrap:anywhere;}
.stApp .fin-library-label {display:block;text-transform:uppercase;font-size:.72rem;font-weight:750;letter-spacing:.035em;margin-bottom:5px;color:inherit;}
.stApp .fin-library-benefit {box-sizing:border-box;font-size:.94rem;line-height:1.45;min-height:8rem;padding:9px 0 12px;border-bottom:1px solid color-mix(in srgb,currentColor 18%,transparent);color:inherit;overflow-wrap:anywhere;}
.stApp .fin-library-meta {box-sizing:border-box;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.45fr);gap:12px;min-height:5.1rem;padding:10px 0;overflow-wrap:anywhere;}
.stApp .fin-library-meta strong {font-size:.88rem;line-height:1.35;color:inherit;}
.stApp .fin-art.has-note .fin-photo {height:calc(100% - 25px);bottom:25px;}
.stApp .fin-art-note {position:absolute;bottom:0;left:0;right:0;height:25px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;padding:2px 5px;background:#F5F7FA;color:#172B45;text-align:center;font-size:.72rem;line-height:1.2;}
.stApp .st-key-compare_workspace .cca-panel {padding:18px;}
.stApp .st-key-compare_workspace .fin-step {margin-bottom:1px;display:flex;align-items:center;gap:8px;letter-spacing:.045em;}
/* Reserve space below the result heading even when Markdown wrappers compress gaps. */
.stApp .st-key-compare_workspace .fin-step.result-step {box-sizing:border-box;min-height:38px;line-height:1.35;margin:0;padding:0 0 12px;}
.stApp .st-key-compare_workspace .fin-step.result-step .step-number {box-sizing:border-box;line-height:1;flex-shrink:0;}
.stApp .fin-step .step-number {display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:8px;flex:none;background:color-mix(in srgb,currentColor 9%,transparent);font-size:.76rem;font-weight:750;color:inherit;}
/* Explicit padding survives Streamlit's compact Markdown wrapper spacing. */
.stApp .st-key-compare_workspace .st-key-purchase_inputs .fin-step.input-step {box-sizing:border-box;line-height:1.35;margin:0;padding:0 0 10px;min-height:36px;}
.stApp .st-key-compare_workspace .st-key-purchase_inputs .fin-step.purchase-step {padding-top:12px;min-height:48px;}
.stApp .st-key-purchase_inputs {min-width:0;}
/* Compact, theme-inheriting guidance; never resize the native sidebar. */
.stApp .cca-side {font-size:.88rem;line-height:1.48;color:inherit;}
.stApp .cca-side .side-kicker {font-size:.69rem;font-weight:750;letter-spacing:.075em;text-transform:uppercase;margin:0 0 6px;color:inherit;}
.stApp .cca-side .side-title {font-size:1.12rem;font-weight:750;line-height:1.28;margin:0 0 7px;color:inherit;}
.stApp .cca-side p {font-size:.87rem;line-height:1.48;margin:0;color:inherit;}
.stApp .cca-side .side-section {border-top:1px solid color-mix(in srgb,currentColor 20%,transparent);padding-top:13px;margin-top:14px;}
.stApp .cca-side .side-label {font-size:.88rem;font-weight:750;margin:0 0 9px;color:inherit;}
.stApp .cca-side .side-step {display:grid;grid-template-columns:24px minmax(0,1fr);gap:9px;align-items:start;margin:0 0 10px;}
.stApp .cca-side .side-step:last-child {margin-bottom:0;}
.stApp .cca-side .side-num {display:grid;place-items:center;width:23px;height:23px;border:1px solid color-mix(in srgb,currentColor 25%,transparent);background:color-mix(in srgb,currentColor 7%,transparent);border-radius:7px;font-size:.73rem;font-weight:750;}
.stApp .cca-side .side-step strong {display:block;font-size:.87rem;font-weight:700;line-height:1.35;margin-bottom:2px;color:inherit;}
.stApp .cca-side .side-step span:not(.side-num) {display:block;font-size:.81rem;line-height:1.4;color:inherit;}
.stApp .cca-side .side-note {border-left:2px solid #688FE8;padding-left:9px;}
.stApp .cca-side .side-note strong {display:block;font-size:.85rem;margin-bottom:4px;color:inherit;}

.stApp .st-key-compare_workspace [data-testid="stVerticalBlock"] {gap:.5rem;}
.stApp .st-key-purchase_inputs [data-testid="stVerticalBlock"] {gap:.42rem;}
.stApp .st-key-compare_workspace .fin-heading {margin-bottom:2px;}
.stApp .cca-side .side-section {padding-top:10px;margin-top:11px;}
.stApp .cca-side .side-step {margin-bottom:7px;}
/* Keep native widget sizes and focus outlines. */
@media(min-width:761px) { .stApp .block-container {padding-top:3.25rem;} }
/* The amount retains native controls, but move overlapping instructions
   into normal layout rather than changing their colours. */
.stApp [data-testid="stNumberInput"] [data-testid="stInputInstructions"],
.stApp [data-testid="stNumberInput"] [data-testid="stWidgetInstructions"] {
    position:static!important;white-space:normal!important;overflow-wrap:anywhere;flex-shrink:1;max-width:100%;
}
@media(max-width:760px) {
    .stApp .block-container {padding:3.75rem 1rem 1.5rem;}
    .stApp .cca-panel .figure {font-size:2.2rem;}
    .stApp .cca-panel {padding:16px;}
    .stApp .fin-library-title,.stApp .fin-library-benefit,.stApp .fin-library-meta {min-height:0;}
}
"""


def header():
    """One shared header; native Settings controls light and dark mode."""
    st.markdown("<style>"+CSS+"</style>",unsafe_allow_html=True)
    st.markdown('<div class="cca-brand"><span class="cca-logo">₹</span>Card Choice Assistant</div>',unsafe_allow_html=True)
    if SAMPLE_DATA:
        st.markdown('<div class="cca-banner">Prototype · sample data only.</div>',unsafe_allow_html=True)


def page_heading(title, sub=None):
    """Common page title hierarchy."""
    import html
    body=f'<div class="fin-copy">{html.escape(sub)}</div>' if sub else ""
    st.markdown(f'<div class="fin-heading">{html.escape(title)}</div>'+body,unsafe_allow_html=True)


def sidebar():
    """Shared, collapsible guidance. No purchase inputs or new workflows."""
    with st.sidebar:
        st.markdown(
            '<div class="cca-side">'
            '<div class="side-title">About Card Choice Assistant</div>'
            '<p>Find the right card for your purchase without checking multiple apps or websites.</p>'
            '<div class="side-section"><div class="side-label">How it works</div>'
            '<div class="side-step"><span class="side-num">1</span><div>'
            '<strong>Select your cards</strong><span>Choose the cards you own.</span></div></div>'
            '<div class="side-step"><span class="side-num">2</span><div>'
            '<strong>Enter purchase details</strong><span>Enter the amount, what you are buying and how you are paying.</span></div></div>'
            '<div class="side-step"><span class="side-num">3</span><div>'
            '<strong>Compare and decide</strong><span>See estimated rewards and important conditions.</span></div></div></div>'
            '<div class="side-section"><div class="side-note"><strong>Your privacy</strong>'
            '<p>We never ask for your card number or bank login. The app keeps your selections only for this session.</p>'
            '<p style="margin-top:7px;">If you enable AI, relevant card names, purchase details and reward information are shared with Google Gemini.</p></div></div>'
            '<div class="side-section"><div class="side-label">Before you decide</div>'
            '<p>Rewards are estimates. Check eligibility and remaining cashback limits.</p></div>'
            '</div>', unsafe_allow_html=True
        )
        with st.expander("Help and limitations"):
            st.markdown("**What does AI do?**")
            st.write(
                "The app calculates the rewards. If you turn on AI, Google Gemini helps "
                "explain the result and selects a practical decision tip from checked options. "
                "AI cannot change the card recommendation. You can compare without AI, "
                "and the calculated result stays available if AI fails."
            )
            st.markdown("**What if I am unsure about eligibility or caps?**")
            st.write(
                "Choose Not sure where appropriate. An unresolved applicable "
                "reward prevents a definitive winner. Enter previously earned "
                "rewards for the relevant cycle and bucket; zero assumes an unused cap."
            )
            st.markdown("**What is excluded?**")
            st.write(
                UNSUPPORTED_PURCHASES + " The comparison assumes a supported purchase; "
                "it cannot identify instalments or international payments automatically. "
                "Fees, interest and promotional offers are not included. "
                "Restricted redemption value is not cash. Do not spend more just to earn rewards."
            )
            st.markdown("**Provider privacy**")
            st.write("The app does not save a customer wallet or purchase history. Your selections are held temporarily while you use it. Streamlit and Google Gemini have their own data-handling policies.")
            st.markdown("[Google Gemini API terms](https://ai.google.dev/gemini-api/terms)")
        st.caption("Group 07 · IIM Visakhapatnam · Academic MVP")
        st.markdown("[Source repository](https://github.com/sitanshuprusty25-06/dpm-gr07)")


def footer():
    """Keep a short disclaimer visible even when the sidebar is collapsed."""
    st.caption(
        "Independent academic decision support · Conditional estimates, not financial advice · "
        "No bank affiliation"
    )


def section(title, sub=None):
    import html
    body=f"<p>{html.escape(sub)}</p>" if sub else ""
    st.markdown(f'<div class="cca-sec"><h2>{html.escape(title)}</h2>{body}</div>',unsafe_allow_html=True)
