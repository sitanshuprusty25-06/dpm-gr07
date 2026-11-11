"""Hand-checked tests for the rules engine and the number checker.

Run from this folder:  python -m unittest -v
"""

import unittest

from cards import CARDS, CATEGORY_LABELS
from explain import build_payload, validate
from rules_engine import evaluate, inr, key_condition, rank, template_explain

BY_ID = {c["id"]: c for c in CARDS}


class RulesEngineTests(unittest.TestCase):
    def test_deck_example_cap_hit(self):
        # Slide 10: Rs 12,000 online, 5% up to Rs 500 a month, 1% beyond -> Rs 520.
        r = evaluate(BY_ID["everyday"], "shopping", 12000)
        self.assertEqual(r.benefit, 520.0)
        self.assertEqual(r.code, "cap-hit")
        self.assertEqual(
            key_condition(r),
            "Monthly cap: only the first ₹10,000 of this purchase earns 5%. The rest earns 1%.",
        )

    def test_full_bonus_shows_cap_left(self):
        r = evaluate(BY_ID["voyage"], "travel", 8000)
        self.assertEqual(r.benefit, 400.0)
        self.assertEqual(r.code, "bonus")
        self.assertEqual(r.cap_left_after, 1100.0)

    def test_below_minimum(self):
        r = evaluate(BY_ID["dine"], "dining", 800)
        self.assertEqual(r.benefit, 8.0)
        self.assertEqual(r.code, "below-min")

    def test_bonus_with_minimum_met(self):
        r = evaluate(BY_ID["dine"], "dining", 2000)
        self.assertEqual(r.benefit, 200.0)
        self.assertEqual(r.code, "bonus")

    def test_cap_already_used(self):
        r = evaluate(BY_ID["everyday"], "shopping", 2000, used=500)
        self.assertEqual(r.benefit, 20.0)
        self.assertEqual(r.code, "cap-exhausted")

    def test_partly_used_cap(self):
        # Rs 300 of the Rs 500 cap used: Rs 200 left covers the first Rs 4,000 at 5%.
        r = evaluate(BY_ID["everyday"], "shopping", 5000, used=300)
        self.assertEqual(r.benefit, 210.0)
        self.assertEqual(r.code, "cap-hit")
        self.assertEqual(r.reason, "Only ₹200 of bonus left this month")

    def test_excluded_category(self):
        r = evaluate(BY_ID["voyage"], "fuel", 1000)
        self.assertEqual(r.benefit, 0.0)
        self.assertEqual(r.code, "excluded")

    def test_per_purchase_limit(self):
        # Fuel: 4% on the first Rs 4,000 (Rs 160, under the Rs 300 cap) + 0.5% on Rs 1,000.
        r = evaluate(BY_ID["fuel"], "fuel", 5000)
        self.assertEqual(r.benefit, 165.0)
        self.assertEqual(r.code, "above-max")

    def test_points_shown_for_points_card(self):
        # 2.5% of Rs 4,000 = Rs 100 = 400 points at Rs 0.25 each.
        r = evaluate(BY_ID["life"], "entertainment", 4000)
        self.assertEqual(r.benefit, 100.0)
        self.assertEqual(r.points, 400.0)

    def test_ranking_order_and_winner(self):
        wallet = [BY_ID[i] for i in ("voyage", "everyday", "dine", "flat2")]
        ranked = rank(wallet, "shopping", 12000)
        benefits = [r.benefit for r in ranked]
        self.assertEqual(benefits, sorted(benefits, reverse=True))
        self.assertEqual(ranked[0].card["id"], "everyday")
        self.assertEqual(ranked[1].card["id"], "flat2")

    def test_tie_goes_to_lower_fee(self):
        # Both earn 1% on "other"; Grocer Plus has the lower annual fee.
        ranked = rank([BY_ID["everyday"], BY_ID["grocer"]], "other", 1000)
        self.assertEqual(ranked[0].benefit, ranked[1].benefit)
        self.assertEqual(ranked[0].card["id"], "grocer")

    def test_no_reward_anywhere(self):
        ranked = rank([BY_ID["voyage"], BY_ID["flat2"]], "fuel", 1000)
        self.assertEqual(ranked[0].benefit, 0.0)

    def test_every_rule_category_exists(self):
        for c in CARDS:
            for cat in list(c["rules"]) + list(c["excl"]):
                self.assertIn(cat, CATEGORY_LABELS, f"{c['id']} uses unknown category {cat}")

    def test_inr_format(self):
        self.assertEqual(inr(12000), "₹12,000")
        self.assertEqual(inr(120000), "₹1,20,000")
        self.assertEqual(inr(0), "₹0")


class CheckerTests(unittest.TestCase):
    def setUp(self):
        wallet = [BY_ID[i] for i in ("voyage", "everyday", "dine", "flat2")]
        ranked = rank(wallet, "shopping", 12000)
        self.win, self.second = ranked[0], ranked[1]
        self.payload = build_payload(self.win, self.second, 12000, "shopping")

    def test_accepts_matching_numbers(self):
        text = (
            "Everyday Cashback should earn you about ₹520, an estimate, because the 5% "
            "bonus is capped at ₹500 a month."
        )
        self.assertTrue(validate(text, self.payload))

    def test_rejects_wrong_number(self):
        self.assertFalse(validate("Everyday Cashback should earn about ₹600.", self.payload))

    def test_rejects_missing_card_name(self):
        self.assertFalse(validate("This card should earn about ₹520.", self.payload))

    def test_template_passes_its_own_checker(self):
        text = template_explain(self.win, self.second, 12000, "shopping")
        self.assertIn("₹520", text)
        self.assertTrue(validate(text, self.payload))


if __name__ == "__main__":
    unittest.main()
