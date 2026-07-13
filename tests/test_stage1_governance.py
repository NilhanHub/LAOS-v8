import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_verifier():
    path = ROOT / "scripts" / "verify_stage1.py"
    spec = importlib.util.spec_from_file_location("verify_stage1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stage1_verifier_passes():
    result = load_verifier().verify()
    assert result["status"] == "PASS"
    assert result["check_count"] >= 12


def test_fixture_ids_and_statuses_are_unique_and_open():
    fixtures = []
    for path in sorted((ROOT / "tests" / "fixtures" / "v7_regressions").glob("*.json")):
        fixtures.append(json.loads(path.read_text(encoding="utf-8")))
    assert len(fixtures) == 8
    assert len({fixture["id"] for fixture in fixtures}) == 8
    assert all(fixture["status"] == "FIXTURE_SPECIFIED_IMPLEMENTATION_OPEN" for fixture in fixtures)


def test_all_release_blockers_remain_open():
    blockers = json.loads((ROOT / "RELEASE_BLOCKERS.json").read_text(encoding="utf-8"))["blockers"]
    assert len(blockers) == 25
    assert all(blocker["status"] == "OPEN" for blocker in blockers)
    assert all(blocker["builder_write_authority"] is False for blocker in blockers)


def test_v7_fixture_observations_reproduce_without_executing_v7():
    path = ROOT / "scripts" / "reproduce_v7_fixtures.py"
    spec = importlib.util.spec_from_file_location("reproduce_v7_fixtures", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    result = module.observe()
    assert result["status"] == "PASS"
    assert result["executed_v7_code"] is False
    assert result["fixture_count"] == 8
