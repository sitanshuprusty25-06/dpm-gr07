"""Regression tests for the ten supported products, Gemini safeguards and repository consistency."""
import unittest
import json
import csv
from pathlib import Path
from unittest.mock import patch
from cards import (CARDS,MARKET,CATALOG, supports_credit_upi, payment_methods,
                   valid_payment_method, upi_merchant_routes)
from rules_engine import evaluate,rank,inr,key_condition,reward_bucket,money
from explain import build_payload,validate,check_response,ai_reword,explain_comparison,_error_category,explanation_parts,decision_tips

from display_text import comparison_text, redemption_guidance, review_date

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
                   "caution_id":"issuer_condition","tip_id":"planned_purchase"}

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
        self.assertEqual(len(diag["checks"]),7)
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
    def test_axis_cap_remaining(self):
        result=evaluate(BY_ID["flipkart_axis"],"shopping",10000,used=3900,merchant_type="flipkart")
        self.assertTrue(result.comparable)
        self.assertEqual(result.benefit,100)
    def test_axis_utilities_excluded(self):
        self.assertEqual(evaluate(BY_ID["flipkart_axis"],"utilities",1000).benefit,0)
    def test_wrong_merchant_context(self):
        self.assertFalse(evaluate(BY_ID["swiggy_blck"],"hotel",1000,merchant_type="swiggy").comparable)

class KiwiScapiaTests(unittest.TestCase):
    def test_kiwi_completed_blocks(self):
        r=evaluate(BY_ID["kiwi_yes_klick"],"groceries",1099,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=100)
        self.assertEqual(r.benefit,15)
    def test_kiwi_exact_minimum_and_sources(self):
        c=BY_ID["kiwi_yes_klick"]
        self.assertEqual(c["name"], "YES BANK Klick RuPay Credit Card (Kiwi)")
        self.assertEqual(c["fee"], 0)
        self.assertIn("https://apply.gokiwi.in/landing", c["sources"])
        self.assertEqual(len(c["sources"]), len(c["source_labels"]))
        for amount, expected in ((99.99, 0), (100, 1.5), (199.99, 1.5), (200, 3)):
            with self.subTest(amount=amount):
                r=evaluate(c,"groceries",amount,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=100)
                self.assertEqual(r.benefit,expected)
    def test_kiwi_bank_source_and_other_online_route(self):
        c=BY_ID["kiwi_yes_klick"]
        self.assertIn("https://www.yes.bank.in/personal-banking/yes-individual/cards/credit-cards/klick-credit-card",c["sources"])
        r=evaluate(c,"shopping",50099,merchant_type="myntra")
        self.assertFalse(r.comparable)
        self.assertIn("YES Rewardz",r.uncertainty)
    def test_partial_screenshot_ranking(self):
        ranked=rank([BY_ID[x] for x in ("amazon_icici","sbi_cashback","scapia_visa","kiwi_yes_klick")],"shopping",50099,merchant_type="myntra")
        comparable=[r for r in ranked if r.available and r.comparable]
        self.assertEqual(comparable[0].card["id"],"sbi_cashback")
        self.assertEqual(comparable[0].benefit,2000)
        self.assertTrue(any(not r.comparable for r in ranked))
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
        self.assertIn("₹1,500",reason)
        self.assertIn("₹2,000",condition)
        self.assertIn("also capped",reason)
        self.assertEqual(condition,key_condition(win))
        self.assertTrue(reason.endswith("."))

    def test_fallback_also_retains_condition_once(self):
        win=evaluate(BY_ID["sbi_cashback"],"dining",1200)
        reason,condition=explanation_parts(win,None,1200,"dining")
        self.assertTrue(reason.endswith("."))
        self.assertEqual(condition,key_condition(win))

    def test_redemption_caution_shows_mandatory_condition_once(self):
        win=evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_prime")
        for caution_id in ("issuer_condition","redemption"):
            with self.subTest(caution_id=caution_id):
                reason,condition=explanation_parts(win,None,1000,"shopping",
                                                  {"reason_id":"eligibility","caution_id":caution_id})
                self.assertEqual(reason,"5% on eligible Amazon purchases with Prime membership.")
                self.assertEqual(condition,key_condition(win))
                self.assertEqual(condition.count("Amazon Pay balance"),1)
        self.assertEqual(explanation_parts(win,None,1000,"shopping")[1],key_condition(win))

    def test_amazon_paise_and_ornge_shared_cap_example(self):
        cards=[BY_ID["amazon_icici"],BY_ID["swiggy_ornge"]]
        win,second=rank(cards,"shopping",74230.33,{"swiggy_ornge":1200},
                        channel="online",merchant_type="amazon_prime")
        self.assertEqual(win.card["id"],"amazon_icici")
        self.assertEqual(win.benefit,3711.52)
        self.assertEqual(second.benefit,300)
        self.assertEqual(second.cap_left_after,0)
        self.assertEqual(money(win.benefit-second.benefit),3411.52)
        reason,condition=explanation_parts(win,second,74230.33,"shopping",
                                          {"reason_id":"eligibility","caution_id":"redemption"})
        self.assertIn("Both cards have a 5%",reason)
        self.assertIn("₹300",reason)
        self.assertEqual(condition,key_condition(win))

    def test_amazon_reason_matches_purchase_route(self):
        card=BY_ID["amazon_icici"]
        for category,route,expected in [
            ("shopping","amazon_nonprime","3% on eligible Amazon purchases without Prime membership"),
            ("hotel","amazon_travel_prime","5% on eligible Amazon Pay hotel bookings with Prime membership"),
            ("hotel","amazon_travel_nonprime","3% on eligible Amazon Pay hotel bookings without Prime membership"),
            ("utilities","amazon_digital","2% on this eligible Amazon Pay payment"),
            ("shopping","other","1% on this eligible purchase"),
        ]:
            with self.subTest(route=route):
                result=evaluate(card,category,1000,merchant_type=route)
                self.assertTrue(result.comparable)
                self.assertEqual(result.reason,expected)

    def test_scapia_and_kiwi_redemption_condition_not_repeated(self):
        cases=[
            evaluate(BY_ID["scapia_visa"],"shopping",1000,merchant_type="other"),
            evaluate(BY_ID["kiwi_yes_klick"],"groceries",1000,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=25),
        ]
        for win in cases:
            with self.subTest(card=win.card["id"]):
                self.assertTrue(win.comparable)
                reason,condition=explanation_parts(win,None,1000,win.category,
                                                  {"reason_id":"eligibility","caution_id":"redemption"})
                self.assertEqual(condition,key_condition(win))

class FinePrintTests(unittest.TestCase):
    def test_axis_issuer_worked_examples(self):
        c=BY_ID["flipkart_axis"]
        self.assertEqual(evaluate(c,"shopping",30000,used=3000,merchant_type="flipkart").benefit,1000)
        self.assertEqual(evaluate(c,"hotel",90000,merchant_type="cleartrip").benefit,4000)
        self.assertEqual(evaluate(c,"hotel",6000,used=4000,merchant_type="cleartrip").benefit,0)

    def test_axis_food_delivery_not_instamart_or_dineout(self):
        c=BY_ID["flipkart_axis"]
        self.assertEqual(evaluate(c,"dining",1000,merchant_type="swiggy_food").benefit,40)
        self.assertEqual(evaluate(c,"groceries",1000,merchant_type="swiggy_other").benefit,10)
        self.assertEqual(evaluate(c,"dining",1000,merchant_type="swiggy_other").benefit,10)
        self.assertFalse(evaluate(c,"dining",1000,merchant_type="swiggy").comparable)

    def test_unconfirmed_merchant_never_recommends_sbi(self):
        r=evaluate(BY_ID["sbi_cashback"],"shopping",42163,merchant_type="unconfirmed")
        self.assertFalse(r.comparable)
        self.assertEqual(r.benefit,0)

    def test_hdfc_original_grocery_mcc_5411(self):
        self.assertEqual(evaluate(BY_ID["swiggy_original"],"groceries",1000,merchant_type="amazon_flipkart_grocery").benefit,50)

    def test_hdfc_named_merchant_not_shared_across_variants(self):
        self.assertEqual(evaluate(BY_ID["swiggy_blck"],"shopping",1000,merchant_type="myntra").benefit,50)
        self.assertFalse(evaluate(BY_ID["swiggy_ornge"],"shopping",1000,merchant_type="myntra").comparable)
        self.assertFalse(evaluate(BY_ID["swiggy_original"],"shopping",1000,merchant_type="marketplace").comparable)

    def test_ornge_cleartrip_shared_cap(self):
        self.assertEqual(evaluate(BY_ID["swiggy_ornge"],"hotel",10000,used=1400,merchant_type="cleartrip").benefit,100)

    def test_amazon_travel_and_digital(self):
        c=BY_ID["amazon_icici"]
        self.assertEqual(evaluate(c,"hotel",10000,merchant_type="amazon_travel_prime").benefit,500)
        self.assertEqual(evaluate(c,"hotel",10000,merchant_type="amazon_travel_nonprime").benefit,300)
        self.assertEqual(evaluate(c,"utilities",1000,merchant_type="amazon_digital").benefit,20)
        self.assertEqual(evaluate(c,"utilities",1000,merchant_type="other").benefit,0)

class RepositoryConsistencyTests(unittest.TestCase):
    def test_artwork_register_matches_catalogue(self):
        root=Path(__file__).resolve().parent
        artwork=json.loads((root/"assets"/"card_images.json").read_text(encoding="utf-8"))
        self.assertEqual(set(artwork),set(BY_ID))
        self.assertTrue(all(entry.get("source") for entry in artwork.values()))

    def test_kiwi_local_artwork_is_current_and_decodable(self):
        from PIL import Image
        root=Path(__file__).resolve().parent
        artwork=json.loads((root/"assets"/"card_images.json").read_text(encoding="utf-8"))
        kiwi=artwork["kiwi_yes_klick"]
        self.assertEqual(kiwi["local_path"],"assets/kiwi-yes-klick-green.webp")
        self.assertNotIn("guide_pdf",kiwi)
        self.assertFalse((root/"assets"/"kiwi-green-reference.webp").exists())
        with Image.open(root/kiwi["local_path"]) as im:
            self.assertEqual(im.format,"WEBP")
            self.assertEqual(im.size,(360,228))
            im.load()

    def test_source_register_matches_catalogue_and_order(self):
        root=Path(__file__).resolve().parent
        with (root/"card_catalog"/"source_register.csv").open(encoding="utf-8",newline="") as handle:
            rows=list(csv.DictReader(handle))
        self.assertEqual([row["card_id"] for row in rows],MARKET["display_order"])
        for row in rows:
            card=BY_ID[row["card_id"]]
            self.assertEqual(row["card_name"],card["name"])
            self.assertEqual(row["issuer"],card["issuer"])
            self.assertEqual(row["source"],card["source"])
            self.assertEqual(row["reviewed_on"],card["last_verified"])
            self.assertIn(card["source"],card["sources"])

    def test_only_current_views_remain_in_active_directory(self):
        root=Path(__file__).resolve().parent
        self.assertEqual({p.name for p in (root/"views").glob("*.py")},{"compare.py","supported_cards.py"})

class DecimalMoneyTests(unittest.TestCase):
    def test_purchase_paise_and_half_up(self):
        r=evaluate(BY_ID["sbi_cashback"],"dining",1200.50,merchant_type="other")
        self.assertEqual(r.benefit,60.03)
        self.assertEqual(r.cap_left_after,1939.97)
        self.assertEqual(inr(r.benefit),"₹60.03")

    def test_partial_cap_in_paise(self):
        r=evaluate(BY_ID["sbi_cashback"],"dining",1200.50,used=1999.75,merchant_type="other")
        self.assertEqual(r.benefit,0.25)
        self.assertEqual(r.cap_left_after,0.0)

    def test_hdfc_minimum_with_paise(self):
        c=BY_ID["swiggy_blck"]
        self.assertEqual(evaluate(c,"dining",248.99,merchant_type="swiggy_food").benefit,0)
        self.assertEqual(evaluate(c,"dining",249.00,merchant_type="swiggy_food").benefit,25)

    def test_axis_remaining_cap_paise(self):
        r=evaluate(BY_ID["flipkart_axis"],"shopping",1000.49,used=3999.89,merchant_type="flipkart")
        self.assertEqual(r.benefit,0.11)
        self.assertEqual(r.cap_left_after,0.0)

    def test_kiwi_completed_blocks_and_fractional_cap(self):
        c=BY_ID["kiwi_yes_klick"]
        r=evaluate(c,"groceries",199.99,channel="upi",merchant_type="kiwi_qr",kiwi_remaining=1.25)
        self.assertEqual(r.benefit,1.25)

    def test_decimal_payload_consistency(self):
        r=evaluate(BY_ID["sbi_cashback"],"dining",1200.50,merchant_type="other")
        p=build_payload(r,None,1200.50,"dining")
        self.assertEqual(p["purchase"]["amount_inr"],1200.50)
        self.assertEqual(p["recommended"]["benefit_inr"],60.03)
        good={"card_id":"sbi_cashback","benefit_inr":60.03,"reward_form":"Cashback","reason_id":"eligibility","caution_id":"issuer_condition","tip_id":"planned_purchase"}
        self.assertTrue(validate(json.dumps(good),p))
        self.assertFalse(validate(json.dumps(dict(good,benefit_inr=60.02)),p))

    def test_money_and_display_rounding(self):
        self.assertEqual(money(2.675),2.68)
        self.assertEqual(inr(2.675),"₹2.68")
        self.assertEqual(money(0.005),0.01)

    def test_link_register_is_unique_and_primary_first(self):
        for c in CARDS:
            self.assertEqual(c["sources"][0],c["source"])
            self.assertEqual(len(c["sources"]),len(set(c["sources"])))
            self.assertTrue(all(url.startswith("https://") for url in c["sources"]))
            self.assertEqual(c["links_checked_on"],"2026-11-12")

class PresentationScenarioTests(unittest.TestCase):
    def test_swiggy_cap_changes_decision(self):
        cards=[BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]]
        for used,expected in [(0,{"swiggy_blck":120,"sbi_cashback":60}),
                              (1440,{"swiggy_blck":60,"sbi_cashback":60}),
                              (1470,{"swiggy_blck":30,"sbi_cashback":60})]:
            with self.subTest(used=used):
                results=rank(cards,"dining",1200,{"swiggy_blck":used,"sbi_cashback":0},
                             channel="online",merchant_type="swiggy_food")
                self.assertTrue(all(item.available and item.comparable for item in results))
                self.assertEqual({item.card["id"]:item.benefit for item in results},expected)
                if used==0:
                    self.assertEqual(results[0].card["id"],"swiggy_blck")
                elif used==1470:
                    self.assertEqual(results[0].card["id"],"sbi_cashback")
                else:
                    self.assertEqual(results[0].benefit,results[1].benefit)

    def test_unknown_route_withholds_comparison(self):
        cards=[BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]]
        results=rank(cards,"dining",1200,channel="online",merchant_type="unconfirmed")
        self.assertTrue(all(item.available and not item.comparable for item in results))

class ContextualReasonTests(unittest.TestCase):
    def test_amazon_ornge_binding_cap_explained_for_every_reason(self):
        win,second=rank([BY_ID["amazon_icici"],BY_ID["swiggy_ornge"]],
                        "shopping",31253.52,{"swiggy_ornge":1200},
                        channel="online",merchant_type="amazon_prime")
        self.assertEqual(win.benefit,1562.68)
        self.assertEqual(second.benefit,300)
        payload=build_payload(win,second,31253.52,"shopping")
        for reason_id,reason in payload["reason_options"].items():
            with self.subTest(reason_id=reason_id):
                self.assertIn("Both cards have a 5%",reason)
                self.assertIn("₹300",reason)
                self.assertIn("no applicable reward cap",reason)
                self.assertNotIn("₹1,262.68",reason)
                displayed,condition=explanation_parts(win,second,31253.52,"shopping",
                    {"reason_id":reason_id,"caution_id":"redemption"})
                self.assertEqual(displayed,reason)
                self.assertEqual(condition,key_condition(win))
        self.assertEqual(explanation_parts(win,second,31253.52,"shopping")[0],
                         payload["reason_options"]["eligibility"])

    def test_swiggy_demo_cap_explained_when_sbi_leads(self):
        win,second=rank([BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]],
                        "dining",1200,{"swiggy_blck":1470},
                        channel="online",merchant_type="swiggy_food")
        self.assertEqual(win.card["id"],"sbi_cashback")
        p=build_payload(win,second,1200,"dining")
        for reason in p["reason_options"].values():
            self.assertIn("₹30",reason)
            self.assertNotIn("Both cards have",reason)
            self.assertNotIn("no applicable reward cap",reason)

    def test_no_binding_cap_claim_when_cap_does_not_limit_reward(self):
        win,second=rank([BY_ID["swiggy_blck"],BY_ID["sbi_cashback"]],
                        "dining",1200,channel="online",merchant_type="swiggy_food")
        p=build_payload(win,second,1200,"dining")
        self.assertIn("5% applicable reward rate",p["reason_options"]["advantage"])
        self.assertNotIn("has only",p["reason_options"]["advantage"])

    def test_two_binding_caps_not_described_as_uncapped(self):
        win,second=rank([BY_ID["sbi_cashback"],BY_ID["swiggy_ornge"]],
                        "shopping",50000,{"swiggy_ornge":1200},
                        channel="online",merchant_type="amazon_prime")
        p=build_payload(win,second,50000,"shopping")
        self.assertIn("also capped",p["reason_options"]["advantage"])
        self.assertIn("₹2,000",p["reason_options"]["advantage"])
        self.assertIn("₹300",p["reason_options"]["advantage"])

    def test_unresolved_comparator_does_not_generate_comparative_reason(self):
        win=evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_prime")
        second=evaluate(BY_ID["swiggy_ornge"],"shopping",1000,merchant_type="unconfirmed")
        self.assertNotIn("advantage",build_payload(win,second,1000,"shopping")["reason_options"])

class CustomerDisplayTests(unittest.TestCase):
    def test_ornge_binding_cap(self):
        r=evaluate(BY_ID["swiggy_ornge"],"shopping",41698.60,used=1200,merchant_type="amazon_prime")
        self.assertEqual(comparison_text(r),("5% cashback on eligible purchases · Limited by remaining cap","Statement credit"))
        self.assertEqual(r.benefit,300)
    def test_ornge_nonbinding_cap(self):
        r=evaluate(BY_ID["swiggy_ornge"],"shopping",1000,merchant_type="amazon_prime")
        self.assertEqual(comparison_text(r),("5% cashback on eligible purchases","Statement credit"))
    def test_amazon_prime_display(self):
        r=evaluate(BY_ID["amazon_icici"],"shopping",41698.60,merchant_type="amazon_prime")
        self.assertEqual(r.benefit,2084.93)
        self.assertEqual(comparison_text(r),("5% on eligible Amazon purchases with Prime membership","Amazon Pay balance"))
    def test_redemption_guidance_selected_only(self):
        a=evaluate(BY_ID["amazon_icici"],"shopping",1000,merchant_type="amazon_prime")
        b=evaluate(BY_ID["swiggy_ornge"],"shopping",1000,merchant_type="amazon_prime")
        self.assertIn("Amazon Pay balance",redemption_guidance([a,b]))
        self.assertNotIn("Scapia",redemption_guidance([a,b]))
        self.assertNotIn("Kiwi",redemption_guidance([a,b]))
        self.assertEqual(redemption_guidance([b]),"")
        s=evaluate(BY_ID["scapia_visa"],"shopping",1000,merchant_type="other")
        self.assertIn("Scapia Coins",redemption_guidance([s,b]))
        self.assertNotIn("Amazon",redemption_guidance([s,b]))
    def test_unknown_and_below_minimum(self):
        a=evaluate(BY_ID["swiggy_ornge"],"shopping",1000,merchant_type="unconfirmed")
        b=evaluate(BY_ID["swiggy_ornge"],"shopping",100,merchant_type="amazon_prime")
        self.assertEqual(comparison_text(a),(a.uncertainty,""))
        self.assertEqual(comparison_text(b),(b.reason,""))
    def test_review_date(self):
        self.assertEqual(review_date("2026-11-12"),"12 Nov 2026")
        self.assertEqual(review_date("2026-11-01"),"1 Nov 2026")
        self.assertEqual(review_date(None),"Not recorded")

class DecisionTipTests(unittest.TestCase):
    def setUp(self):
        self.win,self.second=rank([BY_ID["amazon_icici"],BY_ID["swiggy_ornge"]],
            "shopping",21435.40,{"swiggy_ornge":1200},channel="online",merchant_type="amazon_prime")
        self.payload=build_payload(self.win,self.second,21435.40,"shopping")
        r=self.payload["recommended"]
        self.good={"card_id":r["card_id"],"benefit_inr":r["benefit_inr"],"reward_form":r["reward_form"],
                   "reason_id":"eligibility","caution_id":"issuer_condition","tip_id":"reward_tradeoff"}
    def test_contextual_tradeoff(self):
        tip=self.payload["tip_options"]["reward_tradeoff"]
        self.assertIn("₹771.77",tip)
        self.assertIn("Amazon Pay balance",tip)
        self.assertIn("Statement credit",tip)
        self.assertNotIn("Scapia",tip)
    def test_validated_tip(self):
        selected,checks,_=check_response(json.dumps(self.good),self.payload)
        self.assertIsNotNone(selected)
        self.assertEqual(len(checks),7)
        self.assertTrue(all(checks.values()))
    def test_reject_unknown_tip(self):
        selected,checks,_=check_response(json.dumps(dict(self.good,tip_id="guaranteed_cash")),self.payload)
        self.assertIsNone(selected)
        self.assertFalse(checks["Approved decision tip"])
    def test_missing_tip_rejected(self):
        good=dict(self.good)
        del good["tip_id"]
        self.assertFalse(validate(json.dumps(good),self.payload))
    def test_provider_tip_and_rules_fallback(self):
        with patch("explain._call_gemini",return_value=json.dumps(self.good)):
            msg,status,diag=ai_reword(self.win,self.second,21435.40,"shopping","test-key")
        self.assertEqual(status,"ok")
        self.assertEqual(diag["tip_id"],"reward_tradeoff")
        self.assertIn(self.payload["tip_options"]["reward_tradeoff"],msg)
        reason,condition=explanation_parts(self.win,self.second,21435.40,"shopping")
        self.assertIn("₹300",reason)
        self.assertIn("Amazon Pay balance",condition)
    def test_no_irrelevant_tradeoff_single_card(self):
        tips=decision_tips(self.win,None)
        self.assertNotIn("reward_tradeoff",tips)
        self.assertNotIn("cap_tradeoff",tips)
        self.assertIn("use_balance",tips)

class PaymentChoiceTests(unittest.TestCase):
    def test_no_rupay_no_qr(self):
        for selected in ([], [BY_ID["amazon_icici"], BY_ID["swiggy_ornge"]],
                         [BY_ID["scapia_visa"]]):
            with self.subTest(selected=selected):
                self.assertEqual(payment_methods(selected), ["online", "offline"])
                self.assertEqual(upi_merchant_routes(selected), {})

    def test_each_supported_rupay_offers_qr(self):
        for card_id in ("kiwi_yes_klick", "scapia_rupay"):
            with self.subTest(card_id=card_id):
                selected = [BY_ID[card_id], BY_ID["amazon_icici"]]
                self.assertEqual(payment_methods(selected), ["online", "offline", "upi"])
                self.assertEqual(valid_payment_method(selected, "upi"), "upi")
                self.assertTrue(supports_credit_upi(BY_ID[card_id]))

    def test_removing_last_rupay_resets_channel(self):
        self.assertEqual(valid_payment_method([BY_ID["scapia_visa"]], "upi"), "online")
        self.assertEqual(valid_payment_method([], "upi"), "online")
        self.assertEqual(valid_payment_method([BY_ID["amazon_icici"]], "offline"), "offline")

    def test_kiwi_qr_route_only_when_kiwi_selected(self):
        self.assertEqual(list(upi_merchant_routes([BY_ID["scapia_rupay"]])),
                         ["unconfirmed", "other"])
        self.assertEqual(list(upi_merchant_routes([BY_ID["kiwi_yes_klick"]])),
                         ["unconfirmed", "kiwi_qr", "other"])
        self.assertIn("kiwi_qr", upi_merchant_routes(
            [BY_ID["kiwi_yes_klick"], BY_ID["scapia_rupay"]]))

    def test_ui_upi_support_matches_engine(self):
        for card in CARDS:
            with self.subTest(card=card["id"]):
                result = evaluate(card, "shopping", 1000, channel="upi",
                                  merchant_type="other")
                self.assertEqual(result.available, supports_credit_upi(card))

if __name__=="__main__":
    unittest.main()
