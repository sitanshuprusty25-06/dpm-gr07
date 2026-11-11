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
    extra = ".block-container { max-width:480px; }" if mobile else ""
    return f"""
{extra}
@media (max-width:760px) {{
  .block-container {{ padding:1rem .85rem 2rem; }}
  .cca-hero {{ padding:26px 18px; border-radius:18px; }}
  .cca-hero h1 {{ font-size:1.85rem; }}
  .cca-hero p {{ font-size:1rem; }}
  .cca-sec h2 {{ font-size:1.35rem; }}
  .cca-sec {{ margin-top:24px; }}
  .cca-panel {{ padding:18px; }}
  .cca-panel .figure {{ font-size:2.6rem; }}
  .cca-panel .cname {{ font-size:1.3rem; }}
  .cca-brand {{ font-size:1.15rem; }}
  .cca-trust span {{ font-size:.82rem; padding:5px 11px; }}
  .cca-card {{ padding:14px; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; }}
  h2 {{ font-size:1.35rem; }}
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
    """Styles for our own HTML blocks and the website layout. Always injected."""
    return f"""
:root {{ --bg:{p['bg']}; --surface:{p['surface']}; --ink:{p['ink']}; --muted:{p['muted']};
  --line:{p['line']}; --brand:{p['brand']}; --brand-ink:{p['brand_ink']}; --soft:{p['soft']};
  --panel:{p['panel']}; --panel-ink:{p['panel_ink']}; --panel-muted:{p['panel_muted']};
  --accent:{p['accent']}; --warn-bg:{p['warn_bg']}; --warn-ink:{p['warn_ink']}; --ok:{p['ok']}; }}

/* page width: a website column, not a narrow strip */
.block-container {{ max-width:1180px; padding-top:2.2rem; padding-bottom:3rem; }}

/* header */
.cca-brand {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.35rem; color:var(--ink); }}
.cca-logo {{ width:34px; height:34px; border-radius:9px; background:var(--panel); color:var(--accent);
  display:grid; place-items:center; font-size:1.05rem; }}
.cca-tag {{ font-size:.8rem; color:var(--muted); margin-top:-2px; }}
.cca-banner {{ background:var(--soft); color:var(--ink); border:1px solid var(--line); border-radius:10px;
  padding:6px 12px; font-size:.85rem; margin:6px 0 4px; }}

/* hero */
.cca-hero {{ background:var(--panel); border-radius:24px; padding:56px 48px; margin:14px 0 18px; }}
.cca-hero .kicker {{ color:var(--panel-muted); font-size:.9rem; letter-spacing:.04em; text-transform:uppercase; }}
.cca-hero h1 {{ color:var(--panel-ink); font-size:3rem; line-height:1.1; margin:10px 0 14px; padding:0; max-width:760px; }}
.cca-hero p {{ color:var(--panel-muted); font-size:1.15rem; max-width:640px; margin:0; }}
.cca-hero em {{ color:var(--accent); font-style:normal; }}

/* sections */
.cca-sec {{ margin:34px 0 6px; }}
.cca-sec h2 {{ margin:0; padding:0; color:var(--ink); font-size:1.7rem; }}
.cca-sec p {{ color:var(--muted); margin:4px 0 0; }}
.cca-trust {{ display:flex; flex-wrap:wrap; gap:10px; margin:6px 0 4px; }}
.cca-trust span {{ border:1px solid var(--line); background:var(--surface); color:var(--ink);
  border-radius:999px; padding:6px 14px; font-size:.9rem; }}
.cca-card {{ background:var(--surface); border:1.5px solid var(--line); border-radius:16px; padding:18px 18px 16px;
  height:100%; color:var(--ink); }}
.cca-card h3 {{ margin:0 0 6px; padding:0; font-size:1.1rem; color:var(--ink); }}
.cca-card p, .cca-card li {{ color:var(--muted); font-size:.95rem; margin:0; }}
.cca-card ul {{ margin:6px 0 0; padding-left:18px; }}
.cca-num {{ display:inline-grid; place-items:center; width:30px; height:30px; border-radius:50%;
  background:var(--brand); color:var(--brand-ink); font-weight:700; margin-bottom:8px; }}
.cca-chiprow {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
.cca-swatch {{ width:46px; height:30px; border-radius:6px; flex:none; box-shadow:inset 0 0 0 1px rgba(255,255,255,.25); }}
.cca-cn {{ font-weight:700; color:var(--ink); }}
.cca-cs {{ font-size:.82rem; color:var(--muted); }}
.cca-soon {{ display:inline-block; font-size:.72rem; border:1px solid var(--line); border-radius:6px;
  padding:1px 6px; color:var(--muted); margin-left:6px; }}
.cca-empty {{ border:1.5px dashed var(--line); border-radius:16px; padding:40px 20px; text-align:center;
  color:var(--muted); }}

/* result */
.cca-panel {{ background:var(--panel); border-radius:20px; padding:22px; position:relative; }}
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
.cca-explain {{ border:1.5px solid var(--line); border-radius:14px; padding:14px; margin-top:12px; background:var(--surface); }}
.cca-explain .tag {{ display:inline-block; font-size:.75rem; border-radius:999px; padding:2px 9px;
  background:var(--soft); color:var(--muted); margin-bottom:6px; }}
.cca-explain .tag.ai {{ background:var(--ok); color:var(--surface); }}
.cca-explain .txt {{ color:var(--ink); }}
.cca-row {{ display:flex; align-items:center; gap:10px; padding:10px 0; border-top:1px solid var(--line); }}
.cca-row:first-child {{ border-top:0; }}
.cca-row .dot {{ flex:none; width:12px; height:12px; border-radius:50%; }}
.cca-row .nm {{ flex:1; min-width:0; color:var(--ink); }}
.cca-row .nm b {{ font-weight:650; }}
.cca-row .why {{ display:block; font-size:.8rem; color:var(--muted); }}
.cca-row .amt {{ font-weight:700; font-size:1.05rem; color:var(--ink); }}
.cca-row.best .amt {{ color:var(--ok); }}

/* footer */
.cca-foot-brand {{ font-weight:800; font-size:1.1rem; color:var(--ink); }}
.cca-foot-text {{ color:var(--muted); font-size:.88rem; }}
.cca-foot-h {{ font-weight:700; color:var(--ink); margin-bottom:4px; }}
.cca-foot-dead {{ color:var(--muted); font-size:.9rem; padding:2px 0; opacity:.8; }}
@media (max-width:800px) {{ .cca-hero {{ padding:34px 22px; }} .cca-hero h1 {{ font-size:2.1rem; }} }}
"""


def streamlit_override_css(p):
    """Re-colours Streamlit's own widgets. Injected only when Light or Dark is forced, so
    the page is consistent whatever theme Streamlit itself is using."""
    return f"""
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background:{p['bg']}; color:{p['ink']}; }}
[data-testid="stHeader"] {{ background:{p['bg']}; }}
[data-testid="stHeader"] a, [data-testid="stHeader"] button, [data-testid="stHeader"] span {{ color:{p['ink']}; }}
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
[data-testid="stPageLink"] a {{ color:{p['ink']}; }}
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
    css = custom_css(palette) + responsive_css(mobile)
    if st.session_state["theme"] != "Auto":
        css += streamlit_override_css(palette)
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
