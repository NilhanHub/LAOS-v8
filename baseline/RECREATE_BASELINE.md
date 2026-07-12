# Recreate the v7 reference baseline

1. Obtain the exact source archive with SHA-256 `661445d68a2f44ef0434d9c7b71954b1974e45af625a920ab7dcf72ecf6e1b6d`.
2. Place it at any local path; do not modify it.
3. Verify the hash before extraction.
4. Run:

```bash
python scripts/safe_extract.py /full/path/to/LAOS_v7.0_Complete_System\(1\).zip /full/path/to/clean/reference-directory
```

5. Compare every extracted member to `BASELINE_MANIFEST.json`.
6. Run the v7 tests only inside the clean reference directory. Do not build v8 inside it.

The read-only preserved copy at `baseline/source/LAOS_v7.0_Complete_System(1).zip` is byte-identical to the original source present when Milestone 0 was created.
