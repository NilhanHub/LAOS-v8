#!/usr/bin/env python3
"""Verify the Milestone 0 baseline without claiming any v8 runtime capability."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys, zipfile
from pathlib import Path

REQUIRED = [
    "BASELINE_MANIFEST.json", "RECOVERY_STATE.md", "REQUIREMENTS_LEDGER.json",
    "KNOWN_DEFECTS.md", "THREAT_MODEL_DRAFT.md", "LIMITATIONS_REGISTER.md",
    "IMPLEMENTATION_STATUS.json", "Evidence/README.md", "docs/adr/0001-trust-zone-separation.md",
    "policies/RELEASE_POLICY.md", "issues/REGRESSION_CATALOG.json",
]

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1]); ap.add_argument("--report", type=Path)
    args=ap.parse_args(); root=args.root.resolve(); issues=[]; checks=[]
    for rel in REQUIRED:
        ok=(root/rel).is_file(); checks.append({"check":"required_file","path":rel,"ok":ok})
        if not ok: issues.append(f"missing required file: {rel}")
    if not (root/"Evidence").is_dir(): issues.append("root Evidence folder is missing")
    for p in root.rglob("*.json"):
        try: json.loads(p.read_text(encoding="utf-8"))
        except Exception as e: issues.append(f"invalid JSON {p.relative_to(root)}: {e}")
    status=json.loads((root/"IMPLEMENTATION_STATUS.json").read_text())
    if status.get("v8_runtime_exists") is not False or status.get("v8_release_exists") is not False:
        issues.append("implementation status incorrectly claims a v8 runtime or release")
    baseline=json.loads((root/"BASELINE_MANIFEST.json").read_text())
    archive=root/baseline["source_archive"]["preserved_copy_relative_path"]
    if not archive.is_file(): issues.append("preserved v7 archive copy is missing")
    else:
        if sha(archive)!=baseline["source_archive"]["sha256"]: issues.append("preserved v7 archive SHA-256 mismatch")
        if archive.stat().st_size!=baseline["source_archive"]["bytes"]: issues.append("preserved v7 archive size mismatch")
        with zipfile.ZipFile(archive,"r") as zf:
            info={i.filename:i for i in zf.infolist()}
            if len(info)!=baseline["source_archive"]["entry_count"]: issues.append("ZIP entry count mismatch")
            for item in baseline["entries"]:
                i=info.get(item["path"])
                if i is None: issues.append(f"ZIP member missing: {item['path']}"); continue
                h=hashlib.sha256(zf.read(i)).hexdigest()
                if h!=item["sha256"]: issues.append(f"ZIP member hash mismatch: {item['path']}")
    dm=json.loads((root/"design_inputs/DESIGN_INPUTS_MANIFEST.json").read_text())
    for item in dm["items"]:
        p=root/item["relative_path"]
        if not p.is_file() or sha(p)!=item["sha256"]: issues.append(f"design input mismatch: {item['relative_path']}")
    mutable=[p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and (p.suffix in {".sqlite",".sqlite3"} or p.name.endswith(("-wal","-shm")))]
    if mutable: issues.append("mutable runtime database files present: "+", ".join(mutable))
    ledger=json.loads((root/"REQUIREMENTS_LEDGER.json").read_text())
    defects=json.loads((root/"issues/REGRESSION_CATALOG.json").read_text())
    result={"status":"PASS" if not issues else "FAIL","root":str(root),"issues":issues,"requirement_count":ledger["requirement_count"],"regression_count":defects["count"],"source_archive_sha256":baseline["source_archive"]["sha256"],"checks":checks}
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"; print(text,end="")
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(text,encoding="utf-8")
    return 0 if not issues else 2

if __name__=="__main__": raise SystemExit(main())
