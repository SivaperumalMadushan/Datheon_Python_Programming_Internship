"""
Test Sandbox Generator (make_test_folder.py)
============================================
Creates a messy sandbox folder (sandbox/messy_folder) populated with ~25
dummy files to safely test the File Organizer script.

Includes edge cases:
- Uppercase extensions (.JPG, .PDF, .TXT)
- Files with no extension (LICENSE, DOCKERFILE)
- Hidden files (.env, .gitignore_test)
- Filename collisions (e.g. 'report.pdf' at root and inside a subfolder)
- Unknown extensions (.xyz, .customext)
- Nested subfolders with files (documents, images, scripts)
"""

import os
from pathlib import Path
import shutil


def create_dummy_file(path: Path, content: str = "Dummy test content\n") -> None:
    """Helper function to create a parent directory and write test content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_messy_folder(base_dir: Path) -> Path:
    """Creates sandbox/messy_folder with approximately 25 test files."""
    messy_folder = base_dir / "sandbox" / "messy_folder"

    # Reset any existing sandbox folder for a clean, reproducible state
    if messy_folder.exists():
        shutil.rmtree(messy_folder)

    messy_folder.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # 1. Documents (standard, uppercase, different extensions)
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "report.pdf", "Main top-level report")
    create_dummy_file(messy_folder / "meeting_notes.docx", "Weekly sync notes")
    create_dummy_file(messy_folder / "README_NOTES.TXT", "Uppercase TXT extension")
    create_dummy_file(messy_folder / "budget.xlsx", "Q1 Budget")
    create_dummy_file(messy_folder / "guide.md", "# Guide to testing")
    create_dummy_file(messy_folder / "DATASET.CSV", "id,name,value\n1,Alpha,100")

    # --------------------------------------------------------------------------
    # 2. Images (standard, uppercase, different formats)
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "PHOTO.JPG", "JPEG test data")
    create_dummy_file(messy_folder / "logo.png", "PNG image")
    create_dummy_file(messy_folder / "banner.webp", "WebP banner")
    create_dummy_file(messy_folder / "icon.ico", "Application icon")
    create_dummy_file(messy_folder / "diagram.svg", "<svg></svg>")

    # --------------------------------------------------------------------------
    # 3. Videos
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "screencast.mp4", "MP4 video content")
    create_dummy_file(messy_folder / "recording.mkv", "MKV video stream")

    # --------------------------------------------------------------------------
    # 4. Archives
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "project_backup.zip", "PK Zip content")
    create_dummy_file(messy_folder / "data_dump.tar", "Tarball data")
    create_dummy_file(messy_folder / "bundle.7z", "7-Zip archive")

    # --------------------------------------------------------------------------
    # 5. Code
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "script.py", "print('hello world')")
    create_dummy_file(messy_folder / "app.js", "console.log('web app');")
    create_dummy_file(messy_folder / "config.json", '{"debug": true}')
    create_dummy_file(messy_folder / "styles.css", "body { color: #333; }")

    # --------------------------------------------------------------------------
    # 6. Others: Unknown extension & No extension
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / "archive_backup.xyz", "Unrecognized extension xyz")
    create_dummy_file(messy_folder / "data.unknownext", "Unrecognized extension")
    create_dummy_file(messy_folder / "LICENSE", "MIT License text without extension")
    create_dummy_file(messy_folder / "Dockerfile", "FROM python:3.11-slim")

    # --------------------------------------------------------------------------
    # 7. Hidden files (should always be skipped)
    # --------------------------------------------------------------------------
    create_dummy_file(messy_folder / ".env", "API_KEY=secret_token")
    create_dummy_file(messy_folder / ".gitkeep", "")

    # --------------------------------------------------------------------------
    # 8. Nested subfolder (for testing recursive scanning & collisions)
    # --------------------------------------------------------------------------
    # This 'report.pdf' will collide with the top-level 'report.pdf' in recursive mode!
    nested_dir = messy_folder / "subfolder" / "nested_docs"
    create_dummy_file(nested_dir / "report.pdf", "Subfolder report (collision candidate)")
    create_dummy_file(nested_dir / "nested_photo.png", "Nested photo file")
    create_dummy_file(nested_dir / "deep_notes.txt", "Deep nested notes")

    return messy_folder


def main() -> None:
    project_root = Path(__file__).resolve().parent
    folder = make_messy_folder(project_root)
    print(f"Created test sandbox at: {folder}")

    # Count generated files
    total_files = sum(1 for p in folder.rglob("*") if p.is_file())
    print(f"Total dummy files generated: {total_files}")


if __name__ == "__main__":
    main()
