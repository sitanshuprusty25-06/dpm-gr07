"""Present calculated card comparisons and optional Gemini wording."""
import html
import streamlit as st
from explain import ai_reword
from rules_engine import category_label,inr,key_condition,template_explain
from ui import get_secret

def others_html(ranked,mark_best):
    rows=[]
    for i,r in enumerate(ranked):
        best=" best" if mark_best and i==0 else ""
        amount=inr(r.benefit) if r.comparable else "Not comparable"
        reason=r.reason if r.comparable else r.uncertainty
        rows.append(
            f'<div class="cca-row{best}"><span class="dot" style="background:{r.card["hue"]}"></span>'
            f'<span class="nm"><b>{html.escape(r.card["name"])}</b>'
            f'<span class="why">{html.escape(reason)}</span></span>'
            f'<span class="amt">{html.escape(amount)}</span></div>'
        )
    return "".join(rows)

def panel_html(win,second,amount,cat):
    if win.benefit <= 0.005:
        return ('<div class="cca-panel"><div class="kicker">No modeled card cashback</div>'
                '<div class="cname">None of these cards has an eligible calculated reward here</div>'
                '<div class="delta">Choose on convenience and check issuer conditions.</div></div>')
    if second and abs(win.benefit-second.benefit)<0.005:
        delta=f"Same estimated benefit as {html.escape(second.card['name'])}; either card can work."
    elif second:
        delta=f"{inr(win.benefit-second.benefit)} above {html.escape(second.card['name'])}"
    else:
        delta="Only one selected card is modeled."
    return (
        f'<div class="cca-panel"><span class="swatch" style="background:{win.card["hue"]}"></span>'
        '<div class="kicker">Highest modeled eligible benefit</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated cashback for this {inr(amount)} '
        f'{html.escape(category_label(cat).lower())} purchase</div>'
        f'<div class="delta">{delta}</div></div>'
    )

def render_result(L):
    ranked,win,second,amount,cat=(L["ranked"],L["win"],L["second"],L["amount"],L["cat"])
    uncertain=[r for r in ranked if not r.comparable]
    if uncertain:
        st.warning("A defensible winner cannot be determined for every selected card. "
                   "The catalogue does not establish some merchant or after-cap rules.")
        for r in uncertain:
            st.error(f"{r.card['name']}: {r.uncertainty}")
        st.markdown("**Available partial comparisons**")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        st.caption("No recommended card is shown while a selected card's reward is unresolved.")
        return

    st.markdown(panel_html(win,second,amount,cat),unsafe_allow_html=True)
    if win.benefit<=0.005:
        st.markdown("**Selected cards**")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        return
    st.markdown('<div class="cca-watch"><div class="wt">Check before paying</div>'
                f'<div class="wb">{html.escape(key_condition(win))}</div></div>',unsafe_allow_html=True)

    def explain_html(message,ai):
        label="Gemini wording · numeric/card checks" if ai else "Deterministic explanation"
        return ('<div class="cca-explain"><span class="tag">'
                +html.escape(label)+'</span><div class="txt">'
                +html.escape(message)+'</div></div>')
    placeholder=st.empty()
    placeholder.markdown(explain_html(L.get("ai_text") or template_explain(win,second,amount,cat),
                                       bool(L.get("ai_text"))),unsafe_allow_html=True)
    if st.button("Reword explanation with Gemini",key="ai_btn"):
        with st.spinner("Rewording the computed facts..."):
            text,status,detail=ai_reword(win,second,amount,cat,
                         api_key=get_secret("GEMINI_API_KEY"),
                         model=get_secret("GEMINI_MODEL","gemini-2.5-flash"))
        L["ai_text"],L["ai_status"],L["ai_detail"]=text,status,detail
        placeholder.markdown(explain_html(text or template_explain(win,second,amount,cat),
                                         bool(text)),unsafe_allow_html=True)
    if L.get("ai_status") in {"no_key","error","mismatch"}:
        st.info("Gemini text was unavailable or did not pass the checks. The deterministic explanation remains.")
    st.markdown("**All selected cards**")
    st.markdown(others_html(ranked,True),unsafe_allow_html=True)
    st.caption(f"Issuer sources reviewed {win.card['last_verified']}. Results are conditional estimates, "
               "not guaranteed cashback. Merchant MCC and other exclusions may affect actual rewards. "
               "No card number or banking credential is requested.")
    with st.expander("Official issuer source"):
        st.link_button("Open issuer information",win.card["source"])
        st.write(win.card["caveat"])
    feedback=get_secret("FEEDBACK_URL")
    if feedback:
        st.link_button("Report wrong information",feedback)
