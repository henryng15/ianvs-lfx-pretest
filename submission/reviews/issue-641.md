Confirmed at `37a9c60`: `cloud_model.py:23` declares
`__all__ = ["QwenSemanticSegmentation"]` and the module defines `CloudModel`.

Adding the impact assessment, since it affects how the issue should be triaged.

**This has no runtime effect.** `__all__` only takes effect under
`from <module> import *`. At `37a9c60`:

- star-imports anywhere in `core/`: **0**
- references to `__all__` anywhere in `core/`: **none**
- anything star-importing this module: **0**

Core resolves the class through the ClassFactory alias instead —
`core/testcasecontroller/algorithm/module/module.py:116,130` and
`core/testcasecontroller/metrics/metrics.py:173` — and this module registers correctly.
The Example is not broken by this.

**It is also not isolated.** The same census finds **30** malformed `__all__`
declarations across 10 Examples, in two shapes: naming a symbol the module does not
define (this issue, plus `edge_model.py:25`, `cloud_model.py:25` in
`cloud-edge-collaborative-inference-for-llm`, and both `task_*_by_domain.py` in
`robot-cityscapes-synthia`), and `__all__ = ('name')` — parentheses without a comma, so a
string rather than a tuple — in 18 metric modules. None of the 30 is load-bearing.

A nice illustration is
`examples/robot-cityscapes-synthia/.../erfnet/task_definition_by_domain.py`: `__all__`
names `TaskDefinitionByDomain`, the class is `TaskDefinitionByOrigin`, the
`@ClassFactory.register(..., alias="TaskDefinitionByDomain")` is correct, and the Example
works. The declared name is wrong, the resolved name is right, and nothing notices.

PR #642 fixes this file and PR #651 fixes the 18 string cases. Both are worth merging as
cleanup; neither changes behaviour.

Reproduce: `python3 tools/probe_all_is_inert.py ianvs` —
https://github.com/henryng15/ianvs-lfx-pretest
