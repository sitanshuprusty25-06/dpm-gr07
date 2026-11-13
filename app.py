"""Card Choice Assistant — Group 07, DPM, IIM Visakhapatnam.

The MVP opens directly into the purchase decision. The only secondary
page is the reference catalogue. Run with: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Card Choice Assistant",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto",
)

import ui  # noqa: E402

pages = [
    st.Page("views/compare.py", title="Compare my cards", default=True),
    st.Page("views/supported_cards.py", title="Supported cards", url_path="cards"),
]

ui.header()
ui.sidebar()
st.navigation(pages, position="top").run()
