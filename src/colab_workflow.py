"""Utilities for a Drive-first Colab workflow."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def is_colab_runtime() -> bool:
    """Return True when running inside Google Colab."""
    return "google.colab" in sys.modules or bool(os.environ.get("COLAB_RELEASE_TAG"))


def mount_drive_if_needed(drive_root: str = "/content/drive/MyDrive") -> None:
    """Mount Google Drive when running in Colab and not already mounted."""
    if not is_colab_runtime():
        return

    drive_root_path = Path(drive_root)
    if drive_root_path.exists():
        return

    from google.colab import drive  # type: ignore

    drive.mount("/content/drive")


@dataclass(frozen=True)
class DriveLayout:
    """Directory layout for Drive-first experiment runs."""

    project_root: Path
    log_dir: Path
    runs_dir: Path

    @classmethod
    def from_drive(
        cls,
        project_name: str,
        drive_root: str = "/content/drive/MyDrive",
    ) -> "DriveLayout":
        if not project_name.strip():
            raise ValueError("project_name must be provided for Drive layouts")
        project_root = Path(drive_root) / project_name
        return cls(
            project_root=project_root,
            log_dir=project_root / "data" / "logs",
            runs_dir=project_root / "runs",
        )

    def ensure_dirs(self) -> None:
        """Create Drive directories if missing."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)


def _safe_cmd(command: list[str]) -> str:
    """Run command and return trimmed output, or 'unknown' on failure."""
    try:
        return subprocess.check_output(command, text=True).strip()
    except Exception:
        return "unknown"


def save_run_manifest(
    layout: DriveLayout,
    note: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Write run metadata to Drive and return the manifest path."""
    layout.ensure_dirs()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = layout.runs_dir / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "timestamp_utc": ts,
        "cwd": str(Path.cwd()),
        "log_dir": str(layout.log_dir),
        "git_branch": _safe_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "git_commit": _safe_cmd(["git", "rev-parse", "HEAD"]),
        "note": note,
    }
    if extra:
        manifest["extra"] = extra

    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest_path


def save_notebook_checkpoint() -> None:
    """Request a Colab notebook checkpoint save."""
    if not is_colab_runtime():
        return

    try:
        from IPython.display import Javascript, display
    except Exception:
        return

    display(Javascript("google.colab.notebook.saveCheckpoint();"))
