#!/usr/bin/env python3
"""Helpers for provenance-validated model input loading."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

PRIMARY_TIERS = {"primary_source", "official_statistic", "administrative_record"}
ALLOWED_KINDS = {"primary_source", "official_statistic", "administrative_record", "derived", "assumption"}
ASSUMPTION_CLASSES = {"common_parlance", "scenario_model", "policy_anchor", "proxy"}


def _provenance_root() -> Path:
    return Path(__file__).resolve().parents[1] / "research" / "data" / "provenance"


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r") as handle:
        return json.load(handle)


def load_source_registry() -> Dict[str, Dict[str, Any]]:
    registry_path = _provenance_root() / "primary_sources.json"
    payload = _load_json(registry_path)

    if "sources" not in payload or not isinstance(payload["sources"], list):
        raise ValueError(f"Invalid source registry format: {registry_path}")

    registry: Dict[str, Dict[str, Any]] = {}
    for source in payload["sources"]:
        source_id = source.get("id")
        if not source_id:
            raise ValueError(f"Source entry missing id: {source}")
        if source_id in registry:
            raise ValueError(f"Duplicate source id in registry: {source_id}")
        registry[source_id] = source
    return registry


def _iter_provenance_entries(node: Any, path: str = "$") -> Iterator[Tuple[str, Dict[str, Any]]]:
    if isinstance(node, dict):
        provenance = node.get("provenance")
        if isinstance(provenance, dict):
            yield path, provenance
        for key, value in node.items():
            if key == "provenance":
                continue
            child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
            yield from _iter_provenance_entries(value, child_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_provenance_entries(value, f"{path}[{index}]")


def _validate_provenance(path: str, provenance: Dict[str, Any], registry: Dict[str, Dict[str, Any]]) -> None:
    kind = provenance.get("kind")
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"Invalid provenance kind at {path}: {kind}")

    if kind in PRIMARY_TIERS:
        source_id = provenance.get("source_id")
        if not source_id:
            raise ValueError(f"Missing source_id at {path} for primary provenance kind")
        source = registry.get(source_id)
        if not source:
            raise ValueError(f"Unknown source_id at {path}: {source_id}")
        if source.get("tier") not in PRIMARY_TIERS:
            raise ValueError(f"Non-primary source tier used at {path}: {source_id}")
        return

    if kind == "derived":
        source_ids = provenance.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError(f"Derived provenance must include source_ids at {path}")
        for source_id in source_ids:
            source = registry.get(source_id)
            if not source:
                raise ValueError(f"Unknown source_id at {path}: {source_id}")
            if source.get("tier") not in PRIMARY_TIERS:
                raise ValueError(f"Derived provenance requires primary/official sources at {path}: {source_id}")
        if not provenance.get("method"):
            raise ValueError(f"Derived provenance missing method at {path}")
        return

    if kind == "assumption" and not provenance.get("assumption_basis"):
        raise ValueError(f"Assumption provenance missing assumption_basis at {path}")
    if kind == "assumption":
        assumption_class = provenance.get("assumption_class")
        if assumption_class not in ASSUMPTION_CLASSES:
            raise ValueError(
                f"Assumption provenance must include valid assumption_class at {path}; "
                f"allowed={sorted(ASSUMPTION_CLASSES)}"
            )
    if kind == "assumption" and "source_ids" in provenance:
        source_ids = provenance.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError(f"Assumption provenance source_ids must be a non-empty list at {path}")
        for source_id in source_ids:
            if source_id not in registry:
                raise ValueError(f"Unknown source_id at {path}: {source_id}")


def load_model_inputs(model_name: str) -> Dict[str, Any]:
    file_name = model_name if model_name.endswith(".json") else f"{model_name}.json"
    input_path = _provenance_root() / "model_inputs" / file_name
    payload = _load_json(input_path)

    registry = load_source_registry()
    entries = list(_iter_provenance_entries(payload))
    if not entries:
        raise ValueError(f"No provenance entries found in model input file: {input_path}")

    for path, provenance in entries:
        _validate_provenance(path, provenance, registry)

    if file_name.endswith("_inputs.json") and "generated" not in payload:
        raise ValueError(
            f"Model input file missing generated metadata: {input_path}. "
            "Run `python3 code/build_provenance_inputs.py --refresh-sources`."
        )

    return payload


def record_run(script_name: str, input_files: list[str], output_files: list[str]) -> None:
    """Append a run record linking script execution to concrete inputs and outputs."""
    if os.getenv("PROVENANCE_DISABLE_RUN_RECORD", "").strip().lower() in {"1", "true", "yes"}:
        return

    manifest_path = _provenance_root() / "run_manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
    else:
        manifest = {"version": "1.0", "runs": []}

    manifest.setdefault("runs", []).append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": script_name,
            "input_files": input_files,
            "output_files": output_files,
        }
    )

    with open(manifest_path, "w") as handle:
        json.dump(manifest, handle, indent=2)
