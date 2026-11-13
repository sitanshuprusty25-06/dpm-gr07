"""Presentation regressions for incomplete comparisons, with no external AI calls."""
import unittest
from unittest.mock import patch
from cards import CARDS
from rules_engine import rank, Result

BY_ID = {card["id"]: card for card in CARDS}


class ResultRenderingTests(unittest.TestCase):
    def render(self, ranked, amount=50099):
        from results import render_result
        state = {"ranked": ranked, "amount": amount, "cat": "shopping",
                 "ai_enabled": False, "ai_status": None, "cap_assumed": True}
        with patch("results.st") as st, patch("results.render_details") as details, \
                patch("results.request_guidance") as ai:
            render_result(state, request_ai=True)
            ai.assert_not_called()
            markdown = [str(call.args[0]) for call in st.markdown.call_args_list]
            captions = [str(call.args[0]) for call in st.caption.call_args_list]
            return markdown, captions, st.info.called, details.called

    def test_myntra_partial_suggestion_shows_decision_then_all_cards(self):
        ranked = rank([BY_ID[x] for x in ("amazon_icici", "sbi_cashback",
                      "scapia_visa", "kiwi_yes_klick")], "shopping", 50099,
                      merchant_type="myntra")
        self.assertEqual([(r.card["id"], r.benefit) for r in ranked if r.comparable],
                         [("sbi_cashback", 2000), ("scapia_visa", 1002),
                          ("amazon_icici", 500.99)])
        markdown, captions, info, details = self.render(ranked)
        self.assertIn("Best among comparable cards", markdown[0])
        self.assertIn("CASHBACK SBI Card", markdown[0])
        self.assertIn("₹2,000", markdown[0])
        self.assertIn("Reward comparison", markdown[1])
        self.assertIn("Not comparable", markdown[3])
        self.assertIn("YES BANK Klick RuPay Credit Card (Kiwi)", markdown[3])
        self.assertTrue(any("could change the result" in c for c in captions))
        self.assertFalse(info)
        self.assertTrue(details)

    def test_partial_ai_renders_once_and_keeps_scope_visible(self):
        from results import render_result
        from ai_guidance import build_guidance, guidance_fingerprint, CHECK_NAMES
        ranked=rank(CARDS,"shopping",4500,merchant_type="myntra")
        payload=build_guidance(ranked,4500,"shopping")
        diag={"api_response":True,"option_id":"highest_reward",
              "checks":dict.fromkeys(CHECK_NAMES,True),
              "payload_fingerprint":guidance_fingerprint(payload)}
        state={"ranked":ranked,"amount":4500,"cat":"shopping","ai_enabled":True,
               "ai_status":None,"cap_assumed":True}
        with patch("results.st") as st, patch("results.render_details") as details, \
                patch("results.request_guidance",return_value=("highest_reward","ok",diag)) as ai:
            render_result(state,request_ai=True)
            ai.assert_called_once()
            panel=st.empty.return_value.markdown.call_args.args[0]
            self.assertIn("AI GUIDANCE · VERIFIED CHOICE AMONG COMPARABLE CARDS",panel)
            self.assertIn("₹337.50",panel)
            self.assertEqual(panel.count("Check before paying:"),1)
            self.assertNotIn("Why this calculated card?",str(st.markdown.call_args_list))
            self.assertTrue(any("could change the result" in str(c) for c in st.caption.call_args_list))
            self.assertTrue(details.call_args.args[2])
            render_result(state,request_ai=False)
            ai.assert_called_once()

    def test_partial_tie_is_not_forced_into_single_winner(self):
        ranked = [Result(BY_ID["sbi_cashback"], "shopping", benefit=10),
                  Result(BY_ID["amazon_icici"], "shopping", benefit=10),
                  Result(BY_ID["kiwi_yes_klick"], "shopping", comparable=False,
                         uncertainty="Check route")]
        markdown, captions, info, details = self.render(ranked, 1000)
        self.assertIn("Equal best among comparable cards", markdown[0])
        self.assertIn("2 cards are tied", markdown[0])
        self.assertTrue(any("could change the result" in c for c in captions))

    def test_no_positive_comparable_reward_does_not_invent_suggestion(self):
        ranked = [Result(BY_ID["sbi_cashback"], "shopping", benefit=0),
                  Result(BY_ID["kiwi_yes_klick"], "shopping", comparable=False,
                         uncertainty="Check route")]
        markdown, captions, info, details = self.render(ranked, 1000)
        self.assertTrue(info)
        self.assertFalse(any("Best among comparable cards" in m for m in markdown))
        self.assertTrue(details)

    def test_all_unresolved(self):
        ranked = [Result(BY_ID["kiwi_yes_klick"], "shopping", comparable=False,
                         uncertainty="Check route")]
        markdown, captions, info, details = self.render(ranked, 1000)
        self.assertTrue(info)
        self.assertIn("Not comparable", markdown[1])


if __name__ == "__main__":
    unittest.main()
