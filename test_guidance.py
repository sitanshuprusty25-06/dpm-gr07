import json
import unittest
from unittest.mock import patch
from cards import CARDS
from rules_engine import rank
from ai_guidance import build_guidance, check_guidance, request_guidance, FIELDS

BY_ID={c["id"]:c for c in CARDS}

class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.ranked=rank([BY_ID["scapia_visa"],BY_ID["sbi_cashback"],BY_ID["amazon_icici"]],
                         "shopping",50099,channel="offline",merchant_type="other")
        self.payload=build_guidance(self.ranked,50099,"shopping")
    def response(self,key="cashlike_alternative"):
        option=self.payload["options"][key]
        return {k:option[k] for k in FIELDS}
    def test_conditional_alternative(self):
        option,checks=check_guidance(json.dumps(self.response()),self.payload)
        self.assertEqual(option["card_id"],"sbi_cashback")
        self.assertTrue(all(checks.values()))
        self.assertEqual(len(checks),8)
        self.assertEqual(option["benefit_inr"],500.99)
        self.assertIn("conditional alternative",option["guidance"])
    def test_reject_invented_values_and_sources(self):
        for field,value in (("card_id","unknown"),("benefit_inr",9999),("reward_form","cash"),
                            ("reason_id","invented"),("source_url","https://example.com"),
                            ("option_id","not_approved"),("benefit_inr",True)):
            with self.subTest(field=field,value=value):
                obj=self.response()
                obj[field]=value
                self.assertIsNone(check_guidance(json.dumps(obj),self.payload)[0])
    def test_reject_prose_extra_and_duplicate_keys(self):
        obj=self.response()
        obj["explanation"]="invented"
        self.assertIsNone(check_guidance(json.dumps(obj),self.payload)[0])
        self.assertIsNone(check_guidance("not JSON",self.payload)[0])
        raw=json.dumps(self.response())
        self.assertIsNone(check_guidance(raw[:-1]+',"card_id":"sbi_cashback"}',self.payload)[0])
    def test_partial_myntra_clear_leader_can_request_ai(self):
        ranked=rank(CARDS,"shopping",4500,merchant_type="myntra")
        payload=build_guidance(ranked,4500,"shopping")
        self.assertTrue(payload["comparison_scope"]["partial"])
        self.assertEqual(payload["rules_winner"],"flipkart_axis")
        option=payload["options"]["highest_reward"]
        self.assertEqual(option["benefit_inr"],337.5)
        self.assertEqual(set(payload["options"]),{"highest_reward"})
        response={k:option[k] for k in FIELDS}
        with patch("ai_guidance._call_gemini",return_value=json.dumps(response)) as call:
            self.assertEqual(request_guidance(ranked,4500,"shopping",False)[1],"disabled")
            call.assert_not_called()
            choice,status,diag=request_guidance(ranked,4500,"shopping",True,"key")
            self.assertEqual((choice,status),("highest_reward","ok"))
            self.assertTrue(all(diag["checks"].values()))
            self.assertTrue(diag["payload_fingerprint"])
            call.assert_called_once()
        self.assertNotIn("kiwi_yes_klick", {o["card_id"] for o in payload["options"].values()})

    def test_ties_and_all_unresolved_skip_provider(self):
        from rules_engine import Result
        tied=[Result(BY_ID["sbi_cashback"],"shopping",benefit=10),
              Result(BY_ID["amazon_icici"],"shopping",benefit=10)]
        unresolved=[Result(BY_ID["kiwi_yes_klick"],"shopping",comparable=False)]
        with patch("ai_guidance._call_gemini") as call:
            for ranked in (tied,unresolved):
                self.assertEqual(request_guidance(ranked,1000,"shopping",True,"key")[1],"skipped")
            call.assert_not_called()

    def test_provider_choice_and_failure(self):
        with patch("ai_guidance._call_gemini",return_value=json.dumps(self.response())):
            option,status,diag=request_guidance(self.ranked,50099,"shopping",True,"key")
            self.assertEqual((option,status),("cashlike_alternative","ok"))
            self.assertEqual(len(diag["checks"]),8)
        with patch("ai_guidance._call_gemini",return_value="fabricated"):
            self.assertEqual(request_guidance(self.ranked,50099,"shopping",True,"key")[:2],(None,"mismatch"))
    def test_cash_winner_has_no_arbitrary_alternative(self):
        ranked=rank([BY_ID["sbi_cashback"],BY_ID["scapia_visa"]],"shopping",3000,merchant_type="myntra")
        self.assertEqual(set(build_guidance(ranked,3000,"shopping")["options"]),{"highest_reward"})

if __name__=="__main__":
    unittest.main()
