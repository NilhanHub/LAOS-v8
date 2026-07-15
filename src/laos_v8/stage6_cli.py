"""Stage 6 operator commands kept separate from the compatibility CLI surface."""

from __future__ import annotations

import argparse
import base64
import json
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .criterion_closure import CriterionController, CriterionState
from .errors import SecurityError, ValidationError
from .evidence_custody import DockerEvidenceCustodian
from .policy import ResourceBudget
from .protected_checks import ProtectedCheckStore
from .protected_review import ProtectedReviewVerifier, ReviewCapsule, ReviewChallenge, ReviewerKeyManager
from .protected_signer import DockerProtectedSigner
from .safe_paths import SafeRoot
from .sandbox import CommandSpec, DockerSandbox
from .state import CanonicalState

COMMANDS = frozenset(
    {
        "sandbox-doctor",
        "sandbox-conformance",
        "evidence-custodian-build",
        "evidence-custodian-bootstrap",
        "evidence-custodian-doctor",
        "evidence-custody-export",
        "evidence-custody-purge",
        "evidence-custody-reconcile-purges",
        "check-bundle-provision",
        "check-bundle-verify",
        "criterion-status",
        "criterion-close",
        "reviewer-enroll",
        "review-challenge",
        "review-sign",
        "review-verify",
    }
)


def configure(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    commands.add_parser("sandbox-doctor")
    commands.add_parser("sandbox-conformance")
    commands.add_parser("evidence-custodian-build")
    commands.add_parser("evidence-custodian-bootstrap")
    commands.add_parser("evidence-custodian-doctor")
    export = commands.add_parser("evidence-custody-export")
    export.add_argument("object_id")
    export.add_argument("destination")
    purge = commands.add_parser("evidence-custody-purge")
    purge.add_argument("object_id")
    purge.add_argument("--reason-digest", required=True)
    commands.add_parser("evidence-custody-reconcile-purges")
    provision = commands.add_parser("check-bundle-provision")
    provision.add_argument("store")
    provision.add_argument("files", nargs="+")
    provision.add_argument("--argv-json", required=True)
    provision.add_argument("--issuer", default="control:stage6")
    provision.add_argument("--audience", default="verifier:clean")
    verify = commands.add_parser("check-bundle-verify")
    verify.add_argument("store")
    verify.add_argument("bundle_id")
    verify.add_argument("--issuer", default="control:stage6")
    verify.add_argument("--audience", default="verifier:clean")
    status = commands.add_parser("criterion-status")
    status.add_argument("state")
    status.add_argument("criterion_id")
    close = commands.add_parser("criterion-close")
    close.add_argument("state")
    close.add_argument("criterion_id")
    close.add_argument("target", choices=tuple(item.value for item in CriterionState))
    close.add_argument("--actor", required=True)
    close.add_argument("--verification-digest")
    close.add_argument("--review-digest")
    close.add_argument("--promotion-digest")
    enroll = commands.add_parser("reviewer-enroll")
    enroll.add_argument("--key-path")
    challenge = commands.add_parser("review-challenge")
    challenge.add_argument("capsule")
    challenge.add_argument("output")
    sign = commands.add_parser("review-sign")
    sign.add_argument("challenge")
    sign.add_argument("--key-path")
    verify_review = commands.add_parser("review-verify")
    verify_review.add_argument("challenge")
    verify_review.add_argument("signature")
    verify_review.add_argument("public_key")
    verify_review.add_argument("verdicts")
    verify_review.add_argument("output")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _custodian(root: Path) -> DockerEvidenceCustodian:
    return DockerEvidenceCustodian(root)


def _write_new_json(path: Path, value: Any) -> None:
    destination = path.resolve(strict=False)
    if destination.exists():
        raise ValidationError("output path must be new", code="STAGE6_OUTPUT_EXISTS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    safe = SafeRoot(destination.parent)
    safe.write_bytes_atomic(destination.name, canonical_json(value) + b"\n", max_bytes=10_000_000)


def _sandbox_conformance() -> dict[str, object]:
    script = (
        "import pathlib,socket,sys\n"
        "denied=0\n"
        "try:pathlib.Path('/workspace/forbidden').write_text('x')\n"
        "except OSError:denied+=1\n"
        "try:socket.create_connection(('1.1.1.1',53),0.5)\n"
        "except OSError:denied+=1\n"
        "print('denials',denied)\n"
        "sys.exit(0 if denied==2 else 9)\n"
    )
    with tempfile.TemporaryDirectory(prefix="laos-sandbox-conformance-") as temporary:
        workspace = Path(temporary)
        result = DockerSandbox().run_spec(
            CommandSpec(
                argv=("python", "-c", script),
                workspace=workspace,
                budget=ResourceBudget(timeout_seconds=30, memory_bytes=134_217_728, processes=16, output_bytes=4096),
            )
        )
    if result.exit_code:
        raise SecurityError("sandbox conformance test failed", code="SANDBOX_CONFORMANCE_FAILED")
    return {
        "status": "PASS",
        "provider": result.provider,
        "image": result.image,
        "source_write": "DENIED",
        "network": "DENIED",
        "host_fallback": "DENIED",
        "stdout_digest": result.stdout_digest,
    }


def handle(args: argparse.Namespace, root: Path) -> int | None:
    command = str(args.command)
    if command not in COMMANDS:
        return None
    if command == "sandbox-doctor":
        readiness = DockerSandbox().ensure_available()
        output: object = {
            "status": "PASS",
            "readiness": asdict(readiness),
            "profile": DockerSandbox.assurance_profile.model_dump(),
        }
    elif command == "sandbox-conformance":
        output = _sandbox_conformance()
    elif command == "evidence-custodian-build":
        output = {"status": "PASS", "image_id": DockerEvidenceCustodian.build_image(root)}
    elif command == "evidence-custodian-bootstrap":
        output = _custodian(root).bootstrap()
    elif command == "evidence-custodian-doctor":
        output = _custodian(root).doctor()
    elif command == "evidence-custody-export":
        payload = _custodian(root).fetch(args.object_id)
        destination = Path(args.destination).resolve(strict=False)
        if destination.exists():
            raise ValidationError("evidence export destination must be new", code="EVIDENCE_EXPORT_EXISTS")
        destination.mkdir(parents=True)
        SafeRoot(destination).write_bytes_atomic("object.bin", payload, max_bytes=2_000_000)
        output = {"status": "PASS", "object_id": args.object_id, "destination": str(destination)}
    elif command == "evidence-custody-purge":
        output = _custodian(root).purge(args.object_id, reason_digest=args.reason_digest).model_dump(mode="json")
    elif command == "evidence-custody-reconcile-purges":
        output = {"status": "PASS", **_custodian(root).reconcile_purges()}
    elif command == "check-bundle-provision":
        argv_value: Any = json.loads(args.argv_json)
        if not isinstance(argv_value, list) or any(not isinstance(item, str) for item in argv_value):
            raise ValidationError("protected check argv is invalid", code="PROTECTED_CHECK_ARGV_INVALID")
        signer = DockerProtectedSigner(root, "event_anchor")
        output = ProtectedCheckStore(Path(args.store)).provision(
            tuple(Path(item) for item in args.files),
            argv=tuple(argv_value),
            signer=signer,
            issuer=args.issuer,
            audience=args.audience,
            issued_at=_now(),
        ).model_dump(mode="json")
    elif command == "check-bundle-verify":
        signer = DockerProtectedSigner(root, "event_anchor")
        output = ProtectedCheckStore(Path(args.store)).verify(
            args.bundle_id,
            trust=signer.trust_root,
            expected_issuer=args.issuer,
            expected_audience=args.audience,
        ).model_dump(mode="json")
    elif command == "criterion-status":
        with CanonicalState(Path(args.state)) as state:
            aggregate = state.get_aggregate(args.criterion_id)
        output = asdict(aggregate)
    elif command == "criterion-close":
        with CanonicalState(Path(args.state)) as state:
            controller = CriterionController(state)
            current = state.get_aggregate(args.criterion_id)
            aggregate = controller.advance(
                current,
                CriterionState(args.target),
                actor_id=args.actor,
                verification_digest=args.verification_digest,
                review_digest=args.review_digest,
                promotion_digest=args.promotion_digest,
            )
        output = asdict(aggregate)
    elif command == "reviewer-enroll":
        public = ReviewerKeyManager(Path(args.key_path) if args.key_path else None).enroll_interactive()
        output = {"status": "PASS", "public_key": str(public), "private_key_exported": False}
    elif command == "review-challenge":
        capsule = ReviewCapsule.model_validate_json(Path(args.capsule).read_bytes(), strict=True)
        challenge = ReviewChallenge.issue(capsule, now=datetime.now(UTC), lifetime=timedelta(minutes=15))
        _write_new_json(Path(args.output), challenge)
        output = {"status": "PASS", "challenge_id": challenge.challenge_id, "output": str(Path(args.output))}
    elif command == "review-sign":
        challenge_path = Path(args.challenge).resolve(strict=True)
        ReviewChallenge.model_validate_json(challenge_path.read_bytes(), strict=True)
        signature = ReviewerKeyManager(Path(args.key_path) if args.key_path else None).sign_interactive(challenge_path)
        output = {"status": "PASS", "signature": str(signature)}
    else:
        challenge = ReviewChallenge.model_validate_json(Path(args.challenge).read_bytes(), strict=True)
        signature_b64 = base64.b64encode(Path(args.signature).read_bytes()).decode("ascii")
        verdicts = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))
        if not isinstance(verdicts, dict):
            raise ValidationError("review verdicts are invalid", code="REVIEW_VERDICTS_INVALID")
        verifier = ProtectedReviewVerifier(
            "nilhan",
            Path(args.public_key).read_text(encoding="utf-8"),
            registry_path=root / "runtime_state" / "review-challenges.json",
        )
        record = verifier.verify_and_record(challenge, signature_b64, verdicts=verdicts, now=datetime.now(UTC))
        _write_new_json(Path(args.output), record)
        output = {"status": "PASS", "review_id": record.review_id, "output": str(Path(args.output))}
    print(json.dumps(output, indent=2, default=str))
    return 0
