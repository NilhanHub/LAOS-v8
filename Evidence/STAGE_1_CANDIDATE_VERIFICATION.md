# Stage 1 candidate verification

**PASS — implementation candidate created; Nilhan review remains pending.**

The first subsequent clean checkout exposed line-ending conversion of the authoritative plan. Commit `8fac211c8e9e17c45760f34aadb42412a0c10d15` added byte-preservation attributes. The corrected clean-clone result is recorded in `Evidence/STAGE_1_CLEAN_RECONSTRUCTION.json`.

- Assurance: `BOOTSTRAP`
- Verified content tree: `72a54a660bb87374b606d7849178f16f518fb298`
- Stage 0 tag target: `9a98570803b78e29dada15ae7ee9f84feaf05284`
- Candidate files changed/added: `44`
- Fixture-only v7 path: `true`
- v7.0.1 release claimed: `false`
- v8 runtime implemented: `false`
- v8 release published: `false`

## Verification

- `C:\Users\Nilhan.dev\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe scripts/reproduce_v7_fixtures.py`: exit `0`
- `C:\Users\Nilhan.dev\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe scripts/verify_stage1.py`: exit `0`
- `C:\Users\Nilhan.dev\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pytest tests/test_stage1_governance.py -q`: exit `0`
- `C:\Users\Nilhan.dev\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m compileall -q scripts tests`: exit `0`

All seven Stage 0 internal package checksums matched. The original and embedded v7 archives remain byte-identical. All 25 release blockers remain open.

## Review boundary

Codex cannot independently approve its own candidate. Stage 1 remains open until Nilhan reviews this evidence and the candidate diff. A completion tag must not be created before that approval.
