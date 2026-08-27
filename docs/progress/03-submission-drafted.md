# 03 — Submission drafted

**Date:** 2026-08-27 · **Ianvs SHA:** `37a9c60` · **Status:** drafted, ready to post

## What this step produced

`submission/` — the Discussion body, five Task comments, and 14 target-specific comments.

| File | Content |
|---|---|
| `00-discussion-body.md` | Root Problem, evidence table, verification boundary |
| `01-task1.md` … `05-bonus.md` | Tasks 1-4 and Bonus |
| `reviews/pr-*.md`, `reviews/issue-*.md` | 14 target-specific comments (Dual-channel Output) |

## Targets, final

**Task 2 mandatory (5 PRs, 1 critical):** #558 (Core, critical), #651, #642, #598, #702.
**Anchor issues:** #557, #597, #641, #568.
**Bonus (5 PRs):** #617, #569, #739, #632, #540 — none cited by any of the 70 rivals,
four with zero reviews.

## New finding added at this step

Reviewing #617 surfaced a **fifth** unvalidated-string surface: `paradigm_type`.
`evidence/census_paradigm_type.txt` — two shipped Examples
(`examples/yaoba/singletask_learning_yolox_tta`, `.../singletask_learning_boost`) declare
`singletasklearning_tta` / `singletasklearning_acboost`, neither of which is in
`ParadigmType`. Dispatch has no `else`, so the call returns `None` with no error. Those
two Examples are unrunnable and nothing reports it.

## Deliberate decisions

- **RunPod not used.** Every finding in this submission runs on CPU with no dataset, model
  or network. The device/GPU angle the original plan targeted was abandoned in step 01, and
  nothing that replaced it needs hardware. The $6.93 balance is untouched.
- **R4b scoped down after verification.** The #558 pickle regression was initially framed
  as active. Tracing `task_index` showed every shipped Example returns a plain dict, so it
  is reported as a **latent** regression. Stated as such everywhere.

## Next step

`04` — Post the Discussion and all comments, export the `.docx`, and write the handover
for the manual steps (screenshots, video, email).
