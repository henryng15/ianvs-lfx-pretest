Follow-up to my earlier review: the claim I made statically — that the two `yaoba`
Examples this PR retires are unrunnable and that nothing reports it — is now executed.

The validator that **already ships on `main`** at `37a9c60`
(`.github/workflows/validator/`, merged via #771, wired into
`static_code_requirement_cicd.yaml` on `pull_request` for `examples/**`), run unmodified:

```text
  [PASS] examples/yaoba/singletask_learning_boost        ERROR checks: none   WARNING: 1
  [PASS] examples/yaoba/singletask_learning_yolox_tta    ERROR checks: none   WARNING: 2
  [FAIL] examples/robot-cityscapes-synthia/...           ERROR: Repository path references exist
  [FAIL] examples/MOT17/.../pedestrian_tracking (x2)     ERROR: Repository path references exist
  [FAIL] examples/Cloud_Robotics/.../perception-reasoning ERROR: Repository path references exist
```

Both Examples this PR retires pass **every check the project currently runs**, and neither
can execute: `algorithm.yaml` declares `paradigm_type: "singletasklearning_acboost"` and
`"singletasklearning_tta"`, neither of which is a member of `ParadigmType`
(`core/common/constant.py:33-44`), and dispatch in `base.py:95-152` and
`algorithm.py:109-127` is a chain of `if` comparisons with no `else` — so the call returns
`None` with no exception and no log line.

The reason the validator cannot catch this is worth stating precisely: it resolves whether
config strings point at **files that exist**, not whether config **identifiers** match
anything the code **registers**. There are zero references to `ClassFactory`, `register`,
`alias` or `paradigm_type` anywhere under `.github/workflows/validator/`.

This does not change my recommendation — **accepted as it is**; the deleted files are
genuinely unreachable and they import upward from `examples.yaoba…` into `core/`, which is
reason enough on its own. It sharpens the one request I made: because no check will ever
report these two Examples as broken, deleting their only implementation removes the last
trace that a decision was made. A line in the PR description saying which of the two
outcomes is intended — restore the `ParadigmType` entries, or retire the Examples and mark
their READMEs — would be enough.

Reproduce: `python3 tools/run_shipped_validator.py ianvs` —
https://github.com/henryng15/ianvs-lfx-pretest
