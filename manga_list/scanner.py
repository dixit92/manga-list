"""Filesystem scanner: walk Manga Root -> MangaEntry list."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from .classifier import annotate_file, classify, parse_folder_name
from .models import FileHit, MangaEntry

ARCHIVE_EXTS = {".cbz", ".zip", ".cbr", ".rar", ".7z", ".cb7"}

MAX_DEPTH = 3  # 0 = manga folder itself; 3 = files three levels deep


def _is_archive(p: Path) -> bool:
    return p.suffix.lower() in ARCHIVE_EXTS


def _walk_manga_folder(folder: Path, max_depth: int = MAX_DEPTH) -> List[FileHit]:
    """Return archive FileHits inside ``folder`` up to ``max_depth`` levels."""
    hits: List[FileHit] = []
    folder = folder.resolve()

    for dirpath, dirnames, filenames in os.walk(folder):
        try:
            rel_depth = len(Path(dirpath).resolve().relative_to(folder).parts)
        except ValueError:
            rel_depth = 0
        if rel_depth > max_depth:
            # Don't descend any further.
            dirnames[:] = []
            continue
        for name in filenames:
            p = Path(dirpath) / name
            if not _is_archive(p):
                continue
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            hit = FileHit(path=p, size=size, depth=rel_depth)
            annotate_file(hit)
            hits.append(hit)
    return hits


def _count_subfolders(folder: Path) -> int:
    try:
        return sum(1 for c in folder.iterdir() if c.is_dir())
    except OSError:
        return 0


def _has_direct_archives(folder: Path) -> bool:
    """Return True if folder contains archive files directly (not in subdirs)."""
    try:
        for p in folder.iterdir():
            if p.is_file() and _is_archive(p):
                return True
    except OSError:
        pass
    return False


def _get_subdirs_with_archives(folder: Path) -> List[Path]:
    """Return immediate subdirectories that contain archive files (at any depth)."""
    result: List[Path] = []
    try:
        for subdir in folder.iterdir():
            if not subdir.is_dir():
                continue
            # Check if this subdir has any archives (using existing walk)
            if _walk_manga_folder(subdir):
                result.append(subdir)
    except OSError:
        pass
    return result


# Subdirectory names to skip when extracting franchise subseries
_SKIP_SUBDIR_NAMES = {"chapters", "extras", "bonus", "specials", "omake"}


def _extract_subseries(
    parent: Path, parent_title: str, parent_mtime: float
) -> List[MangaEntry]:
    """Create MangaEntry objects for each subseries in a franchise parent.

    Skips subdirectories named exactly 'Chapters' or other non-series folders.
    Each subseries gets parent_folder set to the parent Path.
    """
    entries: List[MangaEntry] = []
    subdirs = _get_subdirs_with_archives(parent)

    for subdir in subdirs:
        # Skip non-series subdirectories
        if subdir.name.lower() in _SKIP_SUBDIR_NAMES:
            continue

        # Parse subdir name using same logic as parent
        sub_title, sub_eng = parse_folder_name(subdir.name)

        # Use subdir's own mtime if available, fall back to parent
        try:
            mtime = subdir.stat().st_mtime
        except OSError:
            mtime = parent_mtime

        entry = MangaEntry(
            folder=subdir,
            title=sub_title,
            english_title=sub_eng,
            n_subfolders=_count_subfolders(subdir),
            last_modified=mtime,
            parent_folder=parent,  # Mark as subseries
        )
        entry.files = _walk_manga_folder(subdir)
        classify(entry)
        entries.append(entry)

    return entries


def scan_root(
    root: Path,
    progress: Optional[Callable[[int, int, str], None]] = None,
) -> List[MangaEntry]:
    """Scan a Manga Root and return classified MangaEntry objects.

    ``progress(done, total, current_name)`` is called as folders are processed.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    manga_dirs = sorted(
        (p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name.lower(),
    )
    total = len(manga_dirs)
    entries: List[MangaEntry] = []

    for i, folder in enumerate(manga_dirs, start=1):
        if progress:
            progress(i - 1, total, folder.name)

        title, eng = parse_folder_name(folder.name)
        try:
            mtime = folder.stat().st_mtime
        except OSError:
            mtime = 0.0

        has_direct = _has_direct_archives(folder)
        subseries = _extract_subseries(folder, title, mtime)

        if not has_direct and subseries:
            # Parent is a franchise container - only add subseries, not parent
            entries.extend(subseries)
        elif has_direct and subseries:
            # Parent has both direct files AND subseries - add both
            # Create parent entry normally
            parent_entry = MangaEntry(
                folder=folder,
                title=title,
                english_title=eng,
                n_subfolders=_count_subfolders(folder),
                last_modified=mtime,
            )
            parent_entry.files = _walk_manga_folder(folder)
            classify(parent_entry)
            entries.append(parent_entry)
            # Also add subseries
            entries.extend(subseries)
        else:
            # Normal case: no subseries, just the folder itself
            entry = MangaEntry(
                folder=folder,
                title=title,
                english_title=eng,
                n_subfolders=_count_subfolders(folder),
                last_modified=mtime,
            )
            entry.files = _walk_manga_folder(folder)
            classify(entry)
            entries.append(entry)

    if progress:
        progress(total, total, "")
    return entries
