#!/usr/bin/env python3
"""Run the fixed-seed, development-only Stage 4 four-condition pilot."""

from __future__ import annotations

import argparse
import json
import random
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from laos_v8.alpha import parse_bounded_proposal, proposal_prompt
from laos_v8.model_broker import LocalOnlyModelBroker, ModelCallRequest
from laos_v8.ollama_adapter import OllamaModelPin, PinnedOllamaAdapter
from laos_v8.policy import ResourceBudget
from laos_v8.sandbox import DockerSandbox, SandboxRequest

MODEL_TAG = "qwen2.5-coder:1.5b"
MODEL_BLOB = "29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104"
SEED = 80401
CONDITIONS = ("broad_prompt", "resource_matched_structured_prompt", "v7_prompt", "alpha_trust_slice")


@dataclass(frozen=True, slots=True)
class PilotTask:
    task_id: str
    source: str
    exact: str
    tests: str


TASKS = (
    PilotTask(
        "addition",
        "def add(a: int, b: int) -> int:\n    return a - b\n",
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        "import sys\nimport unittest\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
        "from app import add\n"
        "class T(unittest.TestCase):\n"
        "    def test_cases(self):\n"
        "        self.assertEqual(add(7, 5), 12)\n"
        "        self.assertEqual(add(-4, 9), 5)\n",
    ),
    PilotTask(
        "parity",
        "def is_even(value: int) -> bool:\n    return value % 2 == 1\n",
        "def is_even(value: int) -> bool:\n    return value % 2 == 0\n",
        "import sys\nimport unittest\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))\n"
        "from app import is_even\n"
        "class T(unittest.TestCase):\n"
        "    def test_cases(self):\n"
        "        self.assertTrue(is_even(0))\n"
        "        self.assertTrue(is_even(-4))\n"
        "        self.assertFalse(is_even(9))\n",
    ),
)


def instruction(condition: str, task: PilotTask) -> str:
    path = "src/app.py"
    if condition == "broad_prompt":
        task_text = "Fix the obvious logic bug in src/app.py and return the complete corrected file."
    elif condition == "resource_matched_structured_prompt":
        task_text = (
            "Correct the logic defect in src/app.py. Preserve its function signature. Change only src/app.py. "
            "Return the complete corrected file, not a fragment."
        )
    elif condition == "v7_prompt":
        task_text = (
            "You are the LAOS v7 Builder. Implement only the exact legal task; do not modify tests or expand scope. "
            "Correct the logic defect in src/app.py, return the complete file, and leave verification to the reviewer."
        )
    else:
        escaped = task.exact.replace("\n", "\\n")
        task_text = f"Change only src/app.py. Set the replacement to exactly this complete source: {escaped}"
    return proposal_prompt(task_text, task.source, allowed_path=path)


def evaluate(sandbox: DockerSandbox, source: str, tests: str, root: Path) -> bool:
    (root / "src").mkdir(parents=True)
    (root / "protected_tests").mkdir()
    (root / "src/app.py").write_text(source, encoding="utf-8", newline="\n")
    (root / "protected_tests/test_acceptance.py").write_text(tests, encoding="utf-8", newline="\n")
    result = sandbox.run(
        SandboxRequest(
            ("python", "-m", "unittest", "discover", "-s", "protected_tests", "-v"),
            root,
            ResourceBudget(timeout_seconds=60, memory_bytes=268_435_456, processes=32, output_bytes=1_048_576),
        )
    )
    return result.exit_code == 0


def run(output: Path, ollama_executable: str | None) -> dict[str, object]:
    if output.exists():
        raise RuntimeError(f"output already exists: {output}")
    adapter = PinnedOllamaAdapter(OllamaModelPin(MODEL_TAG, MODEL_BLOB), executable=ollama_executable)
    broker = LocalOnlyModelBroker(adapter)
    sandbox = DockerSandbox()
    available, detail = sandbox.availability()
    if not available:
        raise RuntimeError(f"qualifying sandbox unavailable: {detail}")
    trials = [(task, condition) for task in TASKS for condition in CONDITIONS]
    random.Random(SEED).shuffle(trials)  # noqa: S311 - reproducible experiment assignment, not cryptography
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="laos-stage4-pilot-") as temporary:
        root = Path(temporary)
        for index, (task, condition) in enumerate(trials):
            prompt = instruction(condition, task)
            started = time.perf_counter()
            result = broker.invoke(
                ModelCallRequest(
                    prompt,
                    ("Development fixture; no tools or external actions are authorized.",),
                    (task.source,),
                )
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            contract_valid = True
            criterion_pass = False
            error_code = None
            try:
                proposal = parse_bounded_proposal(result.output, allowed_path="src/app.py")
                criterion_pass = evaluate(sandbox, proposal.replacement, task.tests, root / f"trial-{index}")
            except Exception as exc:
                contract_valid = False
                error_code = getattr(exc, "code", type(exc).__name__)
            records.append(
                {
                    "condition": condition,
                    "contract_valid": contract_valid,
                    "criterion_pass": criterion_pass,
                    "elapsed_ms": elapsed_ms,
                    "error_code": error_code,
                    "model_request_digest": result.request_digest,
                    "output_bytes": len(result.output.encode("utf-8")),
                    "task_id": task.task_id,
                    "trial_order": index,
                }
            )
    summary = {
        condition: {
            "criterion_passes": sum(1 for row in records if row["condition"] == condition and row["criterion_pass"]),
            "trials": sum(1 for row in records if row["condition"] == condition),
        }
        for condition in CONDITIONS
    }
    report: dict[str, object] = {
        "assurance": "DEVELOPMENT_PILOT_ONLY_NOT_FINAL_EFFICACY",
        "assignment": "blocked by task then fixed-seed randomized execution order",
        "model_blob_sha256": MODEL_BLOB,
        "records": records,
        "seed": SEED,
        "summary": summary,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ollama-executable")
    args = parser.parse_args()
    print(json.dumps(run(args.output.resolve(), args.ollama_executable), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
