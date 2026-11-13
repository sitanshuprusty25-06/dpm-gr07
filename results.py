"""Present the computed recommendation and its checked AI explanation first."""
import html
import streamlit as st
from rules_engine import category_label,inr,key_condition
from explain import explain_comparison, explanation_parts
from ui import get_secret
from display_text import comparison_text, redemption_guidance, review_date

def others_html(ranked,mark_best):
    rows=[]
    maximum=max([r.benefit for r in ranked if r.available and r.comparable]+[0.01])
    for i,r in enumerate(ranked):
        best=" best" if mark_best and r.available and r.comparable and r.benefit>0.005 and abs(r.benefit-maximum)<0.005 else ""
        amount="Unavailable" if not r.available else inr(r.benefit) if r.comparable else "Not comparable"
        reason,form=comparison_text(r)
        form_html=f'<span class="reward-form">{html.escape(form)}</span>' if form else ""
        width=max(0,min(100,r.benefit/maximum*100)) if r.comparable else 0
        rows.append(
            f'<div class="cca-row{best}">'
            f'<span class="nm"><b>{html.escape(r.card["name"])}</b>'
            f'<span class="why">{html.escape(reason)}</span>{form_html}</span>'
            f'<span class="amt">{html.escape(amount)}</span></div>'
            f'<div class="fin-resultbar"><span style="width:{width:.1f}%"></span></div>'
        )
    return "".join(rows)

def panel_html(win,second,amount,cat):
    if win.benefit <= 0.005:
        return ('<div class="cca-panel"><div class="kicker">No modeled card reward</div>'
                '<div class="cname">None of these cards has an eligible calculated reward here</div>'
                '<div class="delta">Choose on convenience and check issuer conditions.</div></div>')
    purchase_label = {'shopping':'shopping','utilities':'utility bill','cinema':'cinema'}.get(cat,category_label(cat).lower())
    tied=second is not None and abs(win.benefit-second.benefit)<0.005
    if tied:
        delta=f"Same estimated benefit as {html.escape(second.card['name'])}; either card can work."
    elif second:
        delta=f"{inr(win.benefit-second.benefit)} more in estimated reward value than {html.escape(second.card['name'])}"
    else:
        delta="Only one selected card has a comparable result for this route."
    form=win.card.get("reward_label","reward")
    display_form=form if form=="Amazon Pay balance" or form.startswith(("Scapia Coins","Kiwis")) else form.lower()
    return (
        f'<div class="cca-panel">'
        f'<div class="kicker">{"Equal estimated reward" if tied else "Highest estimated reward value" if second else "Your selected card"}</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated {html.escape(display_form)} for this {inr(amount)} '
        f'{html.escape(purchase_label)} purchase</div>'
        f'<div class="delta">{delta}</div></div>'
    )

def render_result(L, request_ai=False):
    ranked,win,second,amount,cat=(L["ranked"],L["win"],L["second"],L["amount"],L["cat"])
    st.markdown("".join(f'<span class="fin-pill">{html.escape(str(x))}</span>' for x in [category_label(cat),L.get("channel",""),L.get("merchant_label","")] if x),unsafe_allow_html=True)
    if L.get("cap_assumed"):
        st.caption("Estimate assumes unused caps wherever prior cashback is zero. Adjust cashback already earned if needed.")
    eligible=[r for r in ranked if r.available]
    if not eligible:
        st.info("No selected card supports this modeled payment route. Check your payment method or choose another card you own.")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        render_details(ranked,{"message":"AI skipped: no selected card supports this payment route."})
        return
    win=eligible[0]
    second=eligible[1] if len(eligible)>1 else None
    uncertain=[r for r in eligible if not r.comparable]
    if uncertain:
        st.warning("We cannot identify a reliable winner yet. One or more selected rewards are uncertain.")
        for r in uncertain:
            st.markdown("**"+r.card["name"]+"**")
            st.write(r.uncertainty)
        st.caption("Next step: check the purchase route and reward allowances, or open the issuer conditions below. If still uncertain, use the partial estimates only.")
        st.markdown("**Available partial comparisons**")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        st.caption("No recommended card is shown while a selected card's reward is unresolved.")
        render_details(ranked,{"message":"AI skipped: one or more applicable rewards cannot be established."})
        return

    tied=[x for x in eligible if abs(x.benefit-win.benefit)<0.005]
    if win.benefit>0.005 and len(tied)>1:
        st.markdown('<div class="cca-panel"><div class="kicker">Equal highest estimated reward</div>'
                    f'<div class="cname">{html.escape(str(len(tied)))} cards are tied</div>'
                    f'<div class="figure">{inr(win.benefit)}</div>'
                    '<div class="delta">Compare the reward forms, conditions and convenience before choosing.</div></div>',unsafe_allow_html=True)
        st.markdown(others_html(ranked,True),unsafe_allow_html=True)
        st.markdown("**Check before paying**")
        for item in tied:
            st.caption(item.card["name"]+": "+key_condition(item))
        render_details(ranked,{"message":"AI skipped: equal estimated rewards. No tie-break is imposed."})
        return
    st.markdown(panel_html(win,second,amount,cat),unsafe_allow_html=True)
    if win.benefit<=0.005:
        st.markdown("**Selected cards**")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        render_details(ranked,{"message":"AI skipped: no positive modeled reward."})
        return
    def explain_html(reason, condition, ai):
        label="Why this card? · AI-assisted" if ai else "Why this card?"
        verified='<div class="cca-verified">Gemini response passed all six checks.</div>' if ai else ""
        return ('<div class="cca-explain"><div class="tag">'
                +html.escape(label)+'</div><div class="txt">'
                +html.escape(reason)+'</div><div class="cca-condition">'
                '<div class="wt">Check before paying</div><div class="txt">'
                +html.escape(condition)+'</div></div>'+verified+'</div>')

    # Render the complete rules-only explanation before waiting for AI.
    explanation_slot=st.empty()
    status_slot=st.empty()
    reason,condition=explanation_parts(win,second,amount,cat)
    explanation_slot.markdown(explain_html(reason,condition,False),unsafe_allow_html=True)
    if request_ai and L.get("ai_enabled") and len(tied)==1 and L.get("ai_status") is None:
        # Only an explicit Compare action can send purchase facts. Ordinary
        # reruns and opening diagnostics cannot trigger another request.
        with status_slot.container():
            with st.spinner("Your card is ready. Checking the AI explanation…"):
                ai_text,ai_status,ai_detail=explain_comparison(
                    ranked,amount,cat,True,
                    api_key=get_secret("GEMINI_API_KEY"),
                    model=get_secret("GEMINI_MODEL","gemini-3.5-flash-lite"))
        L.update(ai_text=ai_text,ai_status=ai_status,ai_detail=ai_detail)
        status_slot.empty()
    status=L.get("ai_status")
    diag=L.get("ai_detail")
    if not isinstance(diag,dict):
        diag={}
    checked=(status=="ok" and bool(L.get("ai_text")) and diag.get("api_response")
             and len(diag.get("checks",{}))==6 and all(diag["checks"].values()))
    reason,condition=explanation_parts(win,second,amount,cat,diag if checked else None)
    explanation_slot.markdown(explain_html(reason,condition,bool(checked)),unsafe_allow_html=True)
    if checked:
        status_slot.empty()
    elif status=="no_key":
        status_slot.info("AI explanation unavailable. The calculated result is unchanged.")
    elif status=="error":
        status_slot.warning("AI explanation unavailable. The calculated result is unchanged.")
    elif status=="mismatch":
        status_slot.warning("AI explanation could not be verified. The calculated result is unchanged.")
    elif status=="disabled":
        status_slot.caption("Rules-only comparison · AI not requested.")
        diag={"message":"AI not requested: rules-only comparison selected."}
    else:
        status_slot.caption("Rules-based explanation. Enable the optional AI explanation and compare again if desired.")

    st.markdown('<div class="cca-result-heading">Reward comparison</div>',unsafe_allow_html=True)
    # Keep the first three visible. Large wallets can expand the full list.
    st.markdown(others_html(ranked[:3],True),unsafe_allow_html=True)
    if len(ranked)>3:
        with st.expander(f"Compare all {len(ranked)} selected cards"):
            st.markdown(others_html(ranked,True),unsafe_allow_html=True)
    st.caption(f"Conditional estimates, not guaranteed savings. Recommended card issuer terms reviewed: {review_date(win.card['last_verified'])}.")
    render_details(ranked,diag,checked)


def render_details(ranked,diag,checked=False):
    """Keep diagnostics and sources accessible even when no winner is possible."""
    guidance=redemption_guidance(ranked)
    if guidance:
        st.caption(guidance)
    st.caption("For planned, affordable purchases only. Fees, interest and promotions are excluded; interest or fees can outweigh rewards.")
    with st.expander("All card conditions and official sources"):
        st.caption("Check the selected cards’ issuer terms for redemption and eligibility.")
        for item in ranked:
            st.markdown("**"+item.card["name"]+"**")
            st.write(key_condition(item))
            st.caption(item.card["caveat"])
            for j,source in enumerate(item.card.get("sources",[item.card["source"]]),1):
                st.link_button(f"Official terms {j} · {item.card['name']}",source)
        feedback=get_secret("FEEDBACK_URL")
        if feedback:
            st.link_button("Report wrong information",feedback)
            st.caption("External feedback form: do not include card numbers, banking credentials or personal purchase details.")
        else:
            st.link_button("Report a rule issue on GitHub","https://github.com/sitanshuprusty25-06/dpm-gr07/issues/new")
            st.caption("GitHub issues are public and require sign-in. Report only the card product and issuer rule; never share personal or purchase details.")
    with st.expander("AI verification · request status and checks"):
        st.caption("Checks compare the AI response with our computed facts, not live issuer terms.")
        st.write("Configured model: "+str(diag.get("model",get_secret("GEMINI_MODEL","gemini-3.5-flash-lite"))))
        st.write("API key configured: "+("Yes" if str(get_secret("GEMINI_API_KEY") or "").strip() else "No"))
        st.write("Provider response received: "+("Yes" if diag.get("api_response") else "Not confirmed"))
        if diag.get("sdk_version"):
            st.write("Google GenAI SDK: "+diag["sdk_version"])
        if diag.get("http_status") is not None:
            st.write(f"HTTP status: {diag['http_status']}")
        if diag.get("failure_type"):
            st.write("Failure category: "+diag["failure_type"])
        if diag.get("elapsed_ms") is not None:
            st.write(f"Request and validation time: {diag['elapsed_ms']} ms")
        for label,passed in diag.get("checks",{}).items():
            st.write(("PASS — " if passed else "FAIL — ")+label)
        if diag.get("message"):
            st.write(diag["message"])
        if checked:
            st.write("Selected reason: "+diag["reason_id"])
            st.write("Selected caution: "+diag["caution_id"])
            st.caption("Only approved financial statements are displayed.")
        elif not diag.get("api_response") and not diag.get("elapsed_ms"):
            st.caption("No AI request was made for this comparison.")
