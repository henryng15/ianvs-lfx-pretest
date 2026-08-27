Reproduced at `37a9c60`, and adding a measurement of how much of the repository is
exposed.

**Reproduction**, importing the unmodified `core.common.utils.load_module` (it needs only
`yaml`, so no stubbing was required):

```text
--- test case 1: load_module(example_A/testenv/accuracy.py) ---
  sys.modules['accuracy'].EXAMPLE_ID = example_A
  accuracy(None, None)               = 0.11

--- test case 2: load_module(example_B/testenv/accuracy.py) ---
  sys.modules['accuracy'].EXAMPLE_ID = example_A      <-- B's file, A's code
  accuracy(None, None)               = 0.11

  test case 2 got the SAME module object as test case 1 : True
  test case 2 actually loaded its own file              : False
  load_module() raised no error                        : True
```

**Exposure across the repository**, from an AST census of all 572 Example `.py` files:

| bare module name | distinct files carrying it |
|---|---|
| `basemodel.py` | **41** |
| `accuracy.py` | **13** |
| `acc.py` | **12** |
| `utils.py`, `train.py` | 10 each |

69 basenames are shared by more than one file; 392 of 572 Example modules collide with at
least one other. The condition this issue needs is the default:
`TestCaseController.run_testcases()` (`core/testcasecontroller/testcasecontroller.py:46-61`)
runs every test case sequentially in one interpreter.

**Practical consequence worth recording on this issue:** a `benchmarkingjob.yaml`
comparing two algorithms whose implementations are both named `basemodel.py` does not
crash. It benchmarks the first algorithm twice and reports the results as two leaderboard
rows. The output is well-formed and wrong.

Scripts and raw output: https://github.com/henryng15/ianvs-lfx-pretest
(`python3 tools/probe_load_module.py ianvs`)
