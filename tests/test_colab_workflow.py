"""Tests for Colab workflow helpers."""

from pathlib import Path

from src.colab_workflow import DriveLayout, is_colab_runtime, save_run_manifest


def test_is_colab_runtime_is_false_in_local_tests():
    """Local test environment should not be detected as Colab."""
    assert is_colab_runtime() is False


def test_drive_layout_paths():
    """DriveLayout should build expected directories."""
    layout = DriveLayout.from_drive(project_name="demo", drive_root="/tmp/drive")
    assert layout.project_root == Path("/tmp/drive/demo")
    assert layout.log_dir == Path("/tmp/drive/demo/data/logs")
    assert layout.runs_dir == Path("/tmp/drive/demo/runs")


def test_drive_layout_requires_project_name():
    """DriveLayout should reject missing project names."""
    try:
        DriveLayout.from_drive(project_name="", drive_root="/tmp/drive")
    except ValueError as exc:
        assert "project_name must be provided" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty project_name")


def test_save_run_manifest_writes_file(tmp_path):
    """Run manifest should be created in runs/<timestamp>/manifest.json."""
    layout = DriveLayout(
        project_root=tmp_path / "project",
        log_dir=tmp_path / "project" / "data" / "logs",
        runs_dir=tmp_path / "project" / "runs",
    )

    manifest_path = save_run_manifest(layout, note="test run", extra={"a": 1})
    assert manifest_path.exists()
    assert manifest_path.name == "manifest.json"
    assert manifest_path.parent.parent == layout.runs_dir
