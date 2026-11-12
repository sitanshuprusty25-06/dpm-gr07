"""Tests for the two issuer-models and the Gemini numeric safeguards."""
import unittest
from cards import CARDS
from rules_engine import evaluate,rank,inr,key_condition
from explain import build_payload,validate

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
        ranked=rank(CARDS,"fuel",1000)
        self.assertTrue(all(r.benefit==0 for r in ranked))
    def test_inr_format(self):
        self.assertEqual(inr(120000),"₹1,20,000")

class ExplanationChecks(unittest.TestCase):
    def setUp(self):
        r=rank([BY_ID["sbi_cashback"],BY_ID["hsbc_live_plus"]],"dining",8000,channel="online")
        self.w,self.s=r[0],r[1]
        self.p=build_payload(self.w,self.s,8000,"dining")
    def test_accepts_right_amount(self):
        msg=f"Use {self.w.card['name']}. Estimated cashback ₹800."
        self.assertTrue(validate(msg,self.p))
    def test_rejects_wrong_numeric_benefit_even_if_number_elsewhere(self):
        msg=f"Use {self.w.card['name']}. Estimated cashback ₹8000."
        self.assertFalse(validate(msg,self.p))
    def test_rejects_wrong_card(self):
        self.assertFalse(validate("Use Other Card. Cashback ₹800.",self.p))

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

if __name__=="__main__":
    unittest.main()
