# LAOS v7 test baseline

Recorded: `2026-07-12T16:10:01+00:00`  
Source archive SHA-256: `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`

## Result

- Shipped tests discovered: **14**
- Passed in isolated subprocesses: **14**
- Failed: **0**
- Timed out individually: **0**
- JSON files parsed successfully in the independent static scan: **38**
- Python source files compiled successfully in the independent static scan: **11**
- Existing v7 content-integrity entries independently verified: **154**

The all-in-one validator was not used as evidence of a full pass because it exceeded the available long-running command window. The 14 shipped tests were instead executed separately with exact output captured in `V7_TEST_BASELINE.json`.
