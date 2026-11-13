"""Present the computed decision and reward comparison before the explanation."""
import html
import streamlit as st
from rules_engine import category_label,inr,key_condition
from explain import explanation_parts
from ai_guidance import build_guidance, request_guidance, CHECK_NAMES
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

def panel_html(win,second,amount,cat,partial=False,split=False):
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
    if partial:
        delta += " · Provisional suggestion; other selected rewards could not be estimated."
    form=win.card.get("reward_label","reward")
    display_form=form if form=="Amazon Pay balance" or form.startswith(("Scapia Coins","Kiwis")) else form.lower()
    return (
        f'<div class="cca-panel">'
        f'<div class="kicker">{"RULE-BASED RECOMMENDATION · " if split else ""}{"Best among comparable cards" if partial else "Equal estimated reward" if tied else "Highest estimated reward value" if second else "Your selected card"}</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated {html.escape(display_form)} for this {inr(amount)} '
        f'{html.escape(purchase_label)} purchase</div>'
        f'<div class="delta">{delta}</div></div>'
    )

def ai_panel_html(option=None,status=None):
    if option is None:
        message={"skipped":"AI is not used for incomplete, tied or zero-reward comparisons.",
                 "no_key":"AI guidance is unavailable. Use the calculated result.",
                 "error":"AI guidance is unavailable. Use the calculated result.",
                 "mismatch":"AI response failed verification. Use the calculated result."}.get(status,"Checking an approved recommendation…")
        return ('<div class="cca-panel cca-ai-panel"><div class="kicker">AI GUIDANCE</div>'
                '<div class="delta">'+html.escape(message)+'</div></div>')
    return ('<div class="cca-panel cca-ai-panel"><div class="kicker">AI GUIDANCE · VERIFIED CHOICE</div>'
            '<div class="cname">'+html.escape(option["card"])+'</div>'
            '<div class="figure">'+inr(option["benefit_inr"])+'</div>'
            '<div class="delta">'+html.escape(option["reward_form"])+'</div>'
            '<div class="delta"><strong>'+html.escape(option["preference"])+'</strong></div>'
            '<div class="delta">'+html.escape(option["guidance"])+'</div>'
            '<div class="delta"><a href="'+html.escape(option["source_url"],quote=True)+'" target="_blank" rel="noopener noreferrer">Official reward terms</a></div></div>')

def recommendation_html(rule,ai=None):
    return '<div class="cca-dual">'+rule+ai+'</div>' if ai is not None else rule

def render_result(L, request_ai=False):
    ranked,amount,cat=L["ranked"],L["amount"],L["cat"]
    enabled=bool(L.get("ai_enabled"))
    eligible=[r for r in ranked if r.available]
    comparable=[r for r in eligible if r.comparable]
    uncertain=[r for r in eligible if not r.comparable]
    partial=bool(uncertain)
    def notes():
        if partial:
            st.caption("Not included in the suggestion: "+", ".join(r.card["name"] for r in uncertain)+". Their rewards could change the result; check the conditions below.")
        if L.get("cap_assumed"):
            st.caption("Estimate assumes unused caps wherever prior cashback is zero. Adjust cashback already earned if needed.")
    def comparison(mark=True):
        st.markdown('<div class="cca-result-heading">Reward comparison</div>',unsafe_allow_html=True)
        st.markdown(others_html(ranked[:3],mark),unsafe_allow_html=True)
        if len(ranked)>3:
            with st.expander(f"Compare all {len(ranked)} selected cards"):
                st.markdown(others_html(ranked,mark),unsafe_allow_html=True)
        notes()
    if not comparable or (partial and comparable[0].benefit<=0.005):
        st.info("No positive reward can be estimated reliably yet. Check the payment route or remaining allowance.")
        if enabled:
            st.markdown(ai_panel_html(status="skipped"),unsafe_allow_html=True)
        comparison(False)
        render_details(ranked,{"message":"AI skipped: no reliable positive reward to suggest."})
        return
    win=comparable[0]
    second=comparable[1] if len(comparable)>1 else None
    tied=[r for r in comparable if abs(r.benefit-win.benefit)<0.005]
    if win.benefit>0.005 and len(tied)>1:
        rule=('<div class="cca-panel"><div class="kicker">'+("Equal best among comparable cards" if partial else "Equal highest estimated reward")+'</div>'
              f'<div class="cname">{len(tied)} cards are tied</div><div class="figure">{inr(win.benefit)}</div>'
              '<div class="delta">Compare the reward forms and conditions before choosing.</div></div>')
        st.markdown(recommendation_html(rule,ai_panel_html(status="skipped") if enabled else None),unsafe_allow_html=True)
        comparison()
        st.markdown("**Check before paying**")
        for item in tied:
            st.caption(item.card["name"]+": "+key_condition(item))
        render_details(ranked,{"message":"AI skipped: equal estimated rewards. No tie-break is imposed."})
        return
    rule=panel_html(win,second,amount,cat,partial=partial,split=enabled)
    payload=build_guidance(ranked,amount,cat) if enabled else None
    def verified_option():
        diag=L.get("ai_detail")
        if not payload or L.get("ai_status")!="ok" or not isinstance(diag,dict) or not diag.get("api_response"):
            return None
        checks=diag.get("checks",{})
        if set(checks)!=set(CHECK_NAMES) or any(v is not True for v in checks.values()):
            return None
        option_id=L.get("ai_option_id")
        return payload["options"].get(option_id) if isinstance(option_id,str) and option_id==diag.get("option_id") else None
    option=verified_option()
    status=L.get("ai_status")
    if enabled:
        panel=st.empty()
        panel.markdown(recommendation_html(rule,ai_panel_html(option,status if payload else "skipped")),unsafe_allow_html=True)
        alignment=st.empty()
    else:
        st.markdown(rule,unsafe_allow_html=True)
    comparison(win.benefit>0.005)
    if win.benefit<=0.005:
        render_details(ranked,{"message":"AI skipped: no positive modeled reward."})
        return
    st.caption(f"Conditional estimates, not guaranteed savings. Rules winner terms reviewed: {review_date(win.card['last_verified'])}.")
    # Build every explanation from locally calculated facts, never model prose.
    reason,condition=explanation_parts(win,second,amount,cat)
    st.markdown('<div class="cca-explain"><div class="tag">Why this calculated card?</div><div class="txt">'
                +html.escape(reason)+'</div><div class="cca-condition"><div class="wt">Check before paying</div><div class="txt">'
                +html.escape(condition)+'</div></div></div>',unsafe_allow_html=True)
    if enabled and payload and request_ai and status is None:
        with st.spinner("Checking AI guidance against calculated rewards…"):
            option_id,status,diag=request_guidance(ranked,amount,cat,True,
                api_key=get_secret("GEMINI_API_KEY"),
                model=get_secret("GEMINI_MODEL","gemini-3.5-flash-lite"))
        L.update(ai_option_id=option_id,ai_status=status,ai_detail=diag)
        option=verified_option()
    if enabled:
        status=L.get("ai_status")
        if payload and status=="ok" and option is None:
            status="mismatch"
        panel.markdown(recommendation_html(rule,ai_panel_html(option,status if payload else "skipped")),unsafe_allow_html=True)
        if option:
            same=option["card_id"]==win.card["id"]
            alignment.caption("Both recommendations align." if same else "Your choice depends on which reward you will actually use. The rules winner has the higher estimated value; the AI alternative is conditional.")
            st.caption("AI choice checked against calculated rewards and approved issuer references; not a live issuer verification.")
            st.caption(option["card"]+" — "+option["condition"])
        elif payload and status is None:
            alignment.caption("Select Compare my cards to request AI guidance.")
    diag=L.get("ai_detail") if isinstance(L.get("ai_detail"),dict) and enabled and payload else {}
    if not diag:
        diag={"message":"AI not requested: disabled or comparison is incomplete, tied or has no positive reward."}
    render_details(ranked,diag,bool(option))

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
                labels=item.card.get("source_labels",[])
                label=labels[j-1] if j<=len(labels) else f"Official terms {j}"
                st.link_button(f"{label} · {item.card['name']}",source)
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
            st.write("Selected approved option: "+diag["option_id"])
            st.caption("All eight grounding checks passed. Only locally approved financial statements and source links are displayed.")
        elif not diag.get("api_response") and not diag.get("elapsed_ms"):
            st.caption("No AI request was made for this comparison.")
