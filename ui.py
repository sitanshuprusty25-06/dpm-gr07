"""Shared look-and-feel for the Card Choice Assistant website: theme, CSS, header, footer.

Pages live in views/. app.py is the entrypoint that wires them into the top navigation.
"""

import os
import re

import streamlit as st

from cards import SAMPLE_DATA

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
.stApp .cca-explain {margin:0 0 10px;}
.stApp .cca-explain .cca-condition {border-top:1px solid color-mix(in srgb,currentColor 20%,transparent);margin-top:12px;padding-top:12px;}
.stApp .cca-explain .wt {font-weight:750;font-size:.9rem;margin-bottom:4px;}
.stApp .cca-verified {font-size:.78rem;margin-top:12px;color:inherit;}
.stApp .cca-result-heading {font-size:1rem;font-weight:750;margin:8px 0 3px;}

.stApp .cca-row {display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid color-mix(in srgb,currentColor 18%,transparent);}
.stApp .cca-row:first-child {border-top:0;}
.stApp .cca-row .nm {flex:1;min-width:0;font-size:.96rem;overflow-wrap:anywhere;color:inherit;}
.stApp .cca-row .why {display:block;font-size:.85rem;color:inherit;line-height:1.4;}
.stApp .cca-row .amt {font-weight:700;font-size:1rem;color:inherit;text-align:right;max-width:38%;overflow-wrap:anywhere;}
.stApp .cca-row.best .amt {font-weight:800;}
.stApp .fin-resultbar {height:6px;background:color-mix(in srgb,currentColor 14%,transparent);border-radius:6px;overflow:hidden;margin:2px 0 5px;}
.stApp .fin-resultbar span {display:block;height:100%;border-radius:6px;background:#688FE8;}
.stApp .fin-art {position:relative;width:100%;max-width:300px;aspect-ratio:1.65;overflow:hidden;border-radius:12px;background:#F5F7FA;margin:0 auto;}
.stApp .fin-fallback {box-sizing:border-box;height:100%;padding:12px 14px;display:flex;flex-direction:column;justify-content:space-between;color:#FFFFFF;background:#142C52;font-size:13px;border-radius:12px;}
.stApp .fin-fallback strong {font-size:1rem;color:#FFFFFF;}
.stApp .fin-fallback small {font-size:.72rem;color:#FFFFFF;}
.stApp .fin-chip {display:block;width:28px;height:21px;background:#DCC495;border-radius:5px;border:1px solid #A99572;}
/* Neutral image mat preserves original product artwork in both themes. */
.stApp .fin-photo {position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#F5F7FA;padding:5px;box-sizing:border-box;}
.stApp .fin-issuer {display:flex;align-items:center;gap:7px;font-size:.82rem;font-weight:650;margin:8px 0;color:inherit;}
.stApp .fin-issuer-icon {width:20px;height:20px;object-fit:contain;border-radius:4px;background:#FFFFFF;padding:2px;box-sizing:border-box;}
.stApp .fin-library-card {display:flex;flex-direction:column;}
.stApp .fin-library-card .fin-issuer {min-height:32px;margin:8px 0 0;padding:0 0 9px;border-bottom:1px solid color-mix(in srgb,currentColor 18%,transparent);}
.stApp .fin-library-title {font-size:1.05rem;font-weight:750;line-height:1.3;min-height:3.2rem;padding:10px 0 4px;color:inherit;}
.stApp .fin-library-label {display:block;text-transform:uppercase;font-size:.72rem;font-weight:750;letter-spacing:.035em;margin-bottom:5px;color:inherit;}
.stApp .fin-library-benefit {font-size:.94rem;line-height:1.45;min-height:6.25rem;padding:9px 0 12px;border-bottom:1px solid color-mix(in srgb,currentColor 18%,transparent);color:inherit;}
.stApp .fin-library-meta {display:grid;grid-template-columns:1fr 1.45fr;gap:12px;min-height:4.4rem;padding:10px 0;}
.stApp .fin-library-meta strong {font-size:.88rem;line-height:1.35;color:inherit;}
.stApp .fin-art-note {text-align:center;font-size:.75rem;line-height:1.35;margin-top:4px;color:inherit;}
.stApp .st-key-compare_workspace .cca-panel {padding:18px;}
.stApp .st-key-compare_workspace .fin-step {margin-bottom:1px;}
.stApp .st-key-compare_workspace [data-testid="stVerticalBlock"] {gap:.65rem;}
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


def footer():
    """Shared, secondary help; do not interrupt the purchase decision."""
    st.divider()
    with st.expander("How it works"):
        st.markdown(
            "1. Select the exact cards you own and enter one purchase.\n"
            "2. Confirm the payment route and adjust previously earned rewards if needed.\n"
            "3. Compare the estimated benefits, explanation and issuer conditions."
        )
        st.write(
            "The rules engine calculates eligibility, rates and caps. Optional Gemini "
            "assistance selects a relevant approved reason and caution; it cannot change "
            "the calculation or ranking. If AI fails, the rules-based result remains."
        )
    with st.expander("Help, privacy and limitations"):
        st.markdown("**What can I compare?**")
        st.write(
            "One supported domestic, non-EMI credit-card purchase. Fees, interest and "
            "unmodeled promotions are excluded. Rewards are conditional estimates, "
            "not guaranteed savings. Restricted redemption value is not the same as cash."
        )
        st.markdown("**What if I am unsure about eligibility or caps?**")
        st.write(
            "Choose Not sure where appropriate. An unresolved applicable reward prevents "
            "a definitive winner. Enter previous rewards for the relevant cycle and bucket; "
            "zero assumes an unused cap. Check the official issuer terms in the result "
            "or Supported cards."
        )
        st.markdown("**What happens to my data?**")
        st.write(
            "No card number, bank login or account is required. The app has no persistent "
            "user wallet; inputs stay in temporary session state. With AI enabled, computed "
            "purchase facts and relevant card names are sent to Google Gemini on eligible "
            "comparisons. Switch AI off for rules-only comparison. Hosting and AI providers "
            "have their own data-handling policies."
        )
        st.markdown("[Google Gemini API terms](https://ai.google.dev/gemini-api/terms)")
        st.caption(
            "Independent academic decision support, not financial advice or a bank-endorsed "
            "service. Do not spend more just to earn rewards."
        )
    st.caption("Group 07 · Digital Product Management · IIM Visakhapatnam · Academic MVP")
    st.markdown("[Source repository](https://github.com/sitanshuprusty25-06/dpm-gr07)")


def section(title, sub=None):
    import html
    body=f"<p>{html.escape(sub)}</p>" if sub else ""
    st.markdown(f'<div class="cca-sec"><h2>{html.escape(title)}</h2>{body}</div>',unsafe_allow_html=True)
