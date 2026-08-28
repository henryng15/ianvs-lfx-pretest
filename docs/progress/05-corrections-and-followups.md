# 05 — Corrections and follow-ups

**Date:** 2026-08-28 · **Ianvs SHA:** `37a9c60` · **Status:** complete

## Trigger

Checking the posted targets for replies found three items, all on the `parse_kwargs`
thread, plus — through a rival's review of PR #835 — evidence that **one of my claims was
wrong**.

## The error I made, and fixed

Task 4 §2.2 said static contract validation had **no existing work**, and Task 3 §3.4
proposed adding a CI job. Both were wrong: `.github/workflows/validator/` **already ships
on `main` at `37a9c60`**, having landed with PR #771 — the merge commit I had been
analysing all along — and is wired into `static_code_requirement_cicd.yaml` for
`examples/**`.

Found via @Prachi194agrawal's review on PR #835. My prior-art map covered 86 Discussions
and every open Issue/PR, and still missed a validator sitting in the checked-out tree,
because I searched the PR queue for *proposals* and never checked what had *merged*.

**Corrections posted in place** (editing preserves permalinks) to the Task 3, Task 4 and
Bonus comments, each under an explicit "Correction — posted 2026-08-28" heading. Nothing
was silently rewritten.

## What the correction produced — a stronger claim

`tools/run_shipped_validator.py`, running the shipped validator unmodified:

```text
  [PASS] examples/yaoba/singletask_learning_boost        ERROR checks: none
  [PASS] examples/yaoba/singletask_learning_yolox_tta    ERROR checks: none
  [FAIL] examples/robot-cityscapes-synthia/...           ERROR: Repository path references exist
  [FAIL] examples/MOT17/.../pedestrian_tracking (x2)     ERROR: Repository path references exist
  [FAIL] examples/Cloud_Robotics/.../perception-reasoning ERROR: Repository path references exist
```

The validator resolves whether config strings point at **files that exist**. It does not
resolve whether config **identifiers** match what the code **registers** — zero references
to `ClassFactory`, `register`, `alias` or `paradigm_type` under
`.github/workflows/validator/`. So **two Examples pass every check the project runs and
cannot execute at all.**

That is a better-evidenced version of the original claim: the missing fix is not "a CI
check" but specifically "identifier resolution", demonstrated against the project's own
shipped validation.

## Follow-ups posted

| Target | Why |
|---|---|
| [PR #598 (follow-up)](https://github.com/kubeedge/ianvs/pull/598#pullrequestreview-5047338395) | Author moved the head `69470dd` → `6b39813` and added tests after my review. Re-reviewed: independently confirmed @31groot's positional-only finding, added two new cases (`getfullargspec` raises `TypeError` on unintrospectable callables; builtins silently return `{}`), and **revised my verdict from minor to major revision** since code changes are now required. |
| [PR #617 (follow-up)](https://github.com/kubeedge/ianvs/pull/617#pullrequestreview-5047339798) | Promoted the static `paradigm_type` claim to executed evidence using the shipped validator. |

## Uniqueness re-checked

86 LFX Discussions now (was 70); 17 new since 2026-08-27. Re-ran the claim scan:

| Claim | Discussions asserting it |
|---|---|
| `__all__` is inert / read by nothing | **0** |
| `parse_kwargs` unreachable | **0** |
| #558 pickle recoverability | **0** |

Two new Discussions have adjacent titles — #965 (benchmark *data* contracts: #357/#502/#563,
#782/#807/#564) and #953 (config validation via #835) — neither overlaps this target set,
and both were created after #948.

**Not claimed:** the #835 allowlist-reachability cascade — @sheikhayaan raised it on that
PR before I looked at it.

## Next step

Nothing further from me. The handover in `docs/HANDOVER.md` is current: repo visibility,
screenshots, video, email, final link check.
