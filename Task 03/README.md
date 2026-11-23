# Datheon Python Programming Internship

Python Programming Internship projects for Datheon — featuring CLI games, automation scripts, and terminal applications.

---

# Task 03: File Organizer

A clean, beginner-friendly command-line automation tool written in Python that organizes messy directories by automatically sorting files into categorized subfolders according to file extensions.

---

## Features

- **Standard Library Only**: Built using Python 3 built-in modules (`os`, `shutil`, `pathlib`, `argparse`, `logging`, `datetime`, `time`, `dataclasses`). No external runtime dependencies.
- **Case-Insensitive Categorization**: Matches extensions seamlessly (`.PDF`, `.pdf`, `.JpG`).
- **On-Demand Folder Creation**: Category folders are created **only** when at least one file belongs to that category.
- **Zero Data Overwriting (Collision Handling)**: If a file with the same name already exists in the destination folder, the incoming file is automatically renamed to `name (1).ext`, `name (2).ext`, etc.
- **Non-Destructive & Resilient**: Wrapped in granular exception handling (`PermissionError`, `FileNotFoundError`, `OSError`). If one file is locked or missing, it logs the error, counts it, and continues organizing remaining files.
- **Safety Checks**: Blocks attempts to run on drive roots (`C:\` or `/`), user home directories (`~`), and critical system directories (`Windows`, `Program Files`, `/usr`, etc.).
- **Dual Logging**: Console output provides high-level `INFO` summaries, while `logs/organizer.log` (stored next to the script) records detailed `DEBUG` traces.
- **Dry-Run Preview**: Test sorting behavior safely with `--dry-run` before moving any files.
- **Recursive Mode**: Safely organizes nested subfolders while preventing re-scanning of already created category folders.

---

## File Categories

Categories are configured in a single dictionary (`EXTENSION_CATEGORIES`) at the top of `organizer.py`:

| Category | File Extensions |
| :--- | :--- |
| **Documents** | `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.csv`, `.ppt`, `.pptx`, `.md` |
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp`, `.tiff`, `.ico` |
| **Videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz` |
| **Code** | `.py`, `.js`, `.ts`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.json`, `.sql`, `.ipynb` |
| **Others** | Any other extension or files without an extension (e.g. `LICENSE`, `Dockerfile`) |

---

## Project Structure

```text
Task 03/
├── organizer.py                 # Main deliverable script
├── make_test_folder.py          # Generates sandbox/messy_folder with ~25 test files
├── README.md                    # Documentation & usage guide
├── .gitignore                   # Ignores logs/, sandbox/, __pycache__/, .venv/
└── tests/
    └── test_organizer.py        # Comprehensive pytest test suite
```

---

## Installation & Setup

1. **Prerequisites**: Python 3.8+ installed.
2. **Clone / Open Workspace**:
   ```powershell
   cd "Task 03"
   ```
3. **Optional (For Running Tests)**:
   ```powershell
   pip install pytest
   ```

---

## Usage

### 1. Interactive Mode
If no path is passed, the script prompts for a directory and suggests your `Downloads` folder as the default:
```powershell
python organizer.py
```

### 2. Previewing Changes (Dry-Run)
Simulate the run to preview which files would move where without altering the disk:
```powershell
python organizer.py sandbox/messy_folder --dry-run
```

### 3. Organizing a Directory
Organize files with safety confirmation:
```powershell
python organizer.py sandbox/messy_folder
```

### 4. Skip Confirmation Prompt
Use `--yes` to skip the interactive `Proceed? (y/n)` prompt (ideal for automated scripts):
```powershell
python organizer.py sandbox/messy_folder --yes
```

### 5. Recursive Sorting
Sort files across all nested subdirectories:
```powershell
python organizer.py sandbox/messy_folder --recursive --yes
```

---

## Safe Sandbox Testing

A test generator script (`make_test_folder.py`) is included to populate a test folder with 25+ realistic dummy files containing uppercase extensions, hidden dotfiles, files without extensions, nested subdirectories, and collision candidates:

```powershell
# Step 1: Create messy sandbox
python make_test_folder.py

# Step 2: Test with dry-run
python organizer.py sandbox/messy_folder --dry-run

# Step 3: Run live organization
python organizer.py sandbox/messy_folder --yes

# Step 4: Verify idempotency (running again moves 0 files)
python organizer.py sandbox/messy_folder --yes
```

---

## Running the Test Suite

Run unit and integration tests using `pytest`:
```powershell
pytest -v
```

All tests run in temporary folders (`tmp_path`) and test:
- Case-insensitive extension matching.
- Fallback classification of unknown extensions to `Others`.
- Collision renaming (`report (1).pdf`) without overwriting.
- Safe dry-run behavior.
- Resilient recovery from `PermissionError` (locked files).
- Recursive scanning while skipping category folders.
- Safety protection on root/home directories.
