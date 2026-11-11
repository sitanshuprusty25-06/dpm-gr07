"""GenAI Card Choice Assistant: V1 (Group 07, DPM, IIM Visakhapatnam).

Website entrypoint: wide layout, top navigation, shared header and footer.
Pages live in views/. Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Card Choice Assistant",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import ui  # noqa: E402  (must come after set_page_config)

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/compare.py", title="Compare my cards", icon="💳", url_path="compare"),
    st.Page("views/supported_cards.py", title="Supported cards", icon="📇", url_path="cards"),
    st.Page("views/how_it_works.py", title="How it works", icon="⚙️", url_path="how-it-works"),
    st.Page("views/roadmap.py", title="Roadmap", icon="🗺️", url_path="roadmap"),
    st.Page("views/faq.py", title="FAQ", icon="❓", url_path="faq"),
    st.Page("views/about.py", title="About & contact", icon="👥", url_path="about"),
]

ui.header()
st.navigation(pages, position="top").run()
ui.footer()
