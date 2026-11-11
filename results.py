"""Result components shared by the Home and Compare pages."""

import html

import streamlit as st

from explain import ai_reword
from rules_engine import category_label, inr, key_condition, template_explain
from ui import get_secret


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
    return "".join(rows)


def panel_html(win, second, amount, cat):
    """The dark 'Use this card' panel (or the 'no rewards' panel)."""
    if win.benefit <= 0.005:
        return (
            '<div class="cca-panel"><div class="kicker">No bonus on this purchase</div>'
            '<div class="cname">None of your cards earn rewards here</div>'
            '<div class="delta" style="margin-top:10px;color:var(--panel-muted)">'
            "Pay with whichever card is most convenient. Reasons are listed below.</div></div>"
        )
    if second and win.benefit - second.benefit > 0.005:
        delta = f"{inr(win.benefit - second.benefit)} more than {html.escape(second.card['name'])}"
    elif second:
        delta = f"Same as {html.escape(second.card['name'])}; lower annual fee wins"
    else:
        delta = "Add a second card to compare"
    return (
        f'<div class="cca-panel"><span class="swatch" style="background:{win.card["hue"]}"></span>'
        '<div class="kicker">Use this card</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated benefit on this {inr(amount)} '
        f'{category_label(cat).lower()} purchase</div>'
        f'<div class="delta">{delta}</div></div>'
    )


def watch_html(win):
    return (
        '<div class="cca-watch"><div class="wt">Watch out</div>'
        f'<div class="wb">{html.escape(key_condition(win))}</div></div>'
    )


def explain_html(text, ai):
    tag, cls = ("AI wording · numbers verified", "tag ai") if ai else ("Rule-based explanation", "tag")
    return (
        f'<div class="cca-explain"><span class="{cls}">{tag}</span>'
        f'<div class="txt">{html.escape(text)}</div></div>'
    )


def render_result(L):
    """Full result for the Compare page: panel, watch-out, explanation (+AI button), all cards."""
    win, second, ranked, amount, cat = L["win"], L["second"], L["ranked"], L["amount"], L["cat"]
    st.markdown(panel_html(win, second, amount, cat), unsafe_allow_html=True)

    if win.benefit <= 0.005:
        st.markdown("**All your cards**")
        st.markdown(others_html(ranked, False), unsafe_allow_html=True)
        return

    st.markdown(watch_html(win), unsafe_allow_html=True)

    box = st.empty()

    def draw_explanation():
        if L.get("ai_text"):
            box.markdown(explain_html(L["ai_text"], True), unsafe_allow_html=True)
        else:
            box.markdown(
                explain_html(template_explain(win, second, amount, cat), False),
                unsafe_allow_html=True,
            )

    draw_explanation()
    if st.button("Reword with AI", key="ai_btn"):
        with st.spinner("Rewording..."):
            text, status, detail = ai_reword(
                win, second, amount, cat,
                api_key=get_secret("GEMINI_API_KEY"),
                model=get_secret("GEMINI_MODEL", "gemini-2.5-flash"),
            )
        L["ai_text"], L["ai_status"], L["ai_detail"] = text, status, detail
        draw_explanation()
    notes = {
        "no_key": "AI rewording is not set up in this deployment (no Gemini key). The rule-based explanation stays.",
        "error": "AI rewording is not available right now. The rule-based explanation stays.",
        "mismatch": "The AI text did not match the rules output, so the rule-based explanation stays.",
    }
    if L.get("ai_status") in notes:
        st.caption(notes[L["ai_status"]])
        if L.get("ai_status") == "error" and L.get("ai_detail"):
            st.caption("Reason: " + L["ai_detail"])

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
