# Reproducible evidence — KubeEdge Ianvs, LFX 2026 Term 3 pre-test

Command output, static-analysis censuses and executable probes backing the pre-test
Discussion **[kubeedge/ianvs#948](https://github.com/kubeedge/ianvs/discussions/948)**
and its target-specific reviews.

Everything here is measured against upstream `kubeedge/ianvs` at commit **`37a9c60`**.
Every probe runs on CPU in seconds, with no dataset, model weights, API key or network
access, so any reviewer can re-run the whole set.

## Reproducing

```bash
git clone --depth 1 https://github.com/kubeedge/ianvs.git ianvs   # cloned here, git-ignored
python3 tools/probe_all_is_inert.py ianvs        # E1  __all__ is read by nothing
python3 tools/probe_parse_kwargs_dead.py ianvs   # E2  parse_kwargs has no callers
python3 tools/probe_pr558_transitive.py ianvs    # R4a PR #558 sibling-import differential
python3 tools/probe_pr558_pickle.py ianvs        # R4b PR #558 pickle-recovery differential
python3 tools/run_shipped_validator.py ianvs     # what the shipped CI validator checks
```

`probe_pr558_*.py` fetch the PR branch and compare it against `main`, so they need network
access for the fetch only. `tools/probe_paradigm_runtime.py` additionally needs Ianvs
installed:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install prettytable pyyaml colorlog tqdm pandas numpy matplotlib onnx scikit-learn
pip install ianvs/resources/third_party/sedna-0.6.0.1-py3-none-any.whl
python3 tools/probe_paradigm_runtime.py ianvs
```

## Layout

| Path | Contents |
|---|---|
| `tools/probe_*.py` | Executable probes; each prints the claim it tests and its verdict |
| `tools/scan_*.py`, `tools/build_coverage.py` | AST censuses and the prior-work coverage map |
| `evidence/*.txt`, `evidence/*.json` | Captured output of the above, unedited |
| `evidence/diffs/` | Diffs of every reviewed PR at the commit reviewed |
| `evidence/screenshots/`, `evidence/videos/` | Terminal captures embedded in the Discussion |

## Ground rules used throughout

1. No unexecuted check is described as passed. Every claim carries its command, the commit
   it ran against, and its output.
2. Where execution was impossible, the blocker is stated instead of glossed over.
3. Claims that turned out to be wrong were retracted in place, publicly, with the
   corrected finding and its evidence.
