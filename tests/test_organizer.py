"""
Unit & Integration Tests for File Organizer
===========================================
Uses pytest and the `tmp_path` fixture to test behavior safely in isolated
temporary directories, ensuring the user's real filesystem is never touched.
"""

from pathlib import Path
import shutil
import pytest

from organizer import (
    EXTENSION_CATEGORIES,
    build_extension_map,
    get_category,
    is_safe_target,
    organize_folder,
    scan_directory,
    unique_destination,
)


@pytest.fixture
def ext_map():
    """Returns the inverted extension mapping."""
    return build_extension_map(EXTENSION_CATEGORIES)


# ==============================================================================
# 1. CATEGORY MATCHING (CASE-INSENSITIVE)
# ==============================================================================
def test_category_matching_case_insensitive(ext_map):
    """Verifies that extensions match regardless of letter case."""
    assert get_category(Path("document.pdf"), ext_map) == "Documents"
    assert get_category(Path("REPORT.PDF"), ext_map) == "Documents"
    assert get_category(Path("Photo.JpG"), ext_map) == "Images"
    assert get_category(Path("clip.MP4"), ext_map) == "Videos"
    assert get_category(Path("ARCHIVE.ZIP"), ext_map) == "Archives"
    assert get_category(Path("script.PY"), ext_map) == "Code"


# ==============================================================================
# 2. UNKNOWN & NO-EXTENSION FILES GO TO 'OTHERS'
# ==============================================================================
def test_unknown_and_no_extension_go_to_others(ext_map):
    """Verifies that unknown extensions and files without extensions go to Others."""
    assert get_category(Path("random_data.xyz"), ext_map) == "Others"
    assert get_category(Path("weird.custom123"), ext_map) == "Others"
    assert get_category(Path("LICENSE"), ext_map) == "Others"
    assert get_category(Path("Makefile"), ext_map) == "Others"
    assert get_category(Path("Dockerfile"), ext_map) == "Others"


# ==============================================================================
# 3. NAME COLLISIONS (NEVER OVERWRITE, RENAME TO 'name (1).ext')
# ==============================================================================
def test_collision_renaming_preserves_files(tmp_path):
    """Verifies that collisions rename incoming files without overwriting existing ones."""
    target_dir = tmp_path / "Documents"
    target_dir.mkdir()

    # Pre-existing file
    original_file = target_dir / "report.pdf"
    original_file.write_text("Original content", encoding="utf-8")

    # First collision candidate
    dest1, renamed1 = unique_destination(target_dir, "report.pdf")
    assert renamed1 is True
    assert dest1.name == "report (1).pdf"

    # Simulate creating the second file
    dest1.write_text("Second content", encoding="utf-8")

    # Second collision candidate
    dest2, renamed2 = unique_destination(target_dir, "report.pdf")
    assert renamed2 is True
    assert dest2.name == "report (2).pdf"

    # Simulate creating the third file
    dest2.write_text("Third content", encoding="utf-8")

    # Case-insensitive collision check (e.g. REPORT.PDF should also collide)
    dest3, renamed3 = unique_destination(target_dir, "REPORT.PDF")
    assert renamed3 is True
    assert dest3.name == "REPORT (3).PDF"

    # Verify original file content was never touched
    assert original_file.read_text(encoding="utf-8") == "Original content"


# ==============================================================================
# 4. DRY-RUN MODE (MOVES NOTHING, CREATES NO FOLDERS)
# ==============================================================================
def test_dry_run_moves_nothing(tmp_path):
    """Verifies that --dry-run previews moves without touching the filesystem."""
    test_folder = tmp_path / "messy"
    test_folder.mkdir()

    doc = test_folder / "notes.txt"
    img = test_folder / "picture.png"
    doc.write_text("Notes text", encoding="utf-8")
    img.write_text("Image bytes", encoding="utf-8")

    stats = organize_folder(test_folder, dry_run=True, recursive=False)

    # Stats should show found and simulated moves
    assert stats.total_found == 2
    assert stats.moved == 2
    assert stats.errors == 0

    # Original files should still be at their initial positions
    assert doc.exists()
    assert img.exists()

    # Category folders must NOT have been created
    assert not (test_folder / "Documents").exists()
    assert not (test_folder / "Images").exists()


# ==============================================================================
# 5. ERROR RESILIENCE (SIMULATED PERMISSIONERROR)
# ==============================================================================
def test_permission_error_resilience(tmp_path, monkeypatch):
    """Verifies that a locked file (PermissionError) logs error, counts it, and continues."""
    test_folder = tmp_path / "messy"
    test_folder.mkdir()

    file1 = test_folder / "locked_file.txt"
    file2 = test_folder / "normal_file.txt"
    file1.write_text("locked", encoding="utf-8")
    file2.write_text("normal", encoding="utf-8")

    real_move = shutil.move

    def mock_move(src, dst):
        # Simulate PermissionError on file1
        if "locked_file" in str(src):
            raise PermissionError("Access is denied: locked by another process")
        return real_move(src, dst)

    monkeypatch.setattr(shutil, "move", mock_move)

    stats = organize_folder(test_folder, dry_run=False, recursive=False)

    # 1 error counted, but normal_file.txt was still successfully moved
    assert stats.total_found == 2
    assert stats.errors == 1
    assert stats.moved == 1

    # file1 remains in messy folder
    assert file1.exists()
    # file2 was moved to Documents/normal_file.txt
    assert (test_folder / "Documents" / "normal_file.txt").exists()


# ==============================================================================
# 6. RECURSIVE MODE & NO RE-SCANNING OF CATEGORY FOLDERS
# ==============================================================================
def test_recursive_mode_finds_nested_files_and_skips_category_folders(tmp_path):
    """Verifies recursive mode sorts subfolders but avoids re-sorting category folders."""
    test_folder = tmp_path / "messy"
    test_folder.mkdir()

    # Top-level file
    (test_folder / "top.pdf").write_text("top pdf", encoding="utf-8")

    # Subfolder with file
    sub = test_folder / "sub"
    sub.mkdir()
    (sub / "nested.png").write_text("nested png", encoding="utf-8")

    # Run organizer recursively
    stats = organize_folder(test_folder, dry_run=False, recursive=True)

    assert stats.total_found == 2
    assert stats.moved == 2
    assert (test_folder / "Documents" / "top.pdf").exists()
    assert (test_folder / "Images" / "nested.png").exists()

    # Run again with recursive=True: it must NOT re-scan Documents or Images folders
    stats_second_run = organize_folder(test_folder, dry_run=False, recursive=True)
    assert stats_second_run.total_found == 0
    assert stats_second_run.moved == 0


# ==============================================================================
# 7. SKIP HIDDEN FILES & SYMLINKS
# ==============================================================================
def test_skips_hidden_files(tmp_path):
    """Verifies that dotfiles (.env, .gitignore) are skipped."""
    test_folder = tmp_path / "messy"
    test_folder.mkdir()

    hidden_file = test_folder / ".secret_env"
    hidden_file.write_text("SECRET=123", encoding="utf-8")

    regular_file = test_folder / "visible.txt"
    regular_file.write_text("Hello", encoding="utf-8")

    stats = organize_folder(test_folder, dry_run=False, recursive=False)

    assert stats.total_found == 1
    assert stats.moved == 1
    assert hidden_file.exists()  # Kept untouched
    assert (test_folder / "Documents" / "visible.txt").exists()


# ==============================================================================
# 8. SAFETY CHECK
# ==============================================================================
def test_safety_check(tmp_path):
    """Verifies that is_safe_target protects system and root paths."""
    # Safe temporary folder
    safe_ok, _ = is_safe_target(tmp_path)
    assert safe_ok is True

    # User home should be blocked
    home_ok, _ = is_safe_target(Path.home())
    assert home_ok is False

    # Drive root should be blocked
    root_path = Path(tmp_path.drive + "\\") if tmp_path.drive else Path("/")
    root_ok, _ = is_safe_target(root_path)
    assert root_ok is False
