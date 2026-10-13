import json

from agentlib.cli import main
from agentlib.install import LOCK_NAME, install
from agentlib.registry import build_registry


def test_registry_is_deterministic(root):
    assert build_registry(root) == build_registry(root)


def test_install_roundtrip(tmp_path, root):
    target = tmp_path / "repo"
    target.mkdir()
    report = install(target, ["skills", "agents", "commands", "workflows"], root=root)
    assert "Installed" in report
    lock = json.loads((target / LOCK_NAME).read_text())
    for rel, digest in lock["files"].items():
        assert (target / rel).is_file(), rel
    # local edits are preserved unless --force
    skills = sorted((target / ".claude" / "skills").glob("*/SKILL.md"))
    if skills:
        skills[0].write_text("locally edited")
        report = install(target, ["skills"], root=root)
        assert "skipped" in report and skills[0].read_text() == "locally edited"
        install(target, ["skills"], root=root, force=True)
        assert skills[0].read_text() != "locally edited"


def test_install_dry_run_writes_nothing(tmp_path, root):
    target = tmp_path / "repo"
    target.mkdir()
    install(target, ["skills"], dry_run=True, root=root)
    assert not (target / LOCK_NAME).exists()
    assert not (target / ".claude").exists()


def test_cli_list_and_validate(capsys):
    assert main(["list", "skills"]) == 0
    assert "SKILLS" in capsys.readouterr().out
