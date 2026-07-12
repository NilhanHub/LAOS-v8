#!/usr/bin/env python3
"""Safely extract a ZIP after rejecting traversal, duplicates, links, encryption and resource abuse."""
from __future__ import annotations
import argparse
import shutil
import zipfile
from pathlib import Path, PurePosixPath

MAX_ENTRIES = 100_000
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_SINGLE_BYTES = 512 * 1024 * 1024
MAX_RATIO = 10_000


def validate_name(raw: str) -> PurePosixPath:
    if not raw or "\\" in raw:
        raise ValueError(f"Unsafe ZIP member name: {raw!r}")
    p = PurePosixPath(raw)
    if p.is_absolute() or ".." in p.parts or (p.parts and ":" in p.parts[0]):
        raise ValueError(f"Unsafe ZIP member path: {raw!r}")
    return p


def safe_extract(source: Path, destination: Path) -> None:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise ValueError("ZIP entry limit exceeded")
        if sum(i.file_size for i in infos) > MAX_TOTAL_BYTES:
            raise ValueError("ZIP total uncompressed size limit exceeded")
        seen: set[str] = set()
        for info in infos:
            p = validate_name(info.filename)
            if info.filename in seen:
                raise ValueError(f"Duplicate ZIP member: {info.filename}")
            seen.add(info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if (mode & 0o170000) == 0o120000:
                raise ValueError(f"Symlink member is forbidden: {info.filename}")
            if info.flag_bits & 0x1:
                raise ValueError(f"Encrypted member is forbidden: {info.filename}")
            if info.file_size > MAX_SINGLE_BYTES:
                raise ValueError(f"Member size limit exceeded: {info.filename}")
            if info.compress_size and info.file_size > 10 * 1024 * 1024 and info.file_size / max(1, info.compress_size) > MAX_RATIO:
                raise ValueError(f"Suspicious compression ratio: {info.filename}")
            target = (destination / Path(*p.parts)).resolve()
            if target != destination and destination not in target.parents:
                raise ValueError(f"Member escapes destination: {info.filename}")
        for info in infos:
            p = validate_name(info.filename)
            target = destination / Path(*p.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_zip", type=Path)
    ap.add_argument("destination", type=Path)
    args = ap.parse_args()
    safe_extract(args.source_zip, args.destination)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
