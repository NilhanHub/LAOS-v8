from __future__ import annotations

import argparse
from pathlib import Path

from laos_v8.evidence_receipts import atomic_write_json
from laos_v8.ollama_adapter import PinnedOllamaAdapter
from laos_v8.prompting import ReleasedProfileBinding
from laos_v8.protected_signer import DockerProtectedSigner
from laos_v8.stage5_calibration import PINNED_MODEL, PINNED_SETTINGS
from laos_v8.stage5_real_capture import run_real_capture


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the no-execution Stage 5 capture of sealed LAOS v7")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    binding = ReleasedProfileBinding.model_validate_json(args.binding.read_text(encoding="utf-8"), strict=True)
    provider = PinnedOllamaAdapter(PINNED_MODEL, settings=PINNED_SETTINGS)
    provider.verify_pin()
    event_signer = DockerProtectedSigner(root, "event_anchor")
    capsule_signer = DockerProtectedSigner(root, "capsule")
    receipt = run_real_capture(
        args.archive,
        provider,
        model_identity_digest=provider.identity_digest,
        released_binding=binding,
        event_signer=event_signer,
        capsule_signer=capsule_signer,
    )
    atomic_write_json(args.output, receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
