"""Tests for the two issuer-models and the Gemini numeric safeguards."""
import unittest
import json
from unittest.mock import patch
from cards import CARDS,MARKET,CATALOG
from rules_engine import evaluate,rank,inr,key_condition,reward_bucket
from explain import build_payload,validate,check_response,ai_reword,explain_comparison,_error_category,explanation_parts

BY_ID={c["id"]:c for c in CARDS}

class IssuerRulesTests(unittest.TestCase):
    def test_sbi_online_cap(self):
        r=evaluate(BY_ID["sbi_cashback"],"dining",50000,channel="online")
        self.assertTrue(r.comparable);self.assertEqual(r.benefit,2000)
    def test_sbi_offline_rate(self):
        self.assertEqual(evaluate(BY_ID["sbi_cashback"],"groceries",10000,channel="offline").benefit,100)
    def test_sbi_channel_used_cap(self):
        self.assertEqual(evaluate(BY_ID["sbi_cashback"],"dining",10000,used=1950,channel="online").benefit,50)
    def test_sbi_after_cap_zero(self):
        self.assertEqual(evaluate(BY_ID["sbi_cashback"],"dining",8000,used=2000).benefit,0)
    def test_sbi_utilities_excluded(self):
        self.assertEqual(evaluate(BY_ID["sbi_cashback"],"utilities",5000).benefit,0)
    def test_hsbc_dining_eligible(self):
        self.assertEqual(evaluate(BY_ID["hsbc_live_plus"],"dining",8000).benefit,800)
    def test_hsbc_shared_cap_used(self):
        r=evaluate(BY_ID["hsbc_live_plus"],"dining",1000,used=1150)
        self.assertFalse(r.comparable)
        self.assertIn("not confirmed",r.uncertainty)
    def test_hsbc_remaining_cap_sufficient(self):
        r=evaluate(BY_ID["hsbc_live_plus"],"groceries",1000,used=1000)
        self.assertTrue(r.comparable);self.assertEqual(r.benefit,100)
    def test_hsbc_shopping_unknown(self):
        self.assertFalse(evaluate(BY_ID["hsbc_live_plus"],"shopping",2000).comparable)
    def test_hsbc_marketplace_known(self):
        r=evaluate(BY_ID["hsbc_live_plus"],"shopping",2000,merchant_type="marketplace")
        self.assertTrue(r.comparable);self.assertEqual(r.benefit,30)
    def test_hsbc_utilities_unknown(self):
        self.assertFalse(evaluate(BY_ID["hsbc_live_plus"],"utilities",3000).comparable)
    def test_hsbc_fuel_excluded(self):
        self.assertEqual(evaluate(BY_ID["hsbc_live_plus"],"fuel",1000).benefit,0)
    def test_tie_not_decided_by_annual_fee(self):
        ranked=rank([c for c in CARDS if c["id"] not in ("kiwi_yes_klick",)],"fuel",1000)
        self.assertTrue(all(r.benefit==0 for r in ranked))
    def test_inr_format(self):
        self.assertEqual(inr(120000),"₹1,20,000")
        self.assertEqual(inr(0.25),"₹0.25")
        self.assertEqual(inr(120000.75),"₹1,20,000.75")
        self.assertEqual(inr(10.10),"₹10.10")

class ExplanationChecks(unittest.TestCase):
    def setUp(self):
        r=rank([BY_ID["sbi_cashback"],BY_ID["hsbc_live_plus"]],"dining",8000,channel="online")
        self.w,self.s=r[0],r[1]
        self.p=build_payload(self.w,self.s,8000,"dining")
        rec=self.p["recommended"]
        self.good={"card_id":rec["card_id"],"benefit_inr":rec["benefit_inr"],
                   "reward_form":rec["reward_form"],"reason_id":"advantage",
                   "caution_id":"issuer_condition"}

    def test_accepts_right_amount(self):
        self.assertTrue(validate(json.dumps(self.good),self.p))
    def test_rejects_wrong_numeric_benefit(self):
        self.assertFalse(validate(json.dumps(dict(self.good,benefit_inr=8000)),self.p))
    def test_rejects_wrong_card(self):
        self.assertFalse(validate(json.dumps(dict(self.good,card_id="other")),self.p))
    def test_rejects_wrong_reward_form(self):
        self.assertFalse(validate(json.dumps(dict(self.good,reward_form="cash in bank")),self.p))
    def test_rejects_invented_reason(self):
        self.assertFalse(validate(json.dumps(dict(self.good,reason_id="guaranteed")),self.p))
    def test_rejects_invented_caution(self):
        self.assertFalse(validate(json.dumps(dict(self.good,caution_id="no cap applies")),self.p))
    def test_rejects_extra_prose(self):
        self.assertFalse(validate(json.dumps(dict(self.good,explanation="guaranteed")),self.p))
    def test_rejects_non_json(self):
        self.assertFalse(validate("Definitely use HSBC.",self.p))
    def test_rejects_duplicate_keys(self):
        duplicate=json.dumps(self.good)[:-1]+', "card_id": "other"}'
        self.assertFalse(validate(duplicate,self.p))
    def test_rejects_boolean_amount(self):
        self.assertFalse(validate(json.dumps(dict(self.good,benefit_inr=True)),self.p))
    def test_rejects_nonfinite_amount(self):
        self.assertFalse(validate(json.dumps(dict(self.good,benefit_inr=float("inf"))),self.p))
    def test_mocked_api_success(self):
        with patch("explain._call_gemini",return_value=json.dumps(self.good)):
            msg,status,diag=ai_reword(self.w,self.s,8000,"dining","test-key")
        self.assertEqual(status,"ok")
        self.assertTrue(diag["api_response"])
        self.assertEqual(len(diag["checks"]),6)
        self.assertTrue(all(diag["checks"].values()))
        self.assertIn("₹800",msg)
        self.assertIn(self.w.card["name"],msg)
    def test_mocked_api_rejection(self):
        with patch("explain._call_gemini",return_value=json.dumps(dict(self.good,benefit_inr=8000))):
            msg,status,diag=ai_reword(self.w,self.s,8000,"dining","test-key")
        self.assertIsNone(msg)
        self.assertEqual(status,"mismatch")
        self.assertFalse(diag["checks"]["Reward amount"])
    def test_missing_key_no_api_call(self):
        with patch("explain._call_gemini") as call:
            msg,status,diag=ai_reword(self.w,self.s,8000,"dining",None)
        call.assert_not_called()
        self.assertIsNone(msg)
        self.assertEqual(status,"no_key")
        self.assertFalse(diag["api_response"])
    def test_provider_error_fallback_does_not_leak_key(self):
        with patch("explain._call_gemini",side_effect=RuntimeError("403 secret-test-key")):
            msg,status,diag=ai_reword(self.w,self.s,8000,"dining","secret-test-key")
        self.assertIsNone(msg)
        self.assertEqual(status,"error")
        self.assertNotIn("secret-test-key",str(diag))
    def test_diagnostics_expose_failed_check(self):
        selection,checks,message=check_response(json.dumps(dict(self.good,reward_form="cash")),self.p)
        self.assertIsNone(selection)
        self.assertFalse(checks["Reward type"])
        self.assertTrue(checks["Recommended card"])
        self.assertTrue(message)

class AdditionalCardsTests(unittest.TestCase):
    def test_orange_swiggy(self):
        self.assertEqual(evaluate(BY_ID["swiggy_ornge"],"dining",1000,merchant_type="swiggy").benefit,50)
    def test_orange_minimum(self):
        self.assertEqual(evaluate(BY_ID["swiggy_ornge"],"dining",200,merchant_type="swiggy").benefit,0)
    def test_orange_shared_cap(self):
        self.assertEqual(evaluate(BY_ID["swiggy_ornge"],"shopping",1000,used=1480,merchant_type="amazon_prime").benefit,20)
    def test_original_swiggy(self):
        self.assertEqual(evaluate(BY_ID["swiggy_original"],"dining",1000,merchant_type="swiggy").benefit,100)
    def test_amazon_prime(self):
        self.assertEqual(evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_prime").benefit,50)
    def test_amazon_nonprime(self):
        self.assertEqual(evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_nonprime").benefit,30)

class ExpandedCardTests(unittest.TestCase):
    def test_original_minimum_updated(self):
        self.assertEqual(evaluate(BY_ID["swiggy_original"],"dining",200,merchant_type="swiggy").benefit,0)
    def test_blck_eligible_swiggy(self):
        self.assertEqual(evaluate(BY_ID["swiggy_blck"],"dining",1200,merchant_type="swiggy").benefit,120)
    def test_blck_minimum(self):
        self.assertEqual(evaluate(BY_ID["swiggy_blck"],"dining",200,merchant_type="swiggy").benefit,0)
    def test_blck_other_cap(self):
        self.assertEqual(evaluate(BY_ID["swiggy_blck"],"dining",5000,used=990,channel="offline",merchant_type="other").benefit,10)
    def test_axis_flipkart(self):
        self.assertEqual(evaluate(BY_ID["flipkart_axis"],"shopping",10000,merchant_type="flipkart").benefit,500)
    def test_axis_myntra(self):
        self.assertEqual(evaluate(BY_ID["flipkart_axis"],"shopping",10000,merchant_type="myntra").benefit,750)
    def test_axis_cleartrip(self):
        self.assertEqual(evaluate(BY_ID["flipkart_axis"],"hotel",10000,merchant_type="cleartrip").benefit,500)
    def test_axis_separate_buckets(self):
        c=BY_ID["flipkart_axis"]
        self.assertNotEqual(reward_bucket(c,"shopping","online","flipkart")[0],reward_bucket(c,"shopping","online","myntra")[0])
    def test_axis_cap_unresolved(self):
        self.assertFalse(evaluate(BY_ID["flipkart_axis"],"shopping",10000,used=3900,merchant_type="flipkart").comparable)
    def test_axis_utilities_excluded(self):
        self.assertEqual(evaluate(BY_ID["flipkart_axis"],"utilities",1000).benefit,0)
    def test_wrong_merchant_context(self):
        self.assertFalse(evaluate(BY_ID["swiggy_blck"],"hotel",1000,merchant_type="swiggy").comparable)

class KiwiScapiaTests(unittest.TestCase):
    def test_kiwi_completed_blocks(self):
        r=evaluate(BY_ID["kiwi_yes_klick"],"groceries",1099,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=100)
        self.assertEqual(r.benefit,15)
    def test_kiwi_cap(self):
        r=evaluate(BY_ID["kiwi_yes_klick"],"groceries",1000,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=4)
        self.assertEqual(r.benefit,4)
    def test_kiwi_online(self):
        self.assertEqual(evaluate(BY_ID["kiwi_yes_klick"],"shopping",1000,merchant_type="kiwi_online",kiwi_remaining=100).benefit,5)
    def test_kiwi_cap_unknown(self):
        self.assertFalse(evaluate(BY_ID["kiwi_yes_klick"],"groceries",1000,channel="upi",merchant_type="kiwi_qr").comparable)
    def test_scapia_visa(self):
        self.assertEqual(evaluate(BY_ID["scapia_visa"],"dining",1000,merchant_type="other").benefit,20)
    def test_scapia_rupay(self):
        self.assertEqual(evaluate(BY_ID["scapia_rupay"],"dining",1000,channel="upi",merchant_type="other").benefit,10)
    def test_scapia_rupay_minimum(self):
        self.assertEqual(evaluate(BY_ID["scapia_rupay"],"dining",499,channel="upi",merchant_type="other").benefit,0)
    def test_scapia_rupay_boundary(self):
        self.assertFalse(evaluate(BY_ID["scapia_rupay"],"dining",500,channel="upi",merchant_type="other").comparable)
    def test_scapia_travel(self):
        self.assertEqual(evaluate(BY_ID["scapia_visa"],"hotel",1000,merchant_type="scapia_travel").benefit,40)
    def test_scapia_utilities(self):
        self.assertEqual(evaluate(BY_ID["scapia_visa"],"utilities",1000,merchant_type="other").benefit,0)
    def test_ordinary_card_not_upi(self):
        r=evaluate(BY_ID["sbi_cashback"],"dining",1000,channel="upi",merchant_type="other")
        self.assertFalse(r.available)
    def test_upi_rank(self):
        ranked=rank([BY_ID["sbi_cashback"],BY_ID["scapia_rupay"],BY_ID["kiwi_yes_klick"]],"groceries",1000,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=100)
        self.assertEqual(ranked[0].card["id"],"kiwi_yes_klick")
        self.assertFalse(ranked[-1].available)

class AutomaticExplanationTests(unittest.TestCase):
    def setUp(self):
        self.ranked=rank([BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]],"dining",1200,
                         channel="online",merchant_type="swiggy")

    def test_enabled_comparison_calls_ai_once_without_changing_ranking(self):
        before=[(r.card["id"],r.benefit) for r in self.ranked]
        with patch("explain.ai_reword",return_value=("approved","ok",{})) as call:
            text,status,diag=explain_comparison(self.ranked,1200,"dining",True,"test-key")
        call.assert_called_once()
        self.assertEqual(status,"ok")
        self.assertEqual(before,[(r.card["id"],r.benefit) for r in self.ranked])

    def test_disabled_comparison_never_sends_data(self):
        with patch("explain.ai_reword") as call:
            text,status,diag=explain_comparison(self.ranked,1200,"dining",False,"test-key")
        call.assert_not_called()
        self.assertEqual(status,"disabled")

    def test_tied_comparison_never_calls_ai(self):
        tied=rank([BY_ID["swiggy_blck"],BY_ID["swiggy_original"]],"dining",1200,
                  channel="online",merchant_type="swiggy")
        with patch("explain.ai_reword") as call:
            text,status,diag=explain_comparison(tied,1200,"dining",True,"test-key")
        call.assert_not_called()
        self.assertEqual(status,"skipped")

    def test_unresolved_comparison_never_calls_ai(self):
        uncertain=rank([BY_ID["hsbc_live_plus"],BY_ID["sbi_cashback"]],"shopping",1200)
        with patch("explain.ai_reword") as call:
            text,status,diag=explain_comparison(uncertain,1200,"shopping",True,"test-key")
        call.assert_not_called()
        self.assertEqual(status,"skipped")

    def test_zero_reward_never_calls_ai(self):
        excluded=rank([BY_ID["sbi_cashback"]],"fuel",1200)
        with patch("explain.ai_reword") as call:
            text,status,diag=explain_comparison(excluded,1200,"fuel",True,"test-key")
        call.assert_not_called()
        self.assertEqual(status,"skipped")

class LatencyConfigurationTests(unittest.TestCase):
    def test_timeout_preserves_safe_fallback(self):
        ranked=rank([BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]],"dining",1200,
                    channel="online",merchant_type="swiggy")
        with patch("explain._call_gemini",side_effect=TimeoutError("request timed out")):
            msg,status,diag=explain_comparison(ranked,1200,"dining",True,"test-key")
        self.assertIsNone(msg)
        self.assertEqual(status,"error")
        self.assertIn("timed out",diag["message"])
        self.assertFalse(diag["api_response"])

class ProviderConfigurationTests(unittest.TestCase):
    def test_invalid_parameters_have_safe_diagnostic(self):
        err=RuntimeError("INVALID_ARGUMENT secret-test-key")
        self.assertEqual(_error_category(err),"Gemini rejected the request parameters (HTTP 400).")

    def test_sdk_configuration_error_has_safe_diagnostic(self):
        self.assertEqual(_error_category(TypeError("private payload")),"Gemini SDK or request configuration error.")

class MarketDisplayOrderTests(unittest.TestCase):
    def test_display_order_contains_every_card_once(self):
        ids=[c["id"] for c in CARDS]
        self.assertEqual(ids,MARKET["display_order"])
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(ids),{c["id"] for c in CATALOG["cards"]})

    def test_reward_ranking_independent_of_display_order(self):
        selected=[BY_ID["sbi_cashback"],BY_ID["swiggy_blck"]]
        a=rank(selected,"dining",1200,channel="online",merchant_type="swiggy")
        b=rank(list(reversed(selected)),"dining",1200,channel="online",merchant_type="swiggy")
        self.assertEqual([(r.card["id"],r.benefit) for r in a],[(r.card["id"],r.benefit) for r in b])
        self.assertEqual(a[0].card["id"],"swiggy_blck")

class ExplanationPresentationTests(unittest.TestCase):
    def test_sbi_capped_explanation_separates_calculation_and_caution(self):
        ranked=rank([BY_ID["sbi_cashback"],BY_ID["swiggy_ornge"]],"shopping",42163,
                    channel="online",merchant_type="eligible_online")
        win,second=ranked
        reason,condition=explanation_parts(win,second,42163,"shopping",
                                          {"reason_id":"eligibility","caution_id":"issuer_condition"})
        self.assertEqual(win.benefit,2000)
        self.assertIn("₹2,108.15",reason)
        self.assertIn("₹2,000",condition)
        self.assertNotIn("₹2,000",reason)
        self.assertEqual(condition,key_condition(win))
        self.assertTrue(reason.endswith("."))

    def test_fallback_also_retains_condition_once(self):
        win=evaluate(BY_ID["sbi_cashback"],"dining",1200)
        reason,condition=explanation_parts(win,None,1200,"dining")
        self.assertTrue(reason.endswith("."))
        self.assertEqual(condition,key_condition(win))

    def test_alternative_caution_keeps_mandatory_condition(self):
        win=evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_prime")
        reason,condition=explanation_parts(win,None,1000,"shopping",
                                          {"reason_id":"eligibility","caution_id":"redemption"})
        self.assertIn(build_payload(win,None,1000,"shopping")["caution_options"]["redemption"],condition)
        self.assertIn(key_condition(win),condition)

if __name__=="__main__":
    unittest.main()
