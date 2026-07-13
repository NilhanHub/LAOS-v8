from __future__ import annotations

from pathlib import Path

from laos_v8.migration_discovery import discover_v7
from laos_v8.platform_profile import doctor, recommended_sqlite_journal_mode, sqlite_wal_reset_fix_verified

ROOT = Path(__file__).resolve().parents[2]


def test_sqlite_wal_fix_profile_is_exact_and_fail_closed() -> None:
    assert not sqlite_wal_reset_fix_verified("3.50.4")
    assert sqlite_wal_reset_fix_verified("3.50.7")
    assert sqlite_wal_reset_fix_verified("3.44.6")
    assert not sqlite_wal_reset_fix_verified("3.45.0")
    assert sqlite_wal_reset_fix_verified("3.51.3")
    assert recommended_sqlite_journal_mode("3.50.4") == "DELETE"
    assert recommended_sqlite_journal_mode("3.51.3") == "WAL"


def test_doctor_reports_no_privileged_support_claim() -> None:
    report = doctor(ROOT)
    assert report.status == "PASS"
    assert report.connected_privileged_profile_claimed is False
    if not report.sqlite_wal_reset_fix_verified:
        assert report.sqlite_journal_mode == "DELETE"


def test_v7_migration_discovery_is_read_only() -> None:
    archive = ROOT / "baseline" / "source" / "LAOS_v7.0_Complete_System(1).zip"
    report = discover_v7(archive)
    assert report["mode"] == "READ_ONLY_NO_EXTRACTION"
    assert report["entry_count"] == 155
    assert report["source_sha256"] == "661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d"
    assert report["migration_status"] == "DISCOVERY_ONLY_NOT_MIGRATED"
