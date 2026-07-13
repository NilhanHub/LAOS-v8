#!/usr/bin/env python3
"""Generate deterministic schemas, registries, transition tables, and golden vectors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from laos_v8.canonical import canonical_json, content_digest, dsse_pae
from laos_v8.errors import ERROR_CODE_REGISTRY
from laos_v8.schema_registry import export_schemas
from laos_v8.transitions import serialized_transition_tables

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def main() -> None:
    outputs = export_schemas(ROOT / "schemas" / "v1")
    write_json(
        ROOT / "schemas" / "SCHEMA_REGISTRY.json",
        {
            "registry_version": "1.0.0",
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "schemas": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for path in outputs
            ],
        },
    )
    write_json(
        ROOT / "schemas" / "ERROR_CODES.json",
        {
            "registry_version": "1.0.0",
            "codes": [{"code": code, "exception": cls.__name__} for code, cls in sorted(ERROR_CODE_REGISTRY.items())],
        },
    )
    write_json(ROOT / "schemas" / "TRANSITION_TABLES.json", serialized_transition_tables())

    vector = {"a": "é", "b": [3, 2, 1], "nested": {"false": False, "null": None, "true": True}}
    canonical = canonical_json(vector)
    payload_type = "application/vnd.nilhan.laos.golden-vector+json"
    pae = dsse_pae(payload_type, canonical)
    write_json(
        ROOT / "schemas" / "golden" / "canonicalization-v1.json",
        {
            "profile": "RFC8785-JCS",
            "input": vector,
            "canonical_utf8_hex": canonical.hex(),
            "sha256": content_digest(vector),
            "dsse_payload_type": payload_type,
            "dsse_pae_hex": pae.hex(),
        },
    )


if __name__ == "__main__":
    main()
