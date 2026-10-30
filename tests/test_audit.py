"""Real-file regression scenarios for the heuristic revision audit."""

import json
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/clarity-wiki/scripts'))

from clarity_wiki.audit import audit_revision
from clarity_wiki.workspace import InputError, Workspace


class RevisionAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = Workspace(self.root)

    def audit(self, original, revised, limit=5):
        (self.root / "original.txt").write_text(original, encoding="utf-8")
        (self.root / "revised.txt").write_text(revised, encoding="utf-8")
        return audit_revision(self.workspace, "original.txt", "revised.txt", limit)

    def test_negative_temperature_and_explicit_positive_sign(self):
        for before, after in [("-5°C", "5°C"), ("+5°C", "-5°C"), ("−5℃", "5℃")]:
            with self.subTest(before=before):
                result = self.audit(before, after)
                self.assertEqual("findings", result["status"])
                self.assertIn("NUMBER_CHANGED", [f["rule"] for f in result["findings"]])

    def test_spaced_and_korean_units(self):
        for before, after in [("길이 10 mm", "길이 10 kg"), ("접수 2건", "접수 2회")]:
            with self.subTest(before=before):
                result = self.audit(before, after)
                self.assertIn("UNIT_CHANGED", [f["rule"] for f in result["findings"]])

    def test_subject_value_swap_is_flagged(self):
        result = self.audit("A10%, B20%", "A20%, B10%")
        self.assertGreater(result["total_findings"], 0)

    def test_same_values_with_changed_subjects_are_candidates(self):
        result = self.audit("A10%, B20%", "B10%, A20%")
        self.assertIn("NUMBER_CONTEXT_CHANGED", [f["rule"] for f in result["findings"]])

    def test_repeated_number_removed(self):
        result = self.audit("10 10 10", "10 10")
        self.assertIn("NUMBER_REMOVED", [f["rule"] for f in result["findings"]])

    def test_number_added_and_removed(self):
        self.assertEqual("NUMBER_ADDED", self.audit("없음", "10")['findings'][0]['rule'])
        self.assertEqual("NUMBER_REMOVED", self.audit("10", "없음")['findings'][0]['rule'])

    def test_insertion_does_not_cascade(self):
        result = self.audit("10 20 30", "5 10 20 30")
        self.assertEqual(1, result["total_findings"])
        self.assertEqual("NUMBER_ADDED", result["findings"][0]["rule"])

    def test_quote_removal_and_replacement(self):
        for opening, closing in [('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’')]:
            with self.subTest(opening=opening):
                before = f"말: {opening}원문{closing}"
                removed = self.audit(before, "말: 원문")
                changed = self.audit(before, f"말: {opening}수정{closing}")
                self.assertIn("QUOTE_REMOVED", [f["rule"] for f in removed["findings"]])
                self.assertIn("QUOTE_CHANGED", [f["rule"] for f in changed["findings"]])

    def test_quote_addition_and_multiline_replacement(self):
        self.assertEqual("QUOTE_ADDED", self.audit("hello", '"hello"')["findings"][0]["rule"])
        self.assertEqual("QUOTE_CHANGED", self.audit('“one\ntwo”', '“one\nthree”')["findings"][0]["rule"])

    def test_korean_quote_with_following_particle(self):
        for before, after in [("‘원문’이라고 했다", "‘수정’이라고 했다"),
                              ("'원문'이라고 했다", "'수정'이라고 했다")]:
            with self.subTest(before=before):
                self.assertEqual("QUOTE_CHANGED", self.audit(before, after)["findings"][0]["rule"])

    def test_apostrophes_are_not_quotes(self):
        result = self.audit("It's fine; John's here.", "It’s fine; John’s here.")
        self.assertEqual(0, result["total_findings"])

    def test_exact_one_based_locations(self):
        finding = self.audit("앞줄\n온도 -5°C", "앞줄\n온도 5°C")["findings"][0]
        self.assertEqual({"path": "original.txt", "line": 2, "column": 4}, finding["original"]["location"])
        self.assertEqual({"path": "revised.txt", "line": 2, "column": 4}, finding["revised"]["location"])

    def test_complete_count_and_truncation(self):
        result = self.audit("1 2 3", "4 5 6", limit=1)
        self.assertEqual(3, result["total_findings"])
        self.assertEqual(1, len(result["findings"]))
        self.assertTrue(result["truncated"])
        full = self.audit("1 2 3", "4 5 6", limit=30)
        self.assertEqual(3, len(full["findings"]))
        self.assertFalse(full["truncated"])

    def test_invalid_limits_are_rejected(self):
        for limit in (0, 31, True, 1.5, "5"):
            with self.subTest(limit=limit), self.assertRaises(InputError):
                self.audit("1", "2", limit)

    def test_numeric_comma_formatting_is_harmless(self):
        result = self.audit("금액 1,000원", "금액 1000원")
        self.assertEqual(0, result["total_findings"])
        self.assertEqual("no_findings", result["status"])

    def test_unchanged_and_empty_inputs_have_heuristic_limitation(self):
        for document in ("", "A10%, B20%", '“원문” 10 mm'):
            with self.subTest(document=document):
                result = self.audit(document, document)
                self.assertEqual("audit_revision", result["tool"])
                self.assertEqual([], result["findings"])
                self.assertEqual(0, result["total_findings"])
                self.assertFalse(result["truncated"])
                self.assertIn("heuristic", result["limitations"].lower())

    def test_large_repeated_input_has_bounded_output(self):
        result = self.audit("1 " * 20000, "2 " * 20000, limit=1)
        self.assertEqual(20000, result["total_findings"])
        self.assertLess(len(json.dumps(result)), 2000)

    def test_long_quote_is_not_echoed(self):
        result = self.audit('"' + "a" * 30000 + '"', '"' + "b" * 30000 + '"')
        self.assertEqual("QUOTE_CHANGED", result["findings"][0]["rule"])
        self.assertLess(len(json.dumps(result)), 2000)

    def test_oversized_input_rejected(self):
        with self.assertRaises(InputError):
            self.audit("a" * 262145, "")


if __name__ == "__main__":
    unittest.main()
