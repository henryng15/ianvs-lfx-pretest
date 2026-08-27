#!/usr/bin/env python3
"""Executed reproduction: Ianvs Core's load_module() silently reuses a
previously imported module when two Examples share a file basename.

Production code under test (imported unmodified, no stubs):
    core.common.utils.load_module   -- ianvs/core/common/utils.py:92-105

Mechanism: load_module() splits the url, prepends the directory to sys.path and
calls importlib.import_module(<basename>). It never clears sys.modules, so the
second call for a different file with the same basename is a no-op: Python
returns the already-cached module. TestCaseController.run_testcases()
(core/testcasecontroller/testcasecontroller.py:46-61) runs every test case
sequentially in one interpreter, so this is the real execution order.

Usage: python3 tools/probe_load_module.py [path/to/ianvs]
"""
import os, subprocess, sys, tempfile, textwrap, pathlib

IANVS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ianvs").resolve()

MODULE_TEMPLATE = textwrap.dedent('''\
    """Stand-in for an Example metric module named {name}.py."""
    EXAMPLE_ID = "{example}"
    def accuracy(y_true, y_pred):
        return {value}
''')


def build_fixture(root, example, value, name="accuracy"):
    d = root / example / "testenv"
    d.mkdir(parents=True)
    f = d / f"{name}.py"
    f.write_text(MODULE_TEMPLATE.format(name=name, example=example, value=value))
    return f


def main():
    sys.path.insert(0, str(IANVS))
    from core.common.utils import load_module          # production code

    sha = subprocess.run(["git", "-C", str(IANVS), "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    print(f"ianvs commit under test : {sha}")
    print(f"load_module source      : {IANVS}/core/common/utils.py:92")
    print(f"python                  : {sys.version.split()[0]}\n")

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        a = build_fixture(root, "example_A", 0.11)
        b = build_fixture(root, "example_B", 0.99)

        print("Two distinct Example metric modules, identical basename:")
        print(f"  test case 1 -> {a}")
        print(f"  test case 2 -> {b}\n")

        print("--- test case 1: load_module(example_A/testenv/accuracy.py) ---")
        load_module(str(a))
        m1 = sys.modules["accuracy"]
        print(f"  sys.modules['accuracy'].__file__   = {m1.__file__}")
        print(f"  sys.modules['accuracy'].EXAMPLE_ID = {m1.EXAMPLE_ID}")
        print(f"  accuracy(None, None)               = {m1.accuracy(None, None)}\n")

        print("--- test case 2: load_module(example_B/testenv/accuracy.py) ---")
        load_module(str(b))
        m2 = sys.modules["accuracy"]
        print(f"  sys.modules['accuracy'].__file__   = {m2.__file__}")
        print(f"  sys.modules['accuracy'].EXAMPLE_ID = {m2.EXAMPLE_ID}")
        print(f"  accuracy(None, None)               = {m2.accuracy(None, None)}\n")

        same = m1 is m2
        served_b = pathlib.Path(m2.__file__).resolve() == b.resolve()
        print("=" * 68)
        print(f"  test case 2 got the SAME module object as test case 1 : {same}")
        print(f"  test case 2 actually loaded its own file              : {served_b}")
        print(f"  load_module() raised no error                        : True")
        print("=" * 68)
        if same and not served_b:
            print("\nRESULT: test case 2 silently executed test case 1's code.")
            print("        No exception, no warning. The benchmark reports a")
            print("        result for example_B that was produced by example_A.")
            return 0
        print("\nRESULT: not reproduced on this interpreter.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
