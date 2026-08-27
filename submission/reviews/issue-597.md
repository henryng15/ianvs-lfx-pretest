The defect is confirmed. Running the current helper at `37a9c60`:

```text
parse_kwargs(positional, threshold=0.9) -> {'threshold': 0.9}
parse_kwargs(kwonly,     threshold=0.9) -> {}
```

`getfullargspec()` reports keyword-only parameters in `.kwonlyargs`, and the function
only consults `.args`, exactly as described.

**One correction to the stated impact.** The issue says this causes hyperparameters to be
silently dropped for Examples. On this commit it cannot, because nothing reaches the
function. An AST scan of `core/` and `examples/` at `37a9c60`:

```text
definitions : ['core/common/utils.py:46']
invocations : NONE
imports of the helper : NONE
```

The bundled Sedna wheel defines and calls **its own** `parse_kwargs`
(`sedna/backend/base.py:47`, with 14 call sites across
`sedna/backend/{base,mindspore,tensorflow}`) and does not import
`core.common.utils`. Hyperparameter filtering for Examples goes through Sedna's copy,
which is unaffected by this bug.

So the code is wrong and the consequence is currently zero. That seems worth recording
here, because it changes what the fix needs: no Example regression testing, and a prior
decision about whether an uncalled helper should be repaired or removed. Two open PRs
(#598 and #702) currently fix it independently.

Reproduce: `python3 tools/probe_parse_kwargs_dead.py ianvs` —
https://github.com/henryng15/ianvs-lfx-pretest
