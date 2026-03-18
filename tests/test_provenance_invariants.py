import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROV_DIR = ROOT / "research" / "data" / "provenance"
MODEL_INPUT_DIR = PROV_DIR / "model_inputs"
sys.path.insert(0, str(ROOT / "code"))

from provenance import load_model_inputs  # noqa: E402


class ProvenanceInvariantTests(unittest.TestCase):
    ASSUMPTION_CLASSES = {"common_parlance", "scenario_model", "policy_anchor", "proxy"}

    def _iter_provenance_entries(self, node, path="$"):
        if isinstance(node, dict):
            provenance = node.get("provenance")
            if isinstance(provenance, dict):
                yield path, provenance
            for key, value in node.items():
                if key == "provenance":
                    continue
                child = f"{path}.{key}" if path != "$" else f"$.{key}"
                yield from self._iter_provenance_entries(value, child)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from self._iter_provenance_entries(value, f"{path}[{index}]")

    def test_all_model_inputs_have_generated_metadata(self):
        for path in MODEL_INPUT_DIR.glob("*_inputs.json"):
            payload = json.loads(path.read_text())
            self.assertIn("generated", payload, f"{path.name} missing generated metadata")
            generated = payload["generated"]
            self.assertIn("generator", generated)
            self.assertIn("artifact_lock_sha256", generated)

    def test_provenance_loader_accepts_all_inputs(self):
        for path in MODEL_INPUT_DIR.glob("*_inputs.json"):
            model_name = path.stem
            payload = load_model_inputs(model_name)
            self.assertIsInstance(payload, dict)

    def test_student_loan_thresholds_positive(self):
        payload = json.loads((MODEL_INPUT_DIR / "student_loans_inputs.json").read_text())
        thresholds = [plan["threshold"] for plan in payload["plans"]]
        self.assertTrue(all(value > 0 for value in thresholds))
        self.assertGreater(payload["plans"][1]["threshold"], payload["plans"][2]["threshold"])

    def test_rent_vs_own_parameter_ranges(self):
        payload = json.loads((MODEL_INPUT_DIR / "rent_vs_own_inputs.json").read_text())
        params = payload["parameters"]
        self.assertGreater(params["years"], 0)
        self.assertGreater(params["property_price_2024"], 0)
        self.assertGreater(params["monthly_rent_2024"], 0)
        self.assertGreater(params["rent_inflation"], 0)
        self.assertLess(params["deposit_percent"], 1)

    def test_historical_2024_totals_are_consistent(self):
        payload = json.loads((MODEL_INPUT_DIR / "historical_inputs.json").read_text())
        snapshot = next(item for item in payload["snapshots"] if item["year"] == 2024)
        category_sum = sum(category["weekly_amount"] for category in snapshot["categories"])
        self.assertAlmostEqual(category_sum, snapshot["avg_weekly_expenditure"], delta=1.5)

    def test_subscriptions_count_series_matches_modeled_stacks(self):
        payload = json.loads((MODEL_INPUT_DIR / "subscriptions_inputs.json").read_text())
        years = payload["subscription_count_series"]["years"]
        counts = payload["subscription_count_series"]["counts"]
        self.assertEqual(len(years), len(counts))
        for year, count in zip(years, counts):
            expenses = payload["household_stacks"][str(year)]["expenses"]
            expected = float(sum(1 for item in expenses if item.get("is_subscription", False)))
            self.assertEqual(count, expected)

    def test_assumption_register_exists(self):
        register = PROV_DIR / "ASSUMPTION_REGISTER.md"
        self.assertTrue(register.exists())
        text = register.read_text()
        for file_name in [
            "historical_inputs.json",
            "leasehold_inputs.json",
            "rent_vs_own_inputs.json",
            "student_loans_inputs.json",
            "subscriptions_inputs.json",
        ]:
            self.assertIn(file_name, text)

    def test_assumption_entries_include_source_ids(self):
        for path in MODEL_INPUT_DIR.glob("*_inputs.json"):
            payload = json.loads(path.read_text())
            for prov_path, provenance in self._iter_provenance_entries(payload):
                if provenance.get("kind") != "assumption":
                    continue
                self.assertIn("source_ids", provenance, f"{path.name}:{prov_path} missing source_ids")
                self.assertIsInstance(provenance["source_ids"], list)
                self.assertGreater(len(provenance["source_ids"]), 0)

    def test_assumption_entries_include_classification(self):
        for path in MODEL_INPUT_DIR.glob("*_inputs.json"):
            payload = json.loads(path.read_text())
            for prov_path, provenance in self._iter_provenance_entries(payload):
                if provenance.get("kind") != "assumption":
                    continue
                self.assertIn("assumption_class", provenance, f"{path.name}:{prov_path} missing assumption_class")
                self.assertIn(
                    provenance["assumption_class"],
                    self.ASSUMPTION_CLASSES,
                    f"{path.name}:{prov_path} invalid assumption_class={provenance.get('assumption_class')}",
                )


if __name__ == "__main__":
    unittest.main()
