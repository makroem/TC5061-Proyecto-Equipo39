"""
Validación del git state
"""
from types import SimpleNamespace
from mibici_equipo39.validation import data_checks as Q
from types import SimpleNamespace

def completed(stdout="", returncode=0):
    return SimpleNamespace(
        stdout=stdout,
        returncode=returncode,
    )

def test_git_state_returns_none_when_git_is_not_installed(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: None)

    assert Q.git_state() == (None, None)


def test_git_state_detects_clean_repository(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: "/fake/git")

    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))

        command = args[0]

        if command[1] == "rev-parse":
            return completed("abc123\n")

        if command[1] == "status":
            return completed("")

        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    commit, dirty = Q.git_state()

    assert commit == "abc123"
    assert dirty is False
    
    
def test_git_state_detects_dirty_repository(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: "/fake/git")

    def fake_run(*args, **kwargs):
        command = args[0]

        if command[1] == "rev-parse":
            return SimpleNamespace(
                returncode=0,
                stdout="abc123\n",
            )

        if command[1] == "status":
            return SimpleNamespace(
                returncode=0,
                stdout=" M data_checks.py\n",
            )

        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    commit, dirty = Q.git_state()

    assert commit == "abc123"
    assert dirty is True
    
    
def test_git_state_returns_none_when_rev_parse_fails(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: "/fake/git")

    def fake_run(*args, **kwargs):
        command = args[0]

        if command[1] == "rev-parse":
            return SimpleNamespace(
                returncode=1,
                stdout="",
            )

        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    assert Q.git_state() == (None, None)
    
    
def test_git_state_uses_resolved_git_executable(monkeypatch):
    git_path = "/custom/path/git"

    monkeypatch.setattr(Q.shutil, "which", lambda _: git_path)

    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])

        if args[0][1] == "rev-parse":
            return SimpleNamespace(
                returncode=0,
                stdout="abc123\n",
            )

        return SimpleNamespace(
            returncode=0,
            stdout="",
        )

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    Q.git_state()

    assert calls[0][0] == git_path
    assert calls[1][0] == git_path
    
def test_git_state_runs_without_shell(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: "/fake/git")

    observed_kwargs = []

    def fake_run(*args, **kwargs):
        observed_kwargs.append(kwargs)

        if args[0][1] == "rev-parse":
            return SimpleNamespace(
                returncode=0,
                stdout="abc123\n",
            )

        return SimpleNamespace(
            returncode=0,
            stdout="",
        )

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    Q.git_state()

    assert len(observed_kwargs) == 2

    for kwargs in observed_kwargs:
        assert kwargs.get("shell", False) is False
        
def test_git_state_uses_expected_git_commands(monkeypatch):
    git_path = "/custom/path/git"

    monkeypatch.setattr(Q.shutil, "which", lambda _: git_path)

    commands = []

    def fake_run(*args, **kwargs):
        commands.append(args[0])

        if args[0][1] == "rev-parse":
            return SimpleNamespace(
                returncode=0,
                stdout="abc123\n",
            )

        return SimpleNamespace(
            returncode=0,
            stdout="",
        )

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    Q.git_state()

    assert commands == [
        [git_path, "rev-parse", "HEAD"],
        [git_path, "status", "--porcelain"],
    ]
    
def test_git_state_returns_none_when_status_fails(monkeypatch):
    monkeypatch.setattr(Q.shutil, "which", lambda _: "/fake/git")

    def fake_run(*args, **kwargs):
        command = args[0]

        if command[1] == "rev-parse":
            return completed(
                "abc123\n",
                returncode=0,
            )

        if command[1] == "status":
            return completed(
                "",
                returncode=1,
            )

        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(Q.subprocess, "run", fake_run)

    assert Q.git_state() == (None, None)
    
