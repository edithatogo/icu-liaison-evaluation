"""Independent tests for local CI/CD runner, Git hooks, and Conductor audit."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.audit_conductor_extension import (
    NON_RUNTIME_REPO_PACKAGING_FILES,
    audit_extension,
    normalize_display_path,
)
from tools.run_local_ci import build_steps, find_forbidden_paths, run_gitleaks_staged, run_local_ci

ROOT = Path(__file__).resolve().parents[1]


def _make_extension_tree(base: Path, *, decision: str = "ask_user", include_packaging: bool = True) -> None:
    if base.exists():
        import shutil
        shutil.rmtree(base)
    (base / "commands/conductor").mkdir(parents=True, exist_ok=True)
    (base / "policies").mkdir(parents=True, exist_ok=True)
    (base / "commands/conductor/status.toml").write_text('prompt = "status"\n', encoding="utf-8")
    (base / "GEMINI.md").write_text("# Conductor\n", encoding="utf-8")
    (base / "policies/conductor.toml").write_text(
        f'[[rule]]\ntoolName = "run_shell_command"\ndecision = "{decision}"\nmodes = ["plan"]\n',
        encoding="utf-8",
    )
    if include_packaging:
        (base / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        (base / "CONTRIBUTING.md").write_text("Contribute\n", encoding="utf-8")


def test_find_forbidden_paths_rejects_private_outputs_data_and_env() -> None:
    sample = [
        "src/icu_liaison/cli.py",
        "docs/repository-import.md",
        "private/chhhs_cohort.csv",
        "outputs/run1.json",
        "results/table.csv",
        "model/observations.CSV",
        "nested/.local/feed.json",
        "nested/private/contract.json",
        "report/database.sqlite",
        "model/workbook.xlsx",
        "model/macro.xlsm",
        "data/episodes.parquet",
        "arrays/draws.npz",
        ".env",
        ".env.local",
    ]
    assert find_forbidden_paths(sample) == sorted(
        [
            ".env",
            ".env.local",
            "arrays/draws.npz",
            "data/episodes.parquet",
            "model/macro.xlsm",
            "model/observations.CSV",
            "model/workbook.xlsx",
            "nested/.local/feed.json",
            "nested/private/contract.json",
            "outputs/run1.json",
            "private/chhhs_cohort.csv",
            "report/database.sqlite",
            "results/table.csv",
        ]
    )
    assert find_forbidden_paths(["README.md", "tests/test_p0_local_ci.py"]) == []


def _temporary_git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _start_publication_fixture(root: Path) -> None:
    _temporary_git(root, "init", "-q")
    _temporary_git(root, "config", "core.autocrlf", "false")
    _temporary_git(root, "config", "user.email", "test@example.invalid")
    _temporary_git(root, "config", "user.name", "Fictional fixture")


@pytest.mark.parametrize(
    "payload",
    [
        {"data_class": "restricted", "fixture": "invented"},
        {"value": [{"id": "FICTIONAL"}]},
        {"file_sha256": {".local/fictional.json": "0" * 64}},
        {"source": "https://example." + "sharepoint.com/sites/fictional"},
    ],
)
def test_publication_guard_reads_staged_blob_instead_of_working_file(tmp_path: Path, payload: dict) -> None:
    from tools.publication_guard import index_violations

    _start_publication_fixture(tmp_path)
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(payload))
    _temporary_git(tmp_path, "add", "metadata.json")
    path.write_text(json.dumps({"data_class": "synthetic"}))
    assert index_violations(tmp_path) == ["metadata.json"]


def test_private_local_files_are_excluded_from_source_inventory(tmp_path: Path) -> None:
    from tools.verify_source_manifest import source_files

    d = tmp_path / "nested" / ".local"
    d.mkdir(parents=True)
    (d / "fictional.json").write_text("{}")
    assert source_files(tmp_path) == {}


def test_only_frozen_public_csv_bytes_are_admitted(tmp_path: Path) -> None:
    from tools.publication_guard import index_violations

    _start_publication_fixture(tmp_path)
    name = "tests/fixtures/p3_episodes/episodes.csv"
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / name).read_bytes())
    _temporary_git(tmp_path, "add", name)
    assert index_violations(tmp_path) == []
    path.write_bytes(path.read_bytes() + b"\n")
    _temporary_git(tmp_path, "add", name)
    assert index_violations(tmp_path) == [name]


def test_pending_push_checks_intermediate_commit_even_with_clean_tip(tmp_path: Path) -> None:
    from tools.publication_guard import pending_push_violations

    _start_publication_fixture(tmp_path)
    _temporary_git(tmp_path, "commit", "-q", "--allow-empty", "-m", "Public source baseline")
    base = _temporary_git(tmp_path, "rev-parse", "HEAD")
    path = tmp_path / "fixture.csv"
    path.write_text("id,measure\nFICTIONAL,1\n")
    _temporary_git(tmp_path, "add", "fixture.csv")
    _temporary_git(tmp_path, "commit", "-qm", "Fictional export")
    _temporary_git(tmp_path, "rm", "-q", "fixture.csv")
    _temporary_git(tmp_path, "commit", "-qm", "Remove fictional export")
    tip = _temporary_git(tmp_path, "rev-parse", "HEAD")
    rejected = f"refs/heads/topic {tip} refs/heads/topic {base}"
    assert pending_push_violations(tmp_path, [rejected]) == ["fixture.csv"]
    clean = f"refs/heads/topic {base} refs/heads/topic {'0' * len(base)}"
    assert pending_push_violations(tmp_path, [clean]) == []

    # Use the real pre-push hook against an isolated bare repository.
    for name in [".githooks/pre-push", "tools/publication_guard.py"]:
        f = tmp_path / name
        f.parent.mkdir(exist_ok=True)
        f.write_bytes((ROOT / name).read_bytes())
        f.chmod((ROOT / name).stat().st_mode)
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(sys.executable)
    _temporary_git(tmp_path, "config", "core.hooksPath", ".githooks")
    remote = tmp_path / "remote.git"
    _temporary_git(tmp_path, "init", "-q", "--bare", str(remote))
    result = subprocess.run(
        ["git", "-C", str(tmp_path), "push", str(remote), "HEAD:refs/heads/topic"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "Public-data check rejected 1 path(s)" in result.stderr
    assert "fixture.csv" not in result.stderr
    assert not _temporary_git(remote, "for-each-ref", "--format=%(refname)")


def test_build_steps_matches_modes() -> None:
    manifest_steps = [s["name"] for s in build_steps(ROOT, sys.executable, "manifest-only")]
    assert manifest_steps == ["verify_source_manifest"]

    pre_commit_steps = [s["name"] for s in build_steps(ROOT, sys.executable, "pre-commit")]
    assert pre_commit_steps == ["verify_source_manifest", "pytest", "ci_smoke"]

    full_steps = [s["name"] for s in build_steps(ROOT, sys.executable, "full")]
    assert full_steps == [
        "verify_source_manifest",
        "pytest",
        "ci_smoke",
        "qualify_current_portable",
        "illustrative_cli",
    ]

    with pytest.raises(ValueError, match="Unsupported"):
        build_steps(ROOT, sys.executable, "unknown")  # type: ignore[arg-type]


def test_run_local_ci_manifest_only_and_forbidden_staged_guard(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "tools").mkdir()
    (repo / "tools/verify_source_manifest.py").write_text(
        (ROOT / "tools/verify_source_manifest.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    version_pin = (ROOT / ".python-version").read_text(encoding="utf-8")
    (repo / ".python-version").write_text(version_pin, encoding="utf-8")
    (repo / "SOURCE_MANIFEST.json").write_text(
        json.dumps({"file_sha256": {}, "git_submodules": {}}, sort_keys=True),
        encoding="utf-8",
    )
    subprocess.run([sys.executable, str(repo / "tools/verify_source_manifest.py"), "--write"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "add", ".python-version", "tools/verify_source_manifest.py", "SOURCE_MANIFEST.json"],
        check=True,
    )

    code, summary = run_local_ci(repo, mode="manifest-only", check_staged=True, python_exe=sys.executable, quiet=True)
    assert code == 0
    assert summary["status"] == "LOCAL_CI_PASSED_SYNTHETIC_ONLY"
    assert summary["hosted_ci_executed"] is False
    assert summary["native_providers_executed"] is False
    assert summary["investment_ready"] is False

    (repo / ".env").write_text("SECRET=1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-f", ".env"], check=True)
    code_bad, summary_bad = run_local_ci(
        repo, mode="manifest-only", check_staged=True, python_exe=sys.executable, quiet=True
    )
    assert code_bad == 2
    assert summary_bad["status"] == "FORBIDDEN_PATHS_REJECTED"
    assert summary_bad["forbidden_paths"] == [".env"]


def test_run_local_ci_rejects_interpreter_outside_runtime_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tools.run_local_ci._python_version", lambda _: "3.13.18")
    with pytest.raises(RuntimeError, match=r"requires Python .+ from \.python-version.+is Python 3\.13\.18"):
        run_local_ci(ROOT, mode="manifest-only", quiet=True)


def test_run_local_ci_drops_hook_git_overrides_from_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    git_dir = subprocess.check_output(
        ["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, text=True,
    ).strip()
    monkeypatch.setenv("GIT_DIR", git_dir)
    test_step = {
        "name": "pytest",
        "command": [sys.executable, "-c", "import os; assert 'GIT_DIR' not in os.environ"],
        "pythonpath_src": True,
        "validator": "pytest",
    }
    monkeypatch.setattr("tools.run_local_ci.build_steps", lambda *_: [test_step])

    code, summary = run_local_ci(ROOT, mode="pre-commit", quiet=True)

    assert code == 0, summary
    assert summary["steps"][0]["status"] == "passed"


def test_audit_extension_verifies_parity_caveats_and_rejects_drift(tmp_path: Path) -> None:
    pinned = tmp_path / "pinned"
    installed = tmp_path / "installed"
    _make_extension_tree(pinned, include_packaging=True)
    _make_extension_tree(installed, include_packaging=True)

    exact = audit_extension(pinned, installed)
    assert exact["status"] == "PINNED_PARITY_VERIFIED"
    assert exact["missing_runtime_files"] == []
    assert exact["extra_in_installed"] == []
    assert exact["hash_mismatches"] == []

    # github-release installs may exclude repo packaging files, while autoUpdate flags a caveat.
    (installed / ".gitignore").unlink()
    (installed / "CONTRIBUTING.md").unlink()
    (installed / ".gemini-extension-install.json").write_text(
        json.dumps({"type": "github-release", "releaseTag": "conductor-v0.4.1", "autoUpdate": True}),
        encoding="utf-8",
    )
    github_release_audit = audit_extension(pinned, installed)
    assert github_release_audit["status"] == "PINNED_PARITY_VERIFIED_WITH_AUTOUPDATE_CAVEAT"
    assert set(github_release_audit["missing_non_runtime_packaging_files"]) <= NON_RUNTIME_REPO_PACKAGING_FILES
    assert github_release_audit["missing_runtime_files"] == []

    # Without github-release type, missing packaging files must fail full-tree parity.
    (installed / ".gemini-extension-install.json").write_text(
        json.dumps({"type": "git", "autoUpdate": False}),
        encoding="utf-8",
    )
    assert audit_extension(pinned, installed)["status"] == "AUDIT_MISMATCH"

    # Restore packaging files and test runtime missing, content mismatch, extra file, unsafe policy.
    _make_extension_tree(installed, include_packaging=True)
    (installed / "GEMINI.md").unlink()
    missing_runtime = audit_extension(pinned, installed)
    assert missing_runtime["status"] == "AUDIT_MISMATCH"
    assert missing_runtime["missing_runtime_files"] == ["GEMINI.md"]

    _make_extension_tree(installed, include_packaging=True)
    (installed / "GEMINI.md").write_text("# Tampered\n", encoding="utf-8")
    tampered = audit_extension(pinned, installed)
    assert tampered["status"] == "AUDIT_MISMATCH"
    assert tampered["hash_mismatches"] == ["GEMINI.md"]

    _make_extension_tree(installed, include_packaging=True)
    (installed / "extra.txt").write_text("extra\n", encoding="utf-8")
    extra = audit_extension(pinned, installed)
    assert extra["status"] == "AUDIT_MISMATCH"
    assert extra["extra_in_installed"] == ["extra.txt"]

    _make_extension_tree(installed, decision="allow", include_packaging=True)
    unsafe = audit_extension(pinned, installed)
    assert unsafe["status"] == "AUDIT_MISMATCH"
    assert unsafe["policies"]["installed"]["unapproved_auto_allow_rules"]


def test_normalize_display_path_redacts_home_directory() -> None:
    sample = Path.home() / ".gemini/extensions/conductor"
    assert normalize_display_path(sample) == "~/.gemini/extensions/conductor"
    assert str(Path.home()) not in normalize_display_path(sample)


def test_git_hooks_and_pre_commit_config_exist_and_are_executable() -> None:
    for rel in (
        ".githooks/pre-commit",
        ".githooks/pre-merge-commit",
        ".githooks/pre-push",
        "tools/install_git_hooks.sh",
    ):
        path = ROOT / rel
        assert path.is_file(), f"Missing hook or installer: {rel}"
        assert os.access(path, os.X_OK), f"Not executable: {rel}"

    pre_commit_cfg = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "tools/run_local_ci.py" in pre_commit_cfg
    assert "--gitleaks" in pre_commit_cfg
    assert "--gitleaks" in (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")
    assert "--gitleaks" in (ROOT / ".githooks/pre-merge-commit").read_text(encoding="utf-8")


def test_run_gitleaks_staged_fails_closed_when_missing_and_handles_exit_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("tools.run_local_ci.shutil.which", lambda name: None)
    code_missing, rec_missing = run_gitleaks_staged(tmp_path)
    assert code_missing == 2
    assert rec_missing["status"] == "missing_binary"

    seen: dict = {}

    def fake_run_pass(cmd, **kwargs):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("tools.run_local_ci.subprocess.run", fake_run_pass)
    code_ok, rec_ok = run_gitleaks_staged(tmp_path, gitleaks_bin="/fake/gitleaks")
    assert code_ok == 0
    assert rec_ok["status"] == "passed"
    assert seen["cmd"] == ["/fake/gitleaks", "protect", "--staged", "--no-banner", "--redact"]

    def fake_run_leak(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="leaks found: 1")

    monkeypatch.setattr("tools.run_local_ci.subprocess.run", fake_run_leak)
    code_leak, rec_leak = run_gitleaks_staged(tmp_path, gitleaks_bin="/fake/gitleaks")
    assert code_leak == 1
    assert rec_leak["status"] == "failed"
    assert "leaks found" in rec_leak["stderr"]
