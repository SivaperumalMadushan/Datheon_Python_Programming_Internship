"""
File Organizer
==============
A command-line automation script that organizes messy directories by sorting
files into category subfolders based on file extensions.

Author: Python Intern & Learner
Tech: Python 3 Standard Library only (os, shutil, pathlib, argparse, logging, time, dataclasses)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

# ==============================================================================
# CATEGORY CONFIGURATION
# ==============================================================================
# Mapping from category subfolder names to their associated file extensions.
# All extensions must be lowercase and begin with a period (dot).
EXTENSION_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "Documents": (
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".xls", ".xlsx", ".csv", ".ppt", ".pptx", ".md",
    ),
    "Images": (
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
        ".webp", ".tiff", ".ico",
    ),
    "Videos": (
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ),
    "Archives": (
        ".zip", ".rar", ".7z", ".tar", ".gz",
    ),
    "Code": (
        ".py", ".js", ".ts", ".html", ".css", ".java",
        ".c", ".cpp", ".json", ".sql", ".ipynb",
    ),
    "Others": (),  # Fallback category for unknown extensions or files with no extension
}


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================
@dataclass
class Stats:
    """Stores execution metrics and file counts for the organizer run."""

    total_found: int = 0
    moved: int = 0
    renamed: int = 0
    skipped: int = 0
    errors: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    elapsed_time: float = 0.0


# ==============================================================================
# LOGGING SETUP
# ==============================================================================
def setup_logging(log_file_path: Path) -> logging.Logger:
    """Configures dual-output logging: INFO to console, DEBUG to a dedicated log file.

    The log file is always stored next to this script (in logs/organizer.log),
    never inside the folder being organized.
    """
    logger = logging.getLogger("file_organizer")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if setup_logging is called multiple times (e.g., in tests)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Ensure the parent logs/ directory exists
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler: logs detailed debug information
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)

    # Console handler: shows high-level information to the user
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)-8s | %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ==============================================================================
# DECISION LOGIC (PURE FUNCTIONS - EASY TO UNIT TEST)
# ==============================================================================
def build_extension_map(categories_dict: Dict[str, Tuple[str, ...]]) -> Dict[str, str]:
    """Inverts the category dictionary into an extension -> category mapping.

    All extensions are converted to lowercase for O(1) case-insensitive lookup.
    Example: {'.pdf': 'Documents', '.jpg': 'Images', ...}
    """
    ext_map: Dict[str, str] = {}
    for category, extensions in categories_dict.items():
        for ext in extensions:
            ext_map[ext.lower()] = category
    return ext_map


def get_category(file_path: Path, ext_map: Dict[str, str]) -> str:
    """Determines the target category for a file based on its extension.

    Extensions are compared case-insensitively. Files with no extension
    or unrecognized extensions are classified into 'Others'.
    """
    # .suffix gets the file extension (e.g. '.PDF' -> '.pdf')
    ext = file_path.suffix.lower()

    # If the extension is known in our mapping, return its category
    if ext and ext in ext_map:
        return ext_map[ext]

    # Handle files with no extension or unrecognized extensions
    return "Others"


def unique_destination(
    target_dir: Path,
    original_name: str,
    reserved_names_lower: Optional[Set[str]] = None,
) -> Tuple[Path, bool]:
    """Resolves name collisions without overwriting existing files.

    If target_dir already contains a file matching original_name (compared case-insensitively),
    this function increments a numeric suffix: 'name (1).ext', 'name (2).ext', etc.

    Args:
        target_dir: Directory where the file will be placed.
        original_name: The base name of the incoming file (e.g., 'report.pdf').
        reserved_names_lower: Optional set of lowercase filenames already present or
                              reserved during this run (helps avoid collision in dry-runs).

    Returns:
        A tuple of (final_destination_path, was_renamed_flag).
    """
    # Gather lowercase names of files currently present in target_dir
    existing_lower: Set[str] = set()
    if target_dir.exists() and target_dir.is_dir():
        for item in target_dir.iterdir():
            existing_lower.add(item.name.lower())

    if reserved_names_lower:
        existing_lower.update(reserved_names_lower)

    path_candidate = Path(original_name)
    stem = path_candidate.stem
    suffix = path_candidate.suffix

    # If the original filename is not taken, we can use it directly
    if original_name.lower() not in existing_lower:
        return target_dir / original_name, False

    # Name is taken: find the first available 'stem (counter).suffix'
    counter = 1
    while True:
        candidate_name = f"{stem} ({counter}){suffix}"
        if candidate_name.lower() not in existing_lower:
            return target_dir / candidate_name, True
        counter += 1


def is_safe_target(folder_path: Path) -> Tuple[bool, str]:
    """Safety check to prevent accidental sorting of system or root directories.

    Refuses drive roots (e.g. 'C:\\' or '/'), the user's home directory itself,
    and major operating system directories.
    """
    try:
        resolved = folder_path.resolve()
    except Exception as err:
        return False, f"Cannot resolve path '{folder_path}': {err}"

    if not resolved.exists():
        return False, f"Directory does not exist: {resolved}"

    if not resolved.is_dir():
        return False, f"Path is not a directory: {resolved}"

    # 1. Reject drive roots (e.g., 'C:\\' on Windows or '/' on Unix)
    if resolved == resolved.parent or resolved.parent == resolved:
        return False, f"Refusing to organize drive root: {resolved}"

    # On Windows, Path('C:\\').drive == 'C:' and Path('C:\\').parts == ('C:\\',)
    if len(resolved.parts) <= 1:
        return False, f"Refusing to organize drive root: {resolved}"

    # 2. Reject the user's home directory itself (e.g., 'C:\\Users\\username' or '/home/user')
    try:
        user_home = Path.home().resolve()
        if resolved == user_home:
            return False, f"Refusing to organize user home directory directly: {resolved}"
    except Exception:
        pass

    # 3. Reject critical system folders (Windows & Linux/macOS)
    resolved_str = str(resolved).lower()
    system_folder_names = {
        "windows",
        "program files",
        "program files (x86)",
        "system32",
        "boot",
        "bin",
        "sbin",
        "usr",
        "etc",
        "var",
        "sys",
        "proc",
    }

    # If any path component exactly matches a known system folder name
    for part in resolved.parts:
        if part.lower() in system_folder_names:
            # Allow safe subdirectories inside user profiles even if containing names
            # But directly targeting system locations is rejected
            if part.lower() in ("windows", "program files", "program files (x86)", "etc", "usr", "bin"):
                # If path starts with system root or system directory
                return False, f"Refusing to organize protected system folder: {resolved}"

    return True, "Target directory is safe."


# ==============================================================================
# DIRECTORY SCANNING
# ==============================================================================
def scan_directory(
    root_folder: Path,
    recursive: bool,
    category_names: Set[str],
    script_path: Path,
    log_file_path: Path,
) -> List[Path]:
    """Scans the directory for candidate files using os.scandir() inside 'with' blocks.

    Rules applied:
    - Skips hidden files (names starting with '.').
    - Skips symlinks (follow_symlinks=False).
    - Skips this organizer script and its log file.
    - In recursive mode: does NOT descend into category folders and does not follow symlinks.
    """
    files_to_process: List[Path] = []
    category_names_lower = {cat.lower() for cat in category_names}

    resolved_script = script_path.resolve() if script_path.exists() else None
    resolved_log = log_file_path.resolve() if log_file_path.exists() else None

    # Helper function to scan a single directory level
    def _scan_level(current_dir: Path, is_top_level: bool):
        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    # Check symlink first to prevent symlink traversal
                    try:
                        if entry.is_symlink():
                            continue
                    except OSError:
                        continue

                    # 1. Skip hidden files/directories (starting with '.')
                    if entry.name.startswith("."):
                        continue

                    # 2. Handle subdirectories
                    if entry.is_dir(follow_symlinks=False):
                        if not recursive:
                            continue

                        # When scanning recursively from top level, don't descend into category folders
                        if entry.name.lower() in category_names_lower:
                            continue

                        # Recurse into nested subfolder
                        _scan_level(Path(entry.path), is_top_level=False)
                        continue

                    # 3. Handle regular files
                    if entry.is_file(follow_symlinks=False):
                        file_path = Path(entry.path)
                        try:
                            resolved_file = file_path.resolve()
                        except OSError:
                            resolved_file = file_path

                        # Skip the script itself and the log file
                        if resolved_script and resolved_file == resolved_script:
                            continue
                        if resolved_log and resolved_file == resolved_log:
                            continue

                        # If scanning top-level and a file is somehow inside a category folder, skip it
                        if not is_top_level:
                            # In recursive mode, if parent directory is a category folder, skip
                            if file_path.parent.name.lower() in category_names_lower:
                                continue

                        files_to_process.append(file_path)

        except (PermissionError, FileNotFoundError, OSError) as err:
            logging.getLogger("file_organizer").warning(
                f"Could not scan directory '{current_dir}': {err}"
            )

    _scan_level(root_folder, is_top_level=True)
    return files_to_process


# ==============================================================================
# ACTIONS: MOVING & EXECUTING
# ==============================================================================
def move_file(source: Path, destination: Path, dry_run: bool) -> None:
    """Moves a file to its destination, creating category subfolders on demand.

    If dry_run is True, no directory is created and no file is moved.
    """
    if dry_run:
        # Dry-run: simulate action only
        return

    # Create destination category directory only when a file actually needs it
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Use standard library shutil.move to relocate the file
    shutil.move(str(source), str(destination))


def organize_folder(
    folder: Path,
    dry_run: bool = False,
    recursive: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Stats:
    """Coordinates scanning, categorizing, renaming for collisions, and moving files."""
    if logger is None:
        logger = logging.getLogger("file_organizer")

    start_time = time.time()
    stats = Stats()

    ext_map = build_extension_map(EXTENSION_CATEGORIES)
    category_names = set(EXTENSION_CATEGORIES.keys())

    script_path = Path(__file__)
    log_path = script_path.parent / "logs" / "organizer.log"

    # Step 1: Scan for all eligible files
    found_files = scan_directory(
        root_folder=folder,
        recursive=recursive,
        category_names=category_names,
        script_path=script_path,
        log_file_path=log_path,
    )
    stats.total_found = len(found_files)

    # Set of reserved lowercase destinations within each category for this run
    reserved_destinations: Dict[str, Set[str]] = {cat: set() for cat in category_names}

    # Step 2: Process each file with robust error handling
    for source in found_files:
        try:
            # Verify file still exists (has not vanished or been deleted by another process)
            if not source.exists() or not source.is_file():
                logger.warning(f"File vanished before move: {source}")
                stats.skipped += 1
                continue

            # Determine category subfolder
            category = get_category(source, ext_map)
            target_dir = folder / category

            # Check if source is already inside its correct category folder
            # (e.g. on repeated runs without recursion or if already sorted)
            if source.parent.resolve() == target_dir.resolve():
                stats.skipped += 1
                continue

            # Determine safe destination name without overwriting
            dest, was_renamed = unique_destination(
                target_dir=target_dir,
                original_name=source.name,
                reserved_names_lower=reserved_destinations[category],
            )

            # Reserve this name so subsequent files in this batch don't pick the same name
            reserved_destinations[category].add(dest.name.lower())

            if was_renamed:
                stats.renamed += 1
                logger.debug(f"NAME COLLISION: Renaming '{source.name}' -> '{dest.name}'")

            # Execute or preview the move
            if dry_run:
                logger.info(f"[DRY RUN] Would move {source} -> {dest}")
            else:
                move_file(source, dest, dry_run=False)
                logger.info(f"MOVED {source} -> {dest}")

            # Record success
            stats.moved += 1
            stats.category_counts[category] = stats.category_counts.get(category, 0) + 1

        except PermissionError as err:
            logger.error(f"Permission denied (file may be in use): {source} -> {err}")
            stats.errors += 1
        except FileNotFoundError as err:
            logger.error(f"File not found during move: {source} -> {err}")
            stats.errors += 1
        except (OSError, shutil.Error) as err:
            logger.error(f"Failed to move file '{source}': {err}")
            stats.errors += 1

    stats.elapsed_time = time.time() - start_time
    return stats


# ==============================================================================
# SUMMARY & CLI INTERFACE
# ==============================================================================
def print_summary(stats: Stats, folder: Path, dry_run: bool) -> None:
    """Prints a clean, formatted terminal summary of the organization run."""
    mode_label = "DRY RUN" if dry_run else "LIVE"
    print("\n================ ORGANIZER SUMMARY ================")
    print(f"Folder     : {folder.resolve()}")
    print(f"Mode       : {mode_label}")
    print(f"Files found: {stats.total_found}")
    print(f"Moved      : {stats.moved}")
    print(f"Renamed    : {stats.renamed}   (name collisions)")
    print(f"Skipped    : {stats.skipped}")
    print(f"Errors     : {stats.errors}")
    print(f"Time       : {stats.elapsed_time:.2f} s")
    print("---------------------------------------------------")
    print(f"{'Category':<16} Files")

    # Display counts for all active categories
    active_categories = [
        (cat, count)
        for cat, count in sorted(stats.category_counts.items(), key=lambda x: (-x[1], x[0]))
    ]
    if active_categories:
        for cat, count in active_categories:
            print(f"{cat:<16} {count:>5}")
    else:
        print("No files were moved.")
    print("===================================================\n")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sort messy files into category subfolders by extension.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Path to the directory to organize (defaults to prompt or ~/Downloads)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the sorting without moving any files",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Descend into nested subfolders (skipping category folders)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt",
    )
    return parser.parse_args(args)


def main() -> int:
    """Entry point for command-line execution."""
    script_dir = Path(__file__).resolve().parent
    log_file = script_dir / "logs" / "organizer.log"
    logger = setup_logging(log_file)

    args = parse_args()

    # Step 1: Determine target folder
    target_str = args.folder
    if not target_str:
        default_downloads = Path.home() / "Downloads"
        prompt_msg = f"Enter folder to organize [Default: {default_downloads}]: "
        try:
            user_input = input(prompt_msg).strip()
            target_str = user_input if user_input else str(default_downloads)
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            return 1

    target_folder = Path(target_str).expanduser()

    # Step 2: Validate folder safety
    is_safe, safety_message = is_safe_target(target_folder)
    if not is_safe:
        logger.error(f"SAFETY ABORT: {safety_message}")
        print(f"\n[ERROR] Safety check failed: {safety_message}")
        return 1

    # Step 3: Scan preview for confirmation
    ext_map = build_extension_map(EXTENSION_CATEGORIES)
    category_names = set(EXTENSION_CATEGORIES.keys())
    preview_files = scan_directory(
        root_folder=target_folder,
        recursive=args.recursive,
        category_names=category_names,
        script_path=Path(__file__),
        log_file_path=log_file,
    )

    # Step 4: Interactive confirmation before live run
    if not args.dry_run and not args.yes:
        print(f"\nTarget folder: {target_folder.resolve()}")
        print(f"Files found  : {len(preview_files)}")
        try:
            proceed = input("Proceed? (y/n): ").strip().lower()
            if proceed not in ("y", "yes"):
                print("Operation cancelled by user.")
                return 0
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.")
            return 1

    # Step 5: Run organization
    stats = organize_folder(
        folder=target_folder,
        dry_run=args.dry_run,
        recursive=args.recursive,
        logger=logger,
    )

    # Step 6: Print formatted summary
    print_summary(stats, target_folder, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
