"""Compare my cards: the product itself.

Desktop: inputs on the left, result on the right.
Phone: one column, with the result below the inputs.
"""

import streamlit as st

from cards import CARDS, CATEGORIES, DEFAULT_WALLET
from results import render_result
from rules_engine import category_label, highlight, inr, rank
from ui import is_mobile, keep, remember

cat_ids = [cid for cid, _ in CATEGORIES]

# Bring back choices made earlier (Streamlit forgets widgets of pages that are not shown).
for c in CARDS:
    keep(f"w_{c['id']}", c["id"] in DEFAULT_WALLET)
keep("amount")
keep("cat", "travel")


def pick_example(amount, cat):
    st.session_state["amount"] = amount
    st.session_state["cat"] = cat
    st.session_state["run"] = True


mobile = is_mobile()

st.markdown("## Compare my cards")
st.caption("Pick the cards you hold, enter the purchase, and see which one gives the most benefit.")

if mobile:
    left = st.container()
    right = st.container()
else:
    left, right = st.columns([1, 1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("**1. Which cards do you hold?**")
        st.caption("We never ask for card numbers, expiry or CVV. Only the cards listed here are compared.")
        cols = None if mobile else st.columns(2)
        for i, c in enumerate(CARDS):
            with (st.container() if mobile else cols[i % 2]):
                st.checkbox(f"{c['chip']} **{c['name']}**", key=f"w_{c['id']}")
                st.caption(f"{c['issuer']} · {highlight(c)}")
            remember(f"w_{c['id']}")
        selected = [c for c in CARDS if st.session_state.get(f"w_{c['id']}")]
        if selected:
            st.caption(f"{len(selected)} card{'s' if len(selected) > 1 else ''} selected.")
        else:
            st.warning("Select at least one card.")

    with st.container(border=True):
        st.markdown("**2. What are you buying?**")
        st.caption("Try an example")
        ex_cols = st.columns(2)
        examples = [("₹8,000 travel", 8000, "travel"), ("₹12,000 online", 12000, "shopping"),
                    ("₹800 dining", 800, "dining"), ("₹3,000 fuel", 3000, "fuel")]
        for i, (lbl, amt, ex_cat) in enumerate(examples):
            ex_cols[i % len(ex_cols)].button(
                lbl, key=f"ex_{amt}_{ex_cat}", on_click=pick_example,
                args=(amt, ex_cat), use_container_width=True,
            )

        st.number_input("Amount (₹)", min_value=0, step=100, value=None, format="%d",
                        key="amount", placeholder="e.g. 8000")
        if mobile:
            st.selectbox("Category", cat_ids, format_func=category_label, key="cat")
        else:
            st.radio("Category", cat_ids, format_func=category_label, horizontal=True, key="cat")
        remember("amount")
        remember("cat")

        # Optional: bonus already used this month, only for cards that have a capped bonus here.
        capped = [c for c in selected if c["rules"].get(st.session_state["cat"], {}).get("cap")]
        used_by_card = {}
        if capped:
            with st.expander("Optional: bonus already used this month"):
                st.caption("The app does not track your spending. Leave these at 0 and it assumes each monthly cap is unused.")
                for c in capped:
                    cap = c["rules"][st.session_state["cat"]]["cap"]
                    used_by_card[c["id"]] = st.number_input(
                        f"{c['name']}: bonus already earned this month (₹, cap {inr(cap)})",
                        min_value=0, max_value=int(cap), step=50, value=0, format="%d",
                        key=f"used_{c['id']}_{st.session_state['cat']}",
                    )

        go = st.button("Find my best card", type="primary", use_container_width=True)

    run = go or st.session_state.pop("run", False)
    error = None
    if run:
        amount = st.session_state.get("amount")
        cat = st.session_state["cat"]
        if not amount or amount <= 0:
            error = "Enter the purchase amount in rupees, for example 8000."
        elif amount > 10000000:
            error = "That amount is above the limit this app handles (₹1,00,00,000)."
        elif not selected:
            error = "Add at least one card to get a recommendation."
        if error:
            st.session_state.pop("last", None)
        else:
            ranked = rank(selected, cat, amount, used_by_card)
            st.session_state["last"] = {
                "ranked": ranked, "win": ranked[0],
                "second": ranked[1] if len(ranked) > 1 else None,
                "amount": amount, "cat": cat, "ai_text": None, "ai_status": None,
            }

with right:
    if error:
        st.error(error)
    if st.session_state.get("last"):
        render_result(st.session_state["last"])
    elif not error:
        st.markdown(
            '<div class="cca-empty"><b>Your recommendation will appear here.</b><br>'
            "Choose your cards, enter an amount and a category, then press “Find my best card”.</div>",
            unsafe_allow_html=True,
        )
