import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from audit_markdown_sources import audit_files, extract_markdown_urls  # noqa: E402


class MarkdownSourceAuditTests(unittest.TestCase):
    def test_extract_urls_trims_trailing_punctuation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("See https://data.worldbank.org/indicator/NE.GDI.FTOT.ZS).", encoding="utf-8")

            hits = extract_markdown_urls(path)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].url, "https://data.worldbank.org/indicator/NE.GDI.FTOT.ZS")
            self.assertEqual(hits[0].domain, "data.worldbank.org")

    def test_audit_allows_subdomains_of_allowed_root(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("API: https://api.worldbank.org/v2/country/US/indicator/SH.XPD.CHEX.GD.ZS", encoding="utf-8")

            report = audit_files([path], ["worldbank.org"])
            self.assertEqual(report["disallowed_count"], 0)

    def test_audit_flags_disallowed_domains(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("Weak source: https://statista.com/anything", encoding="utf-8")

            report = audit_files([path], ["data.worldbank.org", "ec.europa.eu"])
            self.assertEqual(report["disallowed_count"], 1)
            flagged = report["disallowed"][0]
            self.assertEqual(flagged["domain"], "statista.com")


if __name__ == "__main__":
    unittest.main()
