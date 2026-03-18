#!/usr/bin/env python3
"""Generate a claim-level traceability map from model-input provenance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
PROV_DIR = ROOT / "research" / "data" / "provenance"
MODEL_INPUT_DIR = PROV_DIR / "model_inputs"
CATALOG_PATH = PROV_DIR / "claims_catalog.json"
OUTPUT_PATH = PROV_DIR / "CLAIM_TRACEABILITY.md"


def _parse_json_path(path: str) -> List[Tuple[str, Any]]:
    if not path.startswith("$"):
        raise ValueError(f"Invalid JSON path: {path}")
    tokens: List[Tuple[str, Any]] = []
    for key, index in re.findall(r"\.([A-Za-z0-9_]+)|\[(\d+)\]", path):
        if key:
            tokens.append(("key", key))
        else:
            tokens.append(("index", int(index)))
    return tokens


def _get_by_path(payload: Any, path: str) -> Any:
    node = payload
    for kind, token in _parse_json_path(path):
        if kind == "key":
            node = node[token]
        else:
            node = node[token]
    return node


def _find_nearest_provenance(payload: Any, path: str) -> Tuple[str | None, dict | None]:
    tokens = _parse_json_path(path)
    node = payload
    traversed: list[tuple[str, Any]] = [("$", node)]
    rendered_path = "$"
    for kind, token in tokens:
        if kind == "key":
            node = node[token]
            rendered_path = f"{rendered_path}.{token}" if rendered_path != "$" else f"$.{token}"
        else:
            node = node[token]
            rendered_path = f"{rendered_path}[{token}]"
        traversed.append((rendered_path, node))

    for candidate_path, candidate_node in reversed(traversed):
        if isinstance(candidate_node, dict) and isinstance(candidate_node.get("provenance"), dict):
            return candidate_path, candidate_node["provenance"]
    return None, None


def _format_sources(provenance: dict) -> str:
    if "source_ids" in provenance:
        return ", ".join(provenance["source_ids"])
    if "source_id" in provenance:
        return provenance["source_id"]
    return "-"


def _format_trace(provenance: dict) -> str:
    kind = provenance.get("kind", "")
    if kind == "assumption":
        return provenance.get("assumption_basis", "")
    return provenance.get("method", "")


def _sanitize_cell(text: Any) -> str:
    return str(text).replace("\n", " ").replace("|", "\\|")


def build_traceability_markdown() -> str:
    catalog = json.loads(CATALOG_PATH.read_text())
    lines = [
        "# Claim Traceability",
        "",
        "This map links published claims to concrete model-input paths and provenance blocks.",
        "",
        "| Claim ID | Description | Value | Kind | Sources | Trace | Model Path | Published Locations |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for claim in sorted(catalog["claims"], key=lambda item: item["id"]):
        model_file = claim["model_input_file"]
        payload = json.loads((MODEL_INPUT_DIR / model_file).read_text())
        value = _get_by_path(payload, claim["value_path"])
        if "provenance_path" in claim:
            provenance_node = _get_by_path(payload, claim["provenance_path"])
            provenance = provenance_node["provenance"] if isinstance(provenance_node, dict) else provenance_node
            provenance_path = claim["provenance_path"]
        else:
            provenance_path, provenance = _find_nearest_provenance(payload, claim["value_path"])
            if provenance is None:
                raise ValueError(f"No provenance found for claim path: {claim['value_path']}")

        kind = provenance.get("kind", "")
        sources = _format_sources(provenance)
        trace = _format_trace(provenance)
        locations = "; ".join(claim.get("published_locations", []))
        model_path = f"{model_file}:{claim['value_path']} @ {provenance_path}"
        lines.append(
            "| "
            + " | ".join(
                _sanitize_cell(cell)
                for cell in [
                    claim["id"],
                    claim["description"],
                    value,
                    kind,
                    sources,
                    trace,
                    model_path,
                    locations,
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append(
        "Source registry: `research/data/provenance/primary_sources.json` | "
        "Assumption register: `research/data/provenance/ASSUMPTION_REGISTER.md`"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build claim-level traceability markdown")
    parser.add_argument("--check", action="store_true", help="Fail if generated output differs from checked-in file")
    args = parser.parse_args()

    output = build_traceability_markdown()
    if args.check:
        current = OUTPUT_PATH.read_text() if OUTPUT_PATH.exists() else ""
        if current != output:
            raise SystemExit(
                "Claim traceability is out of date. Run `python3 code/build_claim_traceability.py` and commit changes."
            )
        print("Claim traceability check passed")
        return

    OUTPUT_PATH.write_text(output)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
