"""Hand-checked tests for the rules engine and the number checker.

Run from this folder:  python -m unittest -v
"""

import unittest

from cards import CARDS
from explain import numbers_match, template_explanation
from rules_engine import evaluate_all, evaluate_card, inr

BY_ID = {c["id"]: c for c in CARDS}


class RulesEngineTests(unittest.TestCase):
    def test_deck_example_cap_hit(self):
        # Slide 10: Rs 12,000 online, 5% up to Rs 500 a month, 1% beyond -> Rs 520.
        r = evaluate_card(BY_ID["online_shopper"], 12000, "Online shopping")
        self.assertEqual(r.benefit, 520.0)
        self.assertEqual(r.condition_type, "cap_hit")

    def test_below_minimum(self):
        r = evaluate_card(BY_ID["online_shopper"], 400, "Online shopping")
        self.assertEqual(r.benefit, 4.0)
        self.assertEqual(r.condition_type, "below_min")

    def test_full_bonus_under_cap(self):
        r = evaluate_card(BY_ID["online_shopper"], 2000, "Online shopping")
        self.assertEqual(r.benefit, 100.0)
        self.assertEqual(r.condition_type, "full_bonus")

    def test_cap_already_used(self):
        r = evaluate_card(BY_ID["online_shopper"], 2000, "Online shopping", cap_used=500)
        self.assertEqual(r.benefit, 20.0)
        self.assertEqual(r.condition_type, "cap_exhausted")

    def test_excluded_category(self):
        r = evaluate_card(BY_ID["online_shopper"], 3000, "Fuel")
        self.assertEqual(r.benefit, 0.0)
        self.assertEqual(r.condition_type, "excluded")

    def test_points_valued_in_rupees(self):
        # 10 points per Rs 100 at Rs 0.25 each = 2.5% on Rs 10,000 = Rs 250.
        r = evaluate_card(BY_ID["travel_points"], 10000, "Travel")
        self.assertEqual(r.benefit, 250.0)

    def test_max_purchase_limit(self):
        # Fuel: 4% on first Rs 4,000 (= Rs 160, under the Rs 250 cap), 0.5% on Rs 1,000.
        r = evaluate_card(BY_ID["fuel_bills"], 5000, "Fuel")
        self.assertEqual(r.benefit, 165.0)
        self.assertEqual(r.condition_type, "max_purchase")

    def test_ranking_order(self):
        ranked = evaluate_all(CARDS, 12000, "Online shopping")
        benefits = [r.benefit for r in ranked]
        self.assertEqual(benefits, sorted(benefits, reverse=True))
        self.assertEqual(ranked[0].card_id, "online_shopper")

    def test_no_reward_anywhere(self):
        ranked = evaluate_all(
            [BY_ID["online_shopper"], BY_ID["everyday_cashback"]], 1000, "Utilities & bill payments"
        )
        self.assertEqual(ranked[0].benefit, 0.0)

    def test_inr_format(self):
        self.assertEqual(inr(12000), "₹12,000")
        self.assertEqual(inr(120000), "₹1,20,000")
        self.assertEqual(inr(520.5), "₹520.50")


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.ranked = evaluate_all(CARDS, 12000, "Online shopping")
        self.top = self.ranked[0].name

    def test_accepts_matching_numbers(self):
        text = f"{self.top} gives about ₹520 because the 5% bonus covers the first ₹10,000."
        self.assertTrue(numbers_match(text, self.ranked, self.top))

    def test_rejects_wrong_number(self):
        text = f"{self.top} gives about ₹600."
        self.assertFalse(numbers_match(text, self.ranked, self.top))

    def test_rejects_missing_card_name(self):
        self.assertFalse(numbers_match("This card gives about ₹520.", self.ranked, self.top))

    def test_template_has_only_allowed_numbers(self):
        text = template_explanation(self.ranked, 12000, "Online shopping")
        self.assertTrue(numbers_match(text, self.ranked, self.top))


if __name__ == "__main__":
    unittest.main()
