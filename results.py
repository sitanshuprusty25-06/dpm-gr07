"""Present the computed decision and reward comparison before the explanation."""
import html
import streamlit as st
from rules_engine import category_label,inr,key_condition
from explain import explanation_parts
from ai_guidance import build_guidance, request_guidance, guidance_fingerprint, CHECK_NAMES
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

def panel_html(win,second,amount,cat,partial=False,split=False,detail=False):
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
    # The shared scope note below the panels identifies unresolved cards once.
    detail_html=""
    if detail:
        reason,condition=explanation_parts(win,second,amount,cat)
        detail_html=('<div class="cca-panel-detail"><div class="delta"><strong>Why this card?</strong> '
                     +html.escape(reason)+'</div><div class="delta"><strong>Check before paying:</strong> '
                     +html.escape(condition)+'</div></div>')
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
        f'<div class="delta">{delta}</div>{detail_html}</div>'
    )

def ai_panel_html(option=None,status=None,partial=False):
    if option is None:
        message={"skipped":"AI needs one positive, comparable leader and an approved source.",
                 "no_key":"AI guidance is unavailable. Use the calculated result.",
                 "error":"AI guidance is unavailable. Use the calculated result.",
                 "mismatch":"AI response failed verification. Use the calculated result."}.get(status,"Checking an approved recommendation…")
        return ('<div class="cca-panel cca-ai-panel"><div class="kicker">AI GUIDANCE</div>'
                '<div class="delta">'+html.escape(message)+'</div></div>')
    return ('<div class="cca-panel cca-ai-panel"><div class="kicker">AI GUIDANCE · VERIFIED CHOICE'
            +(' AMONG COMPARABLE CARDS' if partial else '')+'</div>'
            '<div class="cname">'+html.escape(option["card"])+'</div>'
            '<div class="figure">'+inr(option["benefit_inr"])+'</div>'
            '<div class="delta">'+html.escape(option["reward_form"])+'</div>'
            '<div class="delta"><strong>'+html.escape(option["preference"])+'</strong></div>'
            '<div class="delta">'+html.escape(option["guidance"])+'</div>'
            '<div class="cca-panel-detail"><div class="delta"><strong>Check before paying:</strong> '
            +html.escape(option["condition"])+'</div></div>'
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

    def scope_note():
        if partial:
            st.caption("Both suggestions use comparable cards only. Not included: "
                       +", ".join(r.card["name"] for r in uncertain)
                       +". Their rewards could change the result." if enabled else
                       "Suggestion uses comparable cards only. Not included: "
                       +", ".join(r.card["name"] for r in uncertain)
                       +". Their rewards could change the result.")

    def comparison(mark=True):
        st.markdown('<div class="cca-result-heading">Reward comparison</div>',unsafe_allow_html=True)
        st.markdown(others_html(ranked[:3],mark),unsafe_allow_html=True)
        if len(ranked)>3:
            with st.expander(f"Compare all {len(ranked)} selected cards"):
                st.markdown(others_html(ranked,mark),unsafe_allow_html=True)
        if L.get("cap_assumed"):
            st.caption("Unused caps assumed where prior cashback is zero.")
        st.caption("Conditional estimates; fees, interest and promotions are excluded.")

    def details(diag,checked=False):
        render_details(ranked,diag,checked,show_ai=enabled)

    if not comparable or comparable[0].benefit<=0.005:
        if not eligible:
            st.info("No selected card supports this modeled payment route.")
        elif partial or not comparable:
            st.info("No positive reward can be estimated reliably yet. Check payment route or remaining allowance.")
        else:
            st.markdown(panel_html(comparable[0],None,amount,cat),unsafe_allow_html=True)
        if enabled:
            st.caption("AI guidance needs a unique positive comparable reward.")
        if partial:
            st.caption("Unresolved cards: "+", ".join(r.card["name"] for r in uncertain)+".")
        comparison(False)
        details({"message":"AI skipped: no positive comparable reward."})
        return
    win=comparable[0]
    second=comparable[1] if len(comparable)>1 else None
    tied=[r for r in comparable if abs(r.benefit-win.benefit)<0.005]
    if len(tied)>1:
        rule=('<div class="cca-panel"><div class="kicker">'+("Equal best among comparable cards" if partial else "Equal highest estimated reward")+'</div>'
              f'<div class="cname">{len(tied)} cards are tied</div><div class="figure">{inr(win.benefit)}</div>'
              '<div class="delta">Compare reward forms and conditions before choosing.</div></div>')
        st.markdown(rule,unsafe_allow_html=True)
        if enabled:
            st.caption("AI guidance does not impose a tie-break.")
        if partial:
            st.caption("Unresolved cards: "+", ".join(r.card["name"] for r in uncertain)+". Their rewards could change the result.")
        comparison()
        st.markdown("**Check before paying**")
        for item in tied:
            st.caption(item.card["name"]+": "+key_condition(item))
        details({"message":"AI skipped: equal highest comparable rewards."})
        return

    payload=build_guidance(ranked,amount,cat) if enabled else None

    def verified_option():
        diag=L.get("ai_detail")
        if not payload or L.get("ai_status")!="ok" or not isinstance(diag,dict) or not diag.get("api_response"):
            return None
        checks=diag.get("checks",{})
        if not isinstance(checks,dict) or set(checks)!=set(CHECK_NAMES) or any(v is not True for v in checks.values()):
            return None
        if diag.get("payload_fingerprint")!=guidance_fingerprint(payload):
            return None
        option_id=L.get("ai_option_id")
        return payload["options"].get(option_id) if isinstance(option_id,str) and option_id==diag.get("option_id") else None

    def display_panels(option,status):
        # A single issuer explanation per recommendation. For an aligned AI
        # choice it appears in purple; for a different choice or fallback,
        # the navy card retains its own rationale and mandatory conditions.
        same=bool(option and option["card_id"]==win.card["id"])
        rule=panel_html(win,second,amount,cat,partial=partial,split=enabled,detail=not same)
        if enabled and payload:
            return recommendation_html(rule,ai_panel_html(option,status,partial))
        return rule

    option=verified_option()
    status=L.get("ai_status")
    if status=="ok" and option is None:
        status="mismatch"
    if enabled and payload:
        panel=st.empty()
        panel.markdown(display_panels(option,status),unsafe_allow_html=True)
        alignment=st.empty()
    else:
        st.markdown(display_panels(None,status),unsafe_allow_html=True)
        if enabled:
            st.caption("AI guidance is unavailable for this comparison. The calculated recommendation remains.")
    scope_note()
    comparison()
    if enabled and payload and request_ai and L.get("ai_status") is None:
        with st.spinner("Checking AI guidance against comparable rewards…"):
            option_id,status,diag=request_guidance(ranked,amount,cat,True,
                api_key=get_secret("GEMINI_API_KEY"),
                model=get_secret("GEMINI_MODEL","gemini-3.5-flash-lite"))
        L.update(ai_option_id=option_id,ai_status=status,ai_detail=diag)
        option=verified_option()
    if enabled and payload:
        status=L.get("ai_status")
        if status=="ok" and option is None:
            status="mismatch"
        panel.markdown(display_panels(option,status),unsafe_allow_html=True)
        if option:
            same=option["card_id"]==win.card["id"]
            alignment.caption(("Both recommendations align among comparable cards." if partial else "Both recommendations align.")
                              if same else "Choose higher estimated value or the conditional reward-form alternative.")
        elif status is None:
            alignment.caption("Select Compare my cards to request AI guidance.")
    diag=L.get("ai_detail") if isinstance(L.get("ai_detail"),dict) and enabled and payload else {}
    if not diag:
        diag={"message":"AI not requested: disabled or no unique positive comparable reward with an approved source."}
    details(diag,bool(option))

def render_details(ranked,diag,checked=False,show_ai=True):
    """Keep diagnostics and sources accessible even when no winner is possible."""
    with st.expander("All card conditions and official sources"):
        st.caption("Check the selected cards’ issuer terms for redemption and eligibility. Interest or fees can outweigh rewards; use only for planned, affordable purchases.")
        guidance=redemption_guidance(ranked)
        if guidance:
            st.caption(guidance)
        for item in ranked:
            st.markdown("**"+item.card["name"]+"**")
            st.write(key_condition(item))
            st.caption(item.card["caveat"])
            st.caption("Issuer terms reviewed: "+review_date(item.card["last_verified"]))
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
    if not show_ai:
        return
    with st.expander("AI verification · request status and checks"):
        st.caption("Checks validate the AI response against computed comparable rewards and approved sources; they are not live issuer verification.")
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
