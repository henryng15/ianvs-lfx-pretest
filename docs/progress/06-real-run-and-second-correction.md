# 06 — Real Ianvs run, and a second correction

**Date:** 2026-08-28 · **Ianvs SHA:** `37a9c60` · **Status:** complete

## Why this step happened

The question "did we just accept someone else's fix and do nothing more?" was a fair one.
The answer for step 05 was no — the corrections there came with new findings — but it
exposed a real weakness: **Task 2's Reproduce section (6 points) had no actual `ianvs`
run.** Everything was static analysis or synthetic differential tests.

The `paradigm_type` finding was the one claim that could be executed with no dataset and
no GPU, so it was the obvious thing to run. Running it disproved my own claim.

## Setup (cheap, no GPU, ~2 GB RAM)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install prettytable pyyaml colorlog tqdm pandas numpy matplotlib onnx scikit-learn
pip install ianvs/resources/third_party/sedna-0.6.0.1-py3-none-any.whl
```

## What the run showed

`tools/probe_paradigm_runtime.py` → `evidence/probe_paradigm_runtime.txt`

```text
1. ianvs CLI on examples/yaoba/singletask_learning_boost
   exit code: 1
   RuntimeError: prepare dataset failed, error: not one of
   train_index/train_data/train_data_info.

2. Algorithm(...) -- where paradigm_type is validated
   yaoba acboost -> ValueError: not support paradigm(singletasklearning_acboost).
                    the following paradigms can be selected: [...]
   yaoba tta     -> ValueError: not support paradigm(singletasklearning_tta). ...
   valid control -> constructed, no error
```

## The error, retracted

I had written that dispatch "has no `else`, so an unknown `paradigm_type` returns `None`
silently — no exception, no log line, no validation at config-parse time."

**False.** `core/testcasecontroller/algorithm/algorithm.py:140-143` validates
`paradigm_type` against the enum and raises, called from `_parse_config` at line 167 —
long before the dispatch chain I was reading is reached. The error message even lists the
valid values.

| Claim | Verdict |
|---|---|
| Both `yaoba` Examples are unrunnable | **confirmed** |
| Shipped CI validator reports PASS for both | **confirmed** |
| Core validates `paradigm_type` silently | **RETRACTED** |

The run also showed the Examples fail *earlier* than the paradigm check, at dataset
preparation — so they are broken in at least two independent ways.

## The finding, corrected and narrower

The gap is **not** that Ianvs fails to validate identifiers. Core validates them, loudly
and helpfully. The gap is that **CI and Core validate different things and CI's set is
smaller**: `ParadigmType` sits in `core/common/constant.py` and the validator under
`.github/workflows/validator/` never consults it, so two Examples pass every check the
project runs and fail the moment they execute.

This is a better claim than the one it replaces: it names information that already exists
in the tree and is simply not wired into the check — which is exactly Step 1 of the Task 3
repair strategy, now describable as a small change rather than a new subsystem.

## Published corrections

| Where | What |
|---|---|
| [Bonus](https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171151), [Task 3](https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171145), [Task 4](https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171147) | "Second correction" section appended; the retracted sentence removed from the body and replaced with a pointer |
| [PR #617 (correction)](https://github.com/kubeedge/ianvs/pull/617#pullrequestreview-5047393734) | Same retraction on the target, with the run attached |
| [Task 2](https://github.com/kubeedge/ianvs/discussions/948#discussioncomment-18171142) | §5 Reproduce upgraded — now carries a real install and CLI run instead of "no end-to-end run is claimed" |

Permalinks unchanged throughout; corrections are appended and labelled, never silently
rewritten.

## Net effect

Two claims lost, one weakest-section fixed. Task 2 Reproduce moved from "static and
synthetic only" to "framework installed, CLI executed, exit code and traceback attached" —
the gap that mattered most for scoring, and the one I could close without the candidate's
video.

## Next step

Nothing further. `docs/HANDOVER.md` is current: 23 links, and the five manual steps.
