"""Present the computed recommendation and its checked AI explanation first."""
import html
import streamlit as st
from rules_engine import category_label,inr,key_condition,template_explain
from explain import explain_comparison
from ui import get_secret

def others_html(ranked,mark_best):
    rows=[]
    maximum=max([r.benefit for r in ranked if r.available and r.comparable]+[0.01])
    for i,r in enumerate(ranked):
        best=" best" if mark_best and r.available and r.comparable and r.benefit>0.005 and abs(r.benefit-maximum)<0.005 else ""
        amount="Unavailable" if not r.available else inr(r.benefit) if r.comparable else "Not comparable"
        reason=r.reason if not r.available else (r.reason+" · "+r.card.get("reward_label","Cashback")) if r.comparable else r.uncertainty
        width=max(0,min(100,r.benefit/maximum*100)) if r.comparable else 0
        rows.append(
            f'<div class="cca-row{best}"><span class="dot" style="background:{r.card["hue"]}"></span>'
            f'<span class="nm"><b>{html.escape(r.card["name"])}</b>'
            f'<span class="why">{html.escape(reason)}</span></span>'
            f'<span class="amt">{html.escape(amount)}</span></div>'
            f'<div class="fin-resultbar"><span style="width:{width:.1f}%;background:{r.card["hue"]}"></span></div>'
        )
    return "".join(rows)

def panel_html(win,second,amount,cat):
    if win.benefit <= 0.005:
        return ('<div class="cca-panel"><div class="kicker">No modeled card reward</div>'
                '<div class="cname">None of these cards has an eligible calculated reward here</div>'
                '<div class="delta">Choose on convenience and check issuer conditions.</div></div>')
    tied=second is not None and abs(win.benefit-second.benefit)<0.005
    if tied:
        delta=f"Same estimated benefit as {html.escape(second.card['name'])}; either card can work."
    elif second:
        delta=f"{inr(win.benefit-second.benefit)} above {html.escape(second.card['name'])}"
    else:
        delta="Only one selected card is eligible for this modeled route."
    return (
        f'<div class="cca-panel"><span class="swatch" style="background:{win.card["hue"]}"></span>'
        f'<div class="kicker">{"Equal estimated reward" if tied else "Highest estimated eligible reward" if second else "Your selected card"}</div>'
        f'<div class="cname">{html.escape(win.card["name"])}</div>'
        f'<div class="issuer">{html.escape(win.card["issuer"])}</div>'
        f'<div class="figure">{inr(win.benefit)}</div>'
        f'<div class="delta">estimated {html.escape(win.card.get("reward_label","reward").lower())} for this {inr(amount)} '
        f'{html.escape(category_label(cat).lower())} purchase</div>'
        f'<div class="delta">{delta}</div></div>'
    )

def render_result(L, request_ai=False):
    ranked,win,second,amount,cat=(L["ranked"],L["win"],L["second"],L["amount"],L["cat"])
    st.markdown("".join(f'<span class="fin-pill">{html.escape(str(x))}</span>' for x in [category_label(cat),L.get("channel",""),L.get("merchant_label","")] if x),unsafe_allow_html=True)
    if L.get("cap_assumed"):
        st.caption("Assumption: cashback caps with zero prior usage are treated as unused. Adjust previous cashback earned if needed.")
    eligible=[r for r in ranked if r.available]
    if not eligible:
        st.info("None of your selected cards supports this modeled payment route.")
        st.markdown(others_html(ranked,False),unsafe_allow_html=True)
        render_details(ranked,{"message":"AI skipped: no selected card supports this payment route."})
        return
    win=eligible[0]
    second=eligible[1] if len(eligible)>1 else None
    uncertain=[r for r in eligible if not r.comparable]
    if uncertain:
        st.warning("A defensible winner cannot be determined for every selected card. "
                   "The catalogue does not establish some merchant or after-cap rules.")
        for r in uncertain:
            st.error(f"{r.card['name']}: {r.uncertainty}")
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
                    '<div class="delta">Compare the reward forms and conditions before choosing.</div></div>',unsafe_allow_html=True)
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
    def explain_html(message,ai):
        label="AI-assisted recommendation explanation" if ai else "Rules-based explanation"
        return ('<div class="cca-explain"><span class="tag'+(' ai' if ai else '')+'">'
                +html.escape(label)+'</span><div class="txt">'
                +html.escape(message)+'</div></div>')

    # Show the financial result and mandatory conditions before waiting for AI.
    # Keep its eventual explanation in the same position above the conditions.
    explanation_slot=st.empty()
    status_slot=st.empty()
    fallback=template_explain(win,second,amount,cat)
    explanation_slot.markdown(explain_html(fallback,False),unsafe_allow_html=True)
    st.markdown('<div class="cca-watch"><div class="wt">Check before paying</div>'
                f'<div class="wb">{html.escape(key_condition(win))}</div></div>',unsafe_allow_html=True)
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
    explanation_slot.markdown(explain_html(L["ai_text"] if checked else fallback,
                                          bool(checked)),unsafe_allow_html=True)
    if checked:
        status_slot.caption("Gemini responded · all six grounding checks passed.")
    elif status=="no_key":
        status_slot.info("AI is not configured. The rules-based recommendation remains available.")
    elif status=="error":
        status_slot.warning("AI request failed. The rules-based recommendation remains available.")
    elif status=="mismatch":
        status_slot.warning("AI response rejected by grounding checks. Rules-based explanation shown.")
    elif status=="disabled":
        status_slot.caption("AI turned off · compared using local rules only.")
        diag={"message":"AI not requested: rules-only comparison selected."}
    else:
        status_slot.caption("Rules-based explanation. Select Compare with AI to request AI assistance.")

    st.markdown("**Reward comparison**")
    # Keep the first three visible. Large wallets can expand the full list.
    st.markdown(others_html(ranked[:3],True),unsafe_allow_html=True)
    if len(ranked)>3:
        with st.expander(f"Compare all {len(ranked)} selected cards"):
            st.markdown(others_html(ranked,True),unsafe_allow_html=True)
    st.caption(f"Conditional estimates, not guaranteed cashback. Reward forms differ; fees, interest and promotions excluded. Winner source reviewed {win.card['last_verified']}.")
    render_details(ranked,diag,checked)


def render_details(ranked,diag,checked=False):
    """Keep diagnostics and sources accessible even when no winner is possible."""
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
    with st.expander("All card conditions and official sources"):
        st.caption("Amazon Pay balance and Scapia Coins are restricted redemption value; Kiwi rewards are bank-redeemable. See issuer terms for redemption and eligibility.")
        for item in ranked:
            st.markdown("**"+item.card["name"]+"**")
            st.write(key_condition(item))
            st.caption(item.card["caveat"])
            for j,source in enumerate(item.card.get("sources",[item.card["source"]]),1):
                st.link_button(f"Official terms {j} · {item.card['name']}",source)
    feedback=get_secret("FEEDBACK_URL")
    if feedback:
        st.link_button("Report wrong information",feedback)
