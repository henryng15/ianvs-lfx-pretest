# 02 — Verified findings and mandatory target set

**Date:** 2026-08-27 · **Ianvs SHA:** `37a9c60` · **PR #558 head:** `b99161f` · **Status:** complete

## What this step did

Read the diffs and every existing review thread of the eight open PRs on the
selected angle, then built executed probes for the claims we intend to publish.
All probes run the **unmodified production code** and need no GPU, dataset, or
network.

## The three findings we own

### F1 — `__all__` in Example modules is inert; two open PRs fix nothing runtime

`evidence/probe_all_is_inert.txt`

| Measurement at `37a9c60` | Value |
|---|---|
| Example modules with a malformed `__all__` | **30** |
| of those, ever consumed by `from ... import *` | **0** |
| star-imports anywhere in `core/` | **0** |
| references to `__all__` anywhere in `core/` | **0** |
| Core resolution sites using `ClassFactory.get_cls` | 3 |

Core resolves metrics and algorithm modules by ClassFactory alias
(`metrics.py:173`, `module.py:116,130`), never by `__all__`.

- **PR #651** rewrites `__all__` in 18 modules, justified by "`from module import *`
  walks it character by character". Nothing star-imports those modules.
- **PR #642** repoints `__all__` at `CloudModel` in Cloud_Robotics (issue #641).

Both are readability improvements, not bug fixes. Neither PR has a single review.

### F2 — `parse_kwargs` is unreachable; two open PRs fix one issue in dead code

`evidence/probe_parse_kwargs_dead.txt`

- `core/common/utils.py:46` defines `parse_kwargs`. Invocations in `core/` and
  `examples/`: **none**. Imports of it: **none**.
- Sedna ships **its own** `parse_kwargs` (`sedna/backend/base.py:47`, 14 call
  sites) and never imports Ianvs's.
- The reported defect is real and confirmed by execution: `parse_kwargs(kwonly,
  threshold=0.9)` returns `{}`.

So **#598** and **#702** are two PRs for one issue (#597), correcting a genuine
defect in code nothing reaches. Neither has a review.

### F3 — PR #558: transitive-import collision (active) and lost pickle recoverability (latent)

`evidence/probe_pr558_pickle.txt`

Sedna persists the lifelong-learning knowledge base with pickle
(`lifelong_learning.py` `FileOps.dump(task_index...)`,
`knowledge_management/*` `FileOps.dump(task_info...)`,
`file_ops.py` `joblib.dump`). pickle stores `__class__.__module__` as a string
and re-imports that name on load. #558 changes that name to
`<basename>_<md5 of the absolute file path>`.

| Unpickle in a fresh interpreter | main `37a9c60` | PR #558 `b99161f` |
|---|---|---|
| with nothing on `sys.path` | FAIL `No module named 'taskdef'` | FAIL |
| with the Example source dir on `sys.path` | **LOAD-OK** | **FAIL — no such module exists** |

On `main` the artifact is recoverable by the same `sys.path` insertion
`load_module()` itself performs. Under #558 the recorded name matches **no file
on disk**, and the md5 changes with the absolute path — so the artifact does not
survive a move between checkout directories, containers, or the edge/cloud
knowledge-base transfer lifelong learning performs by design.

**Scope, verified:** no shipped Example puts an Example-defined class into the pickled
`task_index` (all four `task_definition` modules return a plain dict; `Task.model` is a
path string before dump), so this is a **latent** regression, reported as such.

**Also found and demonstrated:** #558 fixes identity only for the file it opens. Sibling
imports still collide — example_B's `basemodel` binds example_A's `utils`, returning 1
instead of 100. @Aryansingh-ai raised this as an undemonstrated concern; it is now
demonstrated (`evidence/probe_pr558_transitive.txt`).

## Mandatory target set

| PR | Layer | Files | Existing reviews | Our verdict basis |
|---|---|---|---|---|
| **#558** | **Ianvs Core** — critical PR, changes the loader every paradigm uses | 1 | 3 rivals | F3 regression |
| #651 | 18 Example modules | 18 | **0** | F1 |
| #642 | Cloud_Robotics Example | 1 | **0** | F1 |
| #598 | Ianvs Core | 2 | **0** | F2 |
| #702 | Ianvs Core | 2 | **0** | F2 (duplicate of #598) |

Anchor issues: **#557** (Core loader, shared evidence), **#641** (Cloud_Robotics,
0 rivals), **#597** (Core, 0 rivals), **#568** (cloud-edge-collaborative-inference-for-llm, 0 rivals).
Examples involved: Cloud_Robotics, cloud-edge-collaborative-inference-for-llm,
imagenet/multiedge_inference_bench, MOT17, robot-cityscapes-synthia, and more.

## Next step

`03` — Draft the Discussion body and the five Task comments, plus one
target-specific review comment per PR. Then run the RunPod session for the
`#790` / `#599` / `#600` reproductions that need real NVIDIA hardware.
