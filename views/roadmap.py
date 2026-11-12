"""Roadmap: what V1 does, and what is deliberately left for later releases."""

import streamlit as st

from ui import grid, section

st.markdown("## Roadmap")
st.caption("V1 is deliberately small: one user, one problem, one workflow, one AI capability.")

section("Now: V1 (this version)")
st.markdown(
    '<div class="cca-card"><ul>'
    "<li>Choose your cards from a hand-checked list</li>"
    "<li>Enter a purchase amount, category and payment context</li>"
    "<li>Conditional rupee estimates, ranked only when the applicable reward is established</li>"
    "<li>Optional AI selection of approved reasons and cautions, with six grounding checks</li>"
    "</ul></div>",
    unsafe_allow_html=True,
)

section("Later", "Not built yet. Shown so you can see where the product is heading.")
c1, c2, c3 = grid(3)
later = [
    ("Release 2 · Better data",
     ["More cards, each verified against issuer terms", "“Report wrong info” review workflow",
      "Net benefit after annual fees"]),
    ("Release 3 · Remember me",
     ["Sign in and a saved wallet", "Monthly cap tracking from purchases you confirm",
      "Reminders before a cap runs out"]),
    ("Release 4 · At the moment of payment",
     ["Browser extension on checkout pages", "Partner integrations", "Optional bank or transaction linking"]),
]
for col, (title, items) in zip((c1, c2, c3), later):
    col.markdown(
        f'<div class="cca-card"><h3>{title}</h3><ul>{"".join(f"<li>{i}</li>" for i in items)}</ul></div>',
        unsafe_allow_html=True,
    )

st.caption("Release contents are hypotheses, not commitments. Improve coverage only after verifying issuer rules; consider saved wallets or integrations only if user evidence supports them and privacy safeguards are feasible.")
