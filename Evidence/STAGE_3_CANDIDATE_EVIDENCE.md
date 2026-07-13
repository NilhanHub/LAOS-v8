# LAOS v8 Stage 3 review-candidate evidence

Status: **PASS_AWAITING_NILHAN_REVIEW**

- Reconstructed commit: `6e0f84dae644c245011cc1d05354b1fe65a1a767`
- Reconstructed tree: `bd289ebe5ccb94ee5758258efeda0a8378d17252`
- Clean after gates: `True`
- Assurance: `BOOTSTRAP_NOT_PRODUCTION_SIGNING`
- Independent reviewer: Nilhan
- The local Security Spine test profile is implemented.
- All 25 release blockers remain open.
- No real weaker agent, complete v8 runtime, production signing, or v8 release is claimed.

## Gate results

- `sync --frozen`: **PASS** (exit 0)
- `run --frozen ruff check src tests/stage2 tests/stage3 scripts/generate_stage3_evidence.py scripts/reconcile_stage3_records.py scripts/verify_stage2.py scripts/verify_stage3.py scripts/build_stage3_candidate_evidence.py`: **PASS** (exit 0)
- `run --frozen mypy`: **PASS** (exit 0)
- `run --frozen pytest -q`: **PASS** (exit 0)
- `run --frozen python scripts/generate_stage3_evidence.py`: **PASS** (exit 0)
- `run --frozen python scripts/verify_stage1.py`: **PASS** (exit 0)
- `run --frozen python scripts/verify_stage2.py`: **PASS** (exit 0)
- `run --frozen python scripts/verify_stage3.py`: **PASS** (exit 0)
- `build`: **PASS** (exit 0)

## Hashed artifacts

- `LAOS_v8_EXECUTION_AND_RELEASE_PLAN.md`: `d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729`
- `uv.lock`: `3f0cc1751cbee98763cba58a6e0f6211fb49bd2772562a95bf6016224fd537ed`
- `docs/STAGE_3_ENFORCEMENT_CONTRACT.md`: `86f7dacef51090cb23aee356ad6de34b6ea1c0e7259ee2c38bc0e762a91b2a7c`
- `docs/STAGE_3_OPERATOR_PATHS.md`: `01dd01df1fc5ffcbf676d808600febfa4d845a4803c5d9cb28216c5dc4f34f3c`
- `SANDBOX_PROFILE.json`: `9365717818430ba5edc86f88726dd5633e1d5152a2dfde20623e72b6956e14e1`
- `PERMISSION_ENFORCEMENT_MATRIX.json`: `87388b664b2bb417e3afbd936c52d1c0ddfdeb3cb06197abdcc4bfacd8f52e20`
- `STAGE_3_THREAT_COVERAGE.json`: `d54dcbd6beabd20dd3e856e75179da8729cb9180b7cab44cbb9aa530711734c0`
- `Evidence/STAGE_3_LOCAL_SECURITY_PROFILE.json`: `630d5854a2c7d83af208c6a4a37ba87605031892b93b52bcd6eca0faf1ea3606`
- `Evidence/STAGE_3_VERIFICATION.json`: `c2b4c5aa2f7a2f403f5eb89bb99b397b5887ee28b11908bd1df6b95d00dfa25f`
- `baseline/source/LAOS_v7.0_Complete_System(1).zip`: `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`
- `dist/laos_v8-8.0.0a3.tar.gz`: `cfa9c9baf8d685e98c752170045fad00148130f3cd44bcd030b29a328d4ca0aa`
- `dist/laos_v8-8.0.0a3-py3-none-any.whl`: `c1f14c96a419676d81830e2c3c271177306535ebcab218c2ad5d748283ffaf85`
