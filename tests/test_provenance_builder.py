import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from build_provenance_inputs import _looks_rate_limited, _parse_numeric, validate_artifact_hashes  # noqa: E402


class ProvenanceBuilderTests(unittest.TestCase):
    def test_parse_numeric_handles_currency_values(self):
        self.assertEqual(_parse_numeric("£1,285"), 1285.0)
        self.assertEqual(_parse_numeric("7.7"), 7.7)

    def test_looks_rate_limited_detects_ons_blocks(self):
        self.assertTrue(_looks_rate_limited(b"Rate limited - too many HTTP requests"))
        self.assertTrue(_looks_rate_limited(b"Temporary access block to this page"))
        self.assertFalse(_looks_rate_limited(b"normal csv content"))

    def test_validate_hashes_allows_optional_missing_artifact(self):
        registry = {
            "sources": [
                {"id": "required", "required_for_extraction": True, "expected_sha256": "abc"},
                {"id": "optional", "required_for_extraction": False},
            ]
        }
        artifacts = {
            "artifacts": {
                "required": {"sha256": "abc"},
                "optional": {"sha256": None},
            }
        }
        validate_artifact_hashes(registry, artifacts)

    def test_validate_hashes_rejects_required_missing_artifact(self):
        registry = {
            "sources": [
                {"id": "required", "required_for_extraction": True},
            ]
        }
        artifacts = {"artifacts": {"required": {"sha256": None}}}

        with self.assertRaises(ValueError) as error:
            validate_artifact_hashes(registry, artifacts)

        self.assertIn("Missing required source artifacts", str(error.exception))

    def test_validate_hashes_rejects_hash_drift(self):
        registry = {
            "sources": [
                {"id": "source", "required_for_extraction": True, "expected_sha256": "expected"},
            ]
        }
        artifacts = {"artifacts": {"source": {"sha256": "actual"}}}

        with self.assertRaises(ValueError) as error:
            validate_artifact_hashes(registry, artifacts)

        self.assertIn("Source hash drift detected", str(error.exception))


if __name__ == "__main__":
    unittest.main()
