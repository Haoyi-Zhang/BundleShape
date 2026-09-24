#!/usr/bin/env python3
import os as _runner_os
from pathlib import Path as _RunnerPath
_runner_os.chdir(_RunnerPath(__file__).resolve().parent)

import argparse
import json
from pathlib import Path
import time
import unittest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "wall_seconds": round(time.perf_counter() - start, 6),
    }
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "unit-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
