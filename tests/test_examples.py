"""Execute examples/walkthrough.yaml so the documented tour always works."""
import contextlib
import io
import os

import pytest
import yaml

from agentlib.cli import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "examples", "walkthrough.yaml"), encoding="utf-8") as fh:
    STEPS = yaml.safe_load(fh)["steps"]


@pytest.mark.parametrize("step", STEPS, ids=[s["title"] for s in STEPS])
def test_walkthrough_step(step, monkeypatch):
    monkeypatch.chdir(ROOT)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(step["argv"])
        except SystemExit as exc:  # argparse errors
            code = exc.code
    text = out.getvalue() + err.getvalue()
    assert code == step["exit"], f"exit {code}, expected {step['exit']}\n{text[:2000]}"
    for needle in step["expect"]:
        assert needle in text, f"missing {needle!r}\n{text[:2000]}"
