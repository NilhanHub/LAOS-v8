# Stage 4 candidate correction

The initial `stage4-review-candidate` tag at commit `6d9dda8` is retained as a failed reconstruction candidate. It unnecessarily changed the local package version from `8.0.0a3` to `8.0.0a4`, which changed `uv.lock` without the reviewed lock amendment required by the inherited Stage 2 gate.

The correction reverts only that version metadata and lockfile change. No Stage 4 control, runtime evidence, pilot result, or acceptance criterion is weakened. The corrected review tag is `stage4-review-candidate-v2`.
