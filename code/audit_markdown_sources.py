#!/usr/bin/env python3
"""Audit markdown citations against an allowed-domain policy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "research" / "data" / "provenance" / "report_source_policy.json"
URL_PATTERN = re.compile(r"https?://[^\s<>()\[\]{}\"]+")
TRAILING_PUNCT = ".,;:!?)]}"


@dataclass(frozen=True)
class SourceHit:
    file_path: Path
    line_no: int
    url: str
    domain: str


def _normalize_domain(domain: str) -> str:
    value = domain.lower().strip()
    if value.startswith("www."):
        value = value[4:]
    if ":" in value:
        value = value.split(":", 1)[0]
    return value


def _clean_url(raw_url: str) -> str:
    cleaned = raw_url
    while cleaned and cleaned[-1] in TRAILING_PUNCT:
        cleaned = cleaned[:-1]
    return cleaned


def extract_markdown_urls(path: Path) -> List[SourceHit]:
    hits: List[SourceHit] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in URL_PATTERN.finditer(line):
            cleaned = _clean_url(match.group(0))
            parsed = urlparse(cleaned)
            domain = _normalize_domain(parsed.netloc)
            if not domain:
                continue
            hits.append(SourceHit(file_path=path, line_no=line_no, url=cleaned, domain=domain))
    return hits


def _is_domain_allowed(domain: str, allowed_domains: Sequence[str]) -> bool:
    for allowed in allowed_domains:
        normalized = _normalize_domain(allowed)
        if domain == normalized or domain.endswith(f".{normalized}"):
            return True
    return False


def load_policy(path: Path) -> Dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "allowed_domains" not in payload or not isinstance(payload["allowed_domains"], list):
        raise ValueError(f"Policy missing allowed_domains list: {path}")
    if "targets" not in payload or not isinstance(payload["targets"], list):
        raise ValueError(f"Policy missing targets list: {path}")
    return payload


def audit_files(files: Iterable[Path], allowed_domains: Sequence[str]) -> Dict:
    total_urls = 0
    disallowed: List[SourceHit] = []
    per_file: Dict[str, Dict[str, object]] = {}

    for file_path in files:
        hits = extract_markdown_urls(file_path)
        total_urls += len(hits)
        bad = [hit for hit in hits if not _is_domain_allowed(hit.domain, allowed_domains)]
        disallowed.extend(bad)
        per_file[str(file_path)] = {
            "total_urls": len(hits),
            "disallowed_count": len(bad),
        }

    return {
        "total_urls": total_urls,
        "disallowed_count": len(disallowed),
        "disallowed": [
            {
                "file": str(hit.file_path),
                "line": hit.line_no,
                "domain": hit.domain,
                "url": hit.url,
            }
            for hit in disallowed
        ],
        "per_file": per_file,
    }


def _resolve_targets(policy: Dict, explicit_files: Sequence[str] | None) -> List[Path]:
    if explicit_files:
        return [Path(file_name).resolve() for file_name in explicit_files]

    targets: List[Path] = []
    for target in policy["targets"]:
        target_path = (ROOT / target).resolve()
        targets.append(target_path)
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit markdown source domains against policy")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY_PATH), help="Path to domain policy JSON")
    parser.add_argument("--files", nargs="*", help="Optional explicit markdown files to audit")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on policy violations")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    policy_path = Path(args.policy).resolve()
    policy = load_policy(policy_path)
    files = _resolve_targets(policy, args.files)

    for path in files:
        if not path.exists():
            raise FileNotFoundError(f"Audit target not found: {path}")

    report = audit_files(files, policy["allowed_domains"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("# Markdown Source Domain Audit")
        print(f"Policy: {policy_path}")
        print(f"Files audited: {len(files)}")
        print(f"URLs scanned: {report['total_urls']}")
        print(f"Disallowed URLs: {report['disallowed_count']}")
        for item in report["disallowed"]:
            print(f"- {item['file']}:{item['line']} -> {item['domain']} ({item['url']})")

    if args.check and report["disallowed_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
