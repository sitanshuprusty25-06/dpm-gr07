"""Shared look-and-feel for the Card Choice Assistant website: theme, CSS, header, footer.

Pages live in views/. app.py is the entrypoint that wires them into the top navigation.
"""

import os
import re

import streamlit as st

from cards import SAMPLE_DATA

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
    """Honours the footer's 'View as' switch (Auto / Mobile / Desktop)."""
    choice = st.session_state.get("layout", "Auto")
    if choice == "Mobile":
        return True
    if choice == "Desktop":
        return False
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


def responsive_css(mobile):
    """Phone and narrow-screen rules. Always applied for narrow screens via media queries;
    the max-width rule gives a phone-like column when 'Mobile' is chosen on a big screen."""
    extra = ".stApp .block-container { max-width:480px; }" if mobile else ""
    return f"""
{extra}
@media (max-width:760px) {{
  .stApp .block-container {{ padding:4.25rem .85rem 2rem; }}
  .stApp .cca-hero {{ padding:26px 18px; border-radius:18px; }}
  .stApp .cca-hero h1 {{ font-size:1.85rem; }}
  .stApp .cca-hero p {{ font-size:1rem; }}
  .stApp .cca-sec h2 {{ font-size:1.35rem; }}
  .stApp .cca-sec {{ margin-top:24px; }}
  .stApp .cca-panel {{ padding:18px; }}
  .stApp .cca-panel .figure {{ font-size:2.6rem; }}
  .stApp .cca-panel .cname {{ font-size:1.3rem; }}
  .stApp .cca-brand {{ font-size:1.15rem; }}
  .stApp .cca-trust span {{ font-size:.85rem; padding:5px 11px; }}
  .stApp .cca-card {{ padding:14px; }}
  .stApp h2 {{ font-size:1.35rem; }}
}}
"""


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


# ---------------------------------------------------------------- theme


def effective_theme(choice):
    """Auto follows the Streamlit theme (Settings menu / device); otherwise the user's pick."""
    if choice == "Light":
        return "light"
    if choice == "Dark":
        return "dark"
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def custom_css(p):
    """Styles for our own HTML blocks and the website layout. Always injected.
    Every rule is prefixed with .stApp so it outranks the generic text-colour rules in
    streamlit_override_css (this is what keeps text on the dark hero and result panels light)."""
    return f"""
:root {{ --bg:{p['bg']}; --surface:{p['surface']}; --ink:{p['ink']}; --muted:{p['muted']};
  --line:{p['line']}; --brand:{p['brand']}; --brand-ink:{p['brand_ink']}; --soft:{p['soft']};
  --panel:{p['panel']}; --panel-ink:{p['panel_ink']}; --panel-muted:{p['panel_muted']};
  --accent:{p['accent']}; --warn-bg:{p['warn_bg']}; --warn-ink:{p['warn_ink']}; --ok:{p['ok']}; }}

/* page width: use the screen, and clear Streamlit's fixed top bar */
.stApp .block-container {{ max-width:min(1560px, 96vw); padding:4.5rem 2.5rem 3rem; }}

/* header */
.stApp .cca-brand {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.4rem; color:var(--ink); }}
.stApp .cca-logo {{ width:36px; height:36px; border-radius:9px; background:var(--panel); color:var(--accent);
  display:grid; place-items:center; font-size:1.1rem; }}
.stApp .cca-tag {{ font-size:.88rem; color:var(--muted); margin-top:-2px; }}
.stApp .cca-banner {{ background:var(--soft); color:var(--ink); border:1px solid var(--line); border-radius:10px;
  padding:7px 14px; font-size:.9rem; margin:6px 0 4px; }}

/* hero */
.stApp .cca-hero {{ background:var(--panel); border-radius:24px; padding:48px 44px; margin:14px 0 14px; }}
.stApp .cca-hero .kicker {{ color:var(--panel-muted); font-size:.9rem; letter-spacing:.04em; text-transform:uppercase; }}
.stApp .cca-hero h1 {{ color:var(--panel-ink); font-size:3.1rem; line-height:1.1; margin:10px 0 16px; padding:0; }}
.stApp .cca-hero p {{ color:var(--panel-muted); font-size:1.2rem; line-height:1.55; margin:0; }}
.stApp .cca-hero em {{ color:var(--accent); font-style:normal; }}

/* sections */
.stApp .cca-sec {{ margin:36px 0 8px; }}
.stApp .cca-sec h2 {{ margin:0; padding:0; color:var(--ink); font-size:1.8rem; }}
.stApp .cca-sec p {{ color:var(--muted); font-size:1.02rem; margin:4px 0 0; }}
.stApp .cca-trust {{ display:flex; flex-wrap:wrap; gap:10px; margin:6px 0 4px; }}
.stApp .cca-trust span {{ border:1px solid var(--line); background:var(--surface); color:var(--ink);
  border-radius:999px; padding:7px 16px; font-size:.95rem; }}
.stApp .cca-card {{ background:var(--surface); border:1.5px solid var(--line); border-radius:16px; padding:20px 20px 18px;
  height:100%; color:var(--ink); }}
.stApp .cca-card h3 {{ margin:0 0 8px; padding:0; font-size:1.2rem; color:var(--ink); }}
.stApp .cca-card p, .stApp .cca-card li {{ color:var(--muted); font-size:1.02rem; line-height:1.5; margin:0; }}
.stApp .cca-card ul {{ margin:6px 0 0; padding-left:20px; }}
.stApp .cca-card li {{ margin-bottom:3px; }}
.stApp .cca-num {{ display:inline-grid; place-items:center; width:32px; height:32px; border-radius:50%;
  background:var(--brand); color:var(--brand-ink); font-weight:700; margin-bottom:8px; }}
.stApp .cca-chiprow {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
.stApp .cca-swatch {{ width:46px; height:30px; border-radius:6px; flex:none; box-shadow:inset 0 0 0 1px rgba(255,255,255,.25); }}
.stApp .cca-cn {{ font-weight:700; font-size:1.05rem; color:var(--ink); }}
.stApp .cca-cs {{ font-size:.9rem; color:var(--muted); }}
.stApp .cca-empty {{ border:1.5px dashed var(--line); border-radius:16px; padding:48px 20px; text-align:center;
  color:var(--muted); font-size:1.02rem; }}

/* result */
.stApp .cca-panel {{ background:var(--panel); border-radius:20px; padding:24px; position:relative; }}
.stApp .cca-panel .kicker {{ font-size:.9rem; color:var(--panel-muted); }}
.stApp .cca-panel .cname {{ font-size:1.6rem; font-weight:700; color:var(--panel-ink); margin-top:2px; }}
.stApp .cca-panel .issuer {{ font-size:.95rem; color:var(--panel-muted); }}
.stApp .cca-panel .figure {{ font-size:3.4rem; line-height:1.05; font-weight:700; color:var(--accent); margin:14px 0 4px; }}
.stApp .cca-panel .delta {{ font-size:1rem; color:var(--panel-ink); }}
.stApp .cca-panel .swatch {{ position:absolute; right:18px; top:18px; width:54px; height:36px; border-radius:7px;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.3); }}
.stApp .cca-watch {{ background:var(--warn-bg); border-radius:14px; padding:14px 16px; margin-top:12px; }}
.stApp .cca-watch .wt {{ font-weight:700; color:var(--warn-ink); }}
.stApp .cca-watch .wb {{ color:var(--warn-ink); font-size:1.02rem; line-height:1.5; }}
.stApp .cca-explain {{ border:1.5px solid var(--line); border-radius:14px; padding:16px; margin-top:12px; background:var(--surface); }}
.stApp .cca-explain .tag {{ display:inline-block; font-size:.8rem; border-radius:999px; padding:2px 10px;
  background:var(--soft); color:var(--muted); margin-bottom:6px; }}
.stApp .cca-explain .tag.ai {{ background:var(--ok); color:var(--surface); }}
.stApp .cca-explain .txt {{ color:var(--ink); font-size:1.02rem; line-height:1.55; }}
.stApp .cca-row {{ display:flex; align-items:center; gap:12px; padding:11px 0; border-top:1px solid var(--line); }}
.stApp .cca-row:first-child {{ border-top:0; }}
.stApp .cca-row .dot {{ flex:none; width:12px; height:12px; border-radius:50%; }}
.stApp .cca-row .nm {{ flex:1; min-width:0; color:var(--ink); font-size:1.02rem; }}
.stApp .cca-row .nm b {{ font-weight:650; }}
.stApp .cca-row .why {{ display:block; font-size:.88rem; color:var(--muted); }}
.stApp .cca-row .amt {{ font-weight:700; font-size:1.1rem; color:var(--ink); }}
.stApp .cca-row.best .amt {{ color:var(--ok); }}

/* footer */
.stApp .cca-foot-brand {{ font-weight:800; font-size:1.15rem; color:var(--ink); }}
.stApp .cca-foot-text {{ color:var(--muted); font-size:.95rem; }}
.stApp .cca-foot-h {{ font-weight:700; color:var(--ink); margin-bottom:4px; }}
.stApp .cca-foot-dead {{ color:var(--muted); font-size:.95rem; padding:2px 0; }}
"""


def streamlit_override_css(p):
    """Re-colours Streamlit's own widgets and plain text with the chosen palette. Applied in
    every mode (Auto uses the device's light or dark), so the whole page is consistent.
    Selectors here are deliberately plain, so the more specific .stApp .cca-* rules win."""
    return f"""
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{p['bg']}; color:{p['ink']}; }}
[data-testid="stHeader"] {{ background:{p['bg']}; }}
[data-testid="stHeader"] a, [data-testid="stHeader"] button, [data-testid="stHeader"] span {{ color:{p['ink']}; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stWidgetLabel"] p, .stApp label {{ color:{p['ink']}; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color:{p['muted']}; }}
.stApp input, .stApp textarea {{ background:{p['surface']}; color:{p['ink']}; }}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
[data-testid="stNumberInputContainer"] {{ background:{p['surface']}; border-color:{p['line']}; }}
[data-baseweb="select"] div, [data-baseweb="select"] span {{ color:{p['ink']}; }}
[data-testid="stNumberInputContainer"] button {{ background:{p['soft']}; color:{p['ink']}; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {{ background:{p['surface']}; color:{p['ink']}; }}
.stButton > button, .stLinkButton > a {{ background:{p['surface']}; border:1px solid {p['line']}; }}
.stButton > button p, .stLinkButton > a p {{ color:{p['ink']}; }}
.stButton > button[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {{
  background:{p['brand']}; border-color:{p['brand']}; }}
.stButton > button[data-testid="stBaseButton-primary"] p, .stButton > button[kind="primary"] p {{ color:{p['brand_ink']}; }}
.stButton > button:disabled {{ opacity:1; }}
.stButton > button:disabled p {{ color:{p['muted']}; }}
[data-testid="stPageLink"] a, [data-testid="stPageLink"] p {{ color:{p['ink']}; }}
[data-baseweb="tab"] {{ color:{p['muted']}; }}
[data-baseweb="tab"][aria-selected="true"] {{ color:{p['ink']}; }}
[data-testid="stExpander"] details {{ background:{p['surface']}; border-color:{p['line']}; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:{p['line']}; }}
[data-testid="stAlert"] {{ background:{p['soft']}; color:{p['ink']}; }}
"""


# ---------------------------------------------------------------- chrome


def header():
    """Brand, theme switch and a placeholder sign-in. Runs on every page."""
    st.session_state.setdefault("theme", "Auto")
    mobile = is_mobile()

    brand = (
        '<div class="cca-brand"><span class="cca-logo">₹</span>Card Choice Assistant</div>'
        '<div class="cca-tag">Pick the right card before you pay</div>'
    )
    theme_help = "Auto follows your device or the Streamlit Settings menu."
    if mobile:
        st.markdown(brand, unsafe_allow_html=True)
        theme_col, signin_col = st.columns([3, 2], vertical_alignment="center")
        with theme_col:
            st.radio("Theme", ["Auto", "Light", "Dark"], horizontal=True, key="theme", help=theme_help)
        with signin_col:
            st.button("Sign in · soon", disabled=True, use_container_width=True,
                      help="Accounts are not part of the first version.")
    else:
        left, mid, right = st.columns([5, 3, 2], vertical_alignment="center")
        with left:
            st.markdown(brand, unsafe_allow_html=True)
        with mid:
            st.radio("Theme", ["Auto", "Light", "Dark"], horizontal=True, key="theme", help=theme_help)
        with right:
            st.button("Sign in · coming soon", disabled=True, use_container_width=True,
                      help="Accounts are not part of the first version.")

    palette = PALETTES[effective_theme(st.session_state["theme"])]
    css = streamlit_override_css(palette) + custom_css(palette) + responsive_css(mobile)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    if SAMPLE_DATA:
        st.markdown(
            '<div class="cca-banner"><b>Prototype · sample data.</b> Card names, banks and terms '
            "shown here are fictional and for demonstration only.</div>",
            unsafe_allow_html=True,
        )


def footer():
    """Website footer with real pages and a few honest placeholders. Runs on every page."""
    st.divider()
    mobile = is_mobile()
    if mobile:
        c1 = st.container()
        c4 = None
        c2, c3 = st.columns(2)
    else:
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    with c1:
        st.markdown(
            '<div class="cca-foot-brand">Card Choice Assistant</div>'
            '<div class="cca-foot-text">A GenAI-assisted check that tells you which of your own '
            "credit cards gives the most benefit on a purchase, and why.</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="cca-foot-h">Product</div>', unsafe_allow_html=True)
        st.page_link("views/compare.py", label="Compare my cards")
        st.page_link("views/supported_cards.py", label="Supported cards")
        st.page_link("views/how_it_works.py", label="How it works")
    with c3:
        st.markdown('<div class="cca-foot-h">Company</div>', unsafe_allow_html=True)
        st.page_link("views/about.py", label="About & contact")
        st.page_link("views/roadmap.py", label="Roadmap")
        st.page_link("views/faq.py", label="FAQ")
    later = (
        '<div class="cca-foot-h">Coming later</div>'
        '<div class="cca-foot-dead">Blog</div>'
        '<div class="cca-foot-dead">Privacy policy</div>'
        '<div class="cca-foot-dead">Terms of use</div>'
    )
    if c4 is not None:
        with c4:
            st.markdown(later, unsafe_allow_html=True)
    else:
        st.markdown(later, unsafe_allow_html=True)

    st.caption(
        "Group 07 · Digital Product Management · IIM Visakhapatnam. Results are estimates for the "
        "supported cards and dated rules, not a guarantee of reward. Nothing you enter is stored."
    )
    st.session_state.setdefault("layout", "Auto")
    st.radio(
        "View as", ["Auto", "Mobile", "Desktop"], horizontal=True, key="layout",
        help="Auto picks the layout for the device you are using. Choose Mobile to preview the phone layout.",
    )


def section(title, sub=None):
    """A section heading in the website style."""
    html_sub = f"<p>{sub}</p>" if sub else ""
    st.markdown(f'<div class="cca-sec"><h2>{title}</h2>{html_sub}</div>', unsafe_allow_html=True)
