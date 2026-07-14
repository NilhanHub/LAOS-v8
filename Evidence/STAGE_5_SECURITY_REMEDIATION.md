# LAOS v8 Stage 5 security-remediation evidence

Status: **PASS_AWAITING_NILHAN_REVIEW**

This is a security-remediation review candidate, not Stage 5 completion, v8
runtime completion, production signing, or a release claim. Nilhan remains the
sole human reviewer. The three existing Stage 5 product gates remain open.

## Source and clean reconstruction

- Vulnerable scan source: `5f9babd281a4080653986f237bb3af89dcccf4b5`
- First remediation commit scanned: `2e213deb096382151206c035a5f1143687002fcc`
- Final remediated source commit: `80755d39cf4e679b9424b2d599f10975d9f84a25`
- Final remediated source tree: `d5db7f72367e6fabb9b76fddf4a373c0be9d17b0`
- Candidate run: `run:96a88d7e4f034629a17c459bc7c4f967`
- Candidate receipt: `Evidence/STAGE_5_SECURITY_REMEDIATION_CANDIDATE.json`
- Candidate receipt SHA-256:
  `7cc8e313c8e9c02536511200456b026e6ff33d53877f9e68c6cb03a6b3a67080`
- Active Revision 1.1 plan SHA-256:
  `d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729`

The candidate was built from a separate clean clone of the committed source.
All 12 exact run-bound command arrays returned exit code 0. Docker integration
executed and was not skipped. The receipt records only command arrays, exit
codes, byte counts, and sanitized transcript hashes; it does not store command
output or secrets.

The receipt explicitly states
`producer_authentication=NONE_STAGE6_OPEN` and assurance
`BOOTSTRAP_BUILDER_ASSERTED_NOT_AUTHENTICATED_NOT_PRODUCTION_SIGNING`.
It is inspectable bootstrap evidence, not protected producer attestation and
not Nilhan approval.

## Validated finding disposition

| Finding | Former acceptance condition | Current regression result |
|---|---|---|
| `LAOS-S5-F-001` | Unsigned issuer/audience/time fields could be changed without resigning | Protected-envelope v2 authenticates the full statement; retained signatures fail with `SIGNATURE_INVALID`; v1 is denied. |
| `LAOS-S5-F-002` | A key registered to one issuer could claim another | Trust-created verifier denies the claim with `TRUST_ISSUER_MISMATCH`. |
| `LAOS-S5-F-003` | `.GIT/config` could install a Git clean filter on Windows | Case-folded control paths, aliases, collisions, and ambiguous names are denied; inherited Git config and hooks are disabled. |
| `LAOS-S5-F-004` | Far-future capture facts appeared fresh | Shared chronology validation denies excessive future skew with `CAPTURE_FACT_IN_FUTURE` and invalid ordering with stable codes. |
| `LAOS-S5-F-005` | A failed current Stage 3 run could leave an older PASS | `IN_PROGRESS` is published first and every injected failure atomically replaces the prior record with `FAIL`; current verification requires run/source identity. |
| `LAOS-S5-F-006` | Mutable repository assertions could stand in for current evidence | Docker is checked live; candidate evidence binds source, commands, timestamps, transcript hashes, and exact artifact hashes; approval remains Nilhan-only. |
| `LAOS-S5-F-007` | A duplicate row could replace an omitted Stage 5 criterion | The verifier requires the exact unique `S5-01`–`S5-14` map, milestone/status pairs, and active-plan hash. |

The original safe reproductions for findings 1, 2, 3, 4, and 7 now terminate at
their denial boundaries. The scan PoCs for findings 5 and 6 copied or invoked an
older isolated verifier shape and no longer execute unchanged; equivalent
failure-injection and evidence-substitution regressions exercise their original
acceptance conditions directly. This limitation is recorded rather than
misstating those two older harnesses as unchanged PASS tests.

The seven deferred scan candidates remain documented and unpatched. No result
in this record promotes an unvalidated candidate into a defect.

## Focused remediation-diff scan

Codex Security scan `4cd2f0cd-fbf4-4dd1-af41-5d94bd451ecb` reviewed the exact
range `5f9babd..2e213deb`. It reported ten follow-up findings: five Medium/P2
and five Low/P3. One additional local developer-host execution candidate was
excluded from the final findings because no lower-privilege path was established;
`RB-013` remains open for Stage 6. The exactly-300-second positive-skew case was
confirmed as the approved policy; 301 seconds remains denied.

| Candidate | Remediated acceptance condition | Regression result |
|---|---|---|
| `CAND-001` | Ordinary JSON could impersonate Nilhan and approve | Structural tag/source/blob binding is checked, then approval fails closed until protected Nilhan authentication exists. |
| `CAND-002` | Invented command rows could claim PASS | The exact ordered, run-bound argument map is mandatory and the receipt declares its unauthenticated producer boundary. |
| `CAND-004` | Substring filtering hid unrelated dirty files | NUL-delimited Git status paths are compared exactly. |
| `CAND-005` | Receipt output could overwrite a hashed package | Repository output is restricted to one exact untracked Evidence path; retained artifacts cannot collide. |
| `CAND-006` | Dirty bytes were attributed to clean Git IDs | Current generation and verification require a clean source worktree and external evidence paths. |
| `CAND-007` | Hand-authored collector rows passed current verification | Full current verification regenerates all Stage 3 evidence first. |
| `CAND-008` | Very old evidence still counted as current | Current evidence has a 15-minute maximum age and is regenerated immediately. |
| `CAND-009` | Claimed package artifacts were never verified | Ephemeral packages are no longer claimed as retained evidence; exact `uv build` remains a command gate. |
| `CAND-010` | An unrelated tagged commit could be reviewed | The evidence commit must have the source commit as its sole parent and contain the exact receipt blob. |
| `CAND-011` | Signed capture events could predate their request | Request issuance is a lower chronology bound in validation and continuation. |

## Verification gates

The clean reconstruction recorded PASS for:

1. frozen dependency synchronization;
2. changed-scope Ruff;
3. strict mypy;
4. the full pytest suite (`159 passed`);
5. Docker integration with no skip;
6. current run-bound Stage 3 evidence generation and verification;
7. Stage 1, 2, 3, 4, and 5 verifiers;
8. source and wheel package builds; and
9. the focused original and follow-up security regression suite (`76 passed`),
   including `24 passed` in the dedicated evidence-integrity and capture-security files.

The repository-wide Ruff audit still reports the previously recorded 107
diagnostics and introduces no additional diagnostic. That historical baseline
is not silently represented as a clean repository-wide Ruff result.

## Package-build boundary

`uv build` passed in the clean reconstruction. Its temporary source and wheel
outputs are deliberately not listed as retained candidate artifacts because
Stage 8 release custody, provenance, SBOM, reproducibility, and durable
retrieval are still open. No package or v8 release is claimed here.

## Open boundaries

- Protected production signing custody is not implemented.
- Released-profile real calibration is not complete.
- A real weaker-investigator capture round trip is not complete.
- Stage 6 protected evidence custody and external anchoring remain open.
- No `APPROVED` receipt exists until Nilhan separately reviews this candidate.
