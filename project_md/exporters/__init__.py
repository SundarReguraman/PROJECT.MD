"""Exporters that write native AI-assistant context files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from project_md.exporters.exporters import EXPORTERS, Exporter, render_all


def write_files(files: Dict[str, str], out_dir, force: bool = False) -> Tuple[List[Path], List[Path]]:
    """Write ``files`` under ``out_dir``. Returns (written, skipped).

    Existing files are skipped unless ``force``: the target is often a repo
    that already has a hand-written CLAUDE.md or .cursorrules. Note that on
    case-insensitive filesystems (macOS, Windows) ``Claude.md`` counts as
    existing ``CLAUDE.md``.
    """
    root = Path(out_dir)
    written: List[Path] = []
    skipped: List[Path] = []
    for relative, content in files.items():
        path = root / relative
        if path.exists() and not force:
            skipped.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        written.append(path)
    return written, skipped


__all__ = ["EXPORTERS", "Exporter", "render_all", "write_files"]
