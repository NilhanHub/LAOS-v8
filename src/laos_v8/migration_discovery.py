"""Read-only v7 migration discovery that never extracts the sealed archive."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from .errors import ValidationError


def discover_v7(archive: Path) -> dict[str, object]:
    if not archive.is_file():
        raise ValidationError("v7 archive does not exist", code="MIGRATION_SOURCE_MISSING")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise ValidationError("v7 archive contains duplicate entries", code="MIGRATION_SOURCE_DUPLICATE_ENTRY")
        categories = {
            "runtime": sorted(name for name in names if name.endswith("laos_runtime.py")),
            "capture": sorted(name for name in names if "capture" in name.lower()),
            "blueprints": sorted(
                name for name in names if "blueprint" in name.lower() or name.endswith(".example.json")
            ),
            "evidence": sorted(name for name in names if "evidence" in name.lower()),
            "tests": sorted(name for name in names if "/tests/" in name),
        }
    return {
        "report_version": "1.0.0",
        "mode": "READ_ONLY_NO_EXTRACTION",
        "source_archive": archive.name,
        "source_sha256": digest,
        "entry_count": len(names),
        "categories": categories,
        "unknown_fields_policy": "QUARANTINE_DURING_MIGRATION",
        "migration_status": "DISCOVERY_ONLY_NOT_MIGRATED",
    }


def write_discovery(archive: Path, output: Path) -> None:
    output.write_bytes((json.dumps(discover_v7(archive), indent=2) + "\n").encode("utf-8"))
