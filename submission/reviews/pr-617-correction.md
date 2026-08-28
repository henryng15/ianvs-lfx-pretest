Correction to my own follow-up above, with an executed run this time.

I wrote that dispatch "is a chain of `if` comparisons with no `else` — so the call returns
`None` with no exception and no log line." **That is wrong**, and I should not have
inferred it from reading the dispatch chain.
`core/testcasecontroller/algorithm/algorithm.py:140-143` validates `paradigm_type` against
`ParadigmType` and raises; `_parse_config` calls it at line 167, well before
`build_paradigm_job` is reached.

I installed Ianvs (`requirements.txt` plus the bundled `sedna-0.6.0.1` wheel) and ran it
at `37a9c60`:

```text
1. ianvs CLI on examples/yaoba/singletask_learning_boost
   exit code: 1
   RuntimeError: benchmarkingjob runs failed, error: prepare dataset failed,
   error: not one of train_index/train_data/train_data_info..

2. Algorithm(...) -- where paradigm_type is validated
   yaoba acboost: paradigm_type='singletasklearning_acboost'
      -> ValueError: not support paradigm(singletasklearning_acboost).
         the following paradigms can be selected: ['singletasklearning', ...]
   yaoba tta:     paradigm_type='singletasklearning_tta'
      -> ValueError: not support paradigm(singletasklearning_tta). ...
   valid control: paradigm_type='singletasklearning'
      -> constructed, no error
```

**What holds and what I retract:**

| | |
|---|---|
| Both Examples this PR retires are unrunnable | **confirmed** — CLI exits 1; `Algorithm(...)` raises on the paradigm |
| The shipped CI validator reports **PASS** for both | **confirmed** |
| Core validates `paradigm_type` silently / returns `None` | **retracted — Core validates it correctly, and the error message even lists the valid values** |

The run also shows these Examples fail *earlier* than the paradigm check, at dataset
preparation, so they are broken in at least two independent ways.

**None of this changes my recommendation, which remains `accepted as it is`,** and the one
request I made stands but for a better reason than I originally gave. It is not that
nothing would report these Examples as broken — Core reports them clearly the moment
anyone runs them. It is that **CI does not**, because the validator never consults
`ParadigmType` even though it sits in `core/common/constant.py`. So deleting the two
paradigm implementations is correct, and a line in the description saying whether the
`yaoba` Examples are being retired deliberately would still help — CI will keep saying
they are fine either way.

Apologies for the noise of a third comment on this PR. I would rather correct a wrong
statement I made on your PR than leave it sitting there.

Reproduce: `python3 tools/probe_paradigm_runtime.py ianvs` —
https://github.com/henryng15/ianvs-lfx-pretest
