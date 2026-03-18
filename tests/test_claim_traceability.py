import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from build_claim_traceability import _find_nearest_provenance, build_traceability_markdown  # noqa: E402


class ClaimTraceabilityTests(unittest.TestCase):
    def test_find_nearest_provenance_walks_up_tree(self):
        payload = {
            "parent": {
                "provenance": {"kind": "assumption", "assumption_basis": "test"},
                "child": [{"value": 123}],
            }
        }

        path, provenance = _find_nearest_provenance(payload, "$.parent.child[0].value")
        self.assertEqual(path, "$.parent")
        self.assertEqual(provenance["kind"], "assumption")

    def test_traceability_markdown_contains_known_claims(self):
        markdown = build_traceability_markdown()
        self.assertIn("# Claim Traceability", markdown)
        self.assertIn("student_plan2_threshold", markdown)
        self.assertIn("rent_vs_own_property_price_2024", markdown)


if __name__ == "__main__":
    unittest.main()
