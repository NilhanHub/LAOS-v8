# Stage 1 clean reconstruction

**PASS — corrected candidate reconstructed and verified from a second clean clone.**

- Source and clone HEAD: `8fac211c8e9e17c45760f34aadb42412a0c10d15`
- Clone method: `git clone --no-local` into a new temporary directory
- Working tree after verification: clean
- Tracked files: 141
- Stage 1 verifier: 14 checks passed
- Governance tests: 4 passed
- Authoritative plan SHA-256: `d8f1955b4c7c8a649cc425c9c2d3463ea25db2ead96229813d4bbb542c262729`
- Embedded v7 SHA-256: `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`

## Retained failed attempt

The first clean checkout changed the plan hash to `009c5d9ca426715a7e6e2454a1c1a75266af9791225551d5c74a2c64e56ebb0f` because global Git line-ending conversion was active. The candidate was not accepted. Commit `8fac211c8e9e17c45760f34aadb42412a0c10d15` added `.gitattributes` rules preserving the reviewed plan and review bytes. The complete clean-clone verification was then rerun and passed.

Stage 1 remains open pending Nilhan's independent review.
