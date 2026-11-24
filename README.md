# Datheon Python Programming Internship

Projects completed during my remote **Python Programming Internship at Datheon** (November 2026). Each task is a self-contained Python project in its own folder, with its own README, tests and run instructions.

## Table of contents

- [Repository structure](#repository-structure)
- [Tasks at a glance](#tasks-at-a-glance)
- [Task 02: Stock Portfolio Performance Tracker](#task-02-stock-portfolio-performance-tracker)
- [Task 03: Smart File Organizer](#task-03-smart-file-organizer)
- [Task 04: Rule-Based Terminal Chatbot](#task-04-rule-based-terminal-chatbot)
- [Tools and technologies](#tools-and-technologies)
- [How to run any task](#how-to-run-any-task)
- [Experience and lessons learned](#experience-and-lessons-learned)
- [How I used AI tools](#how-i-used-ai-tools)

---

## Repository structure

```
Datheon_Python_Programming_Internship/
├── Task 02/                      # Stock Portfolio Performance Tracker
│   ├── backend/portfolio.py      # main script
│   ├── data/constituents.csv     # S&P 500 company list (provided)
│   ├── data/output/              # generated portfolio_summary.csv
│   └── README.md
├── Task 03/                      # Smart File Organizer
│   ├── organizer.py
│   ├── tests/
│   └── README.md
├── Task 04/                      # Rule-Based Terminal Chatbot
│   ├── chatbot.py
│   ├── data/sample_faq.json      # FAQ dataset (provided)
│   ├── tests/
│   └── README.md
└── README.md                     # this file
```

## Tasks at a glance

| Task | Project | Main skills practised | Run it |
|---|---|---|---|
| [02](Task%2002/) | Stock Portfolio Performance Tracker | dictionaries, input validation, CSV file I/O, formatted output | `python backend/portfolio.py` |
| [03](Task%2003/) | Smart File Organizer | `os.scandir`, `shutil`, exception handling, logging, CLI arguments | `python organizer.py <folder> --dry-run` |
| [04](Task%2004/) | Rule-Based Terminal Chatbot | regular expressions, JSON, intent scoring, state management | `python chatbot.py` |

On Windows you can use `py` instead of `python`.

---

## Task 02: Stock Portfolio Performance Tracker

**Goal:** an investment-tracking utility where the user enters stock holdings and the program reports performance and logs a summary to a CSV file.

**What it does**

- Interactive entry of holdings: ticker, buy price, number of shares and current price (type `done` to finish).
- Validates every ticker against the provided S&P 500 list (`data/constituents.csv`, 480 unique tickers after removing duplicate rows) and looks up the company name and sector.
- Rejects zero, negative and non-numeric input and asks again.
- Merges repeated tickers using the **weighted average cost** of the shares.
- Calculates per holding, plus portfolio totals:
  - invested = buy price x shares
  - market value = current price x shares
  - gain/loss = market value - invested
  - gain/loss % = (current - buy) / buy x 100
- Prints an aligned console table with a totals row and a **sector allocation** summary with a text bar chart.
- Appends each run to `data/output/portfolio_summary.csv` (header written once, one `TOTAL` row per run).
- Built only with the Python standard library, as small single-purpose functions.

**Example (simplified)**

```
Ticker  Shares   Buy $  Curr $  Invested    Value  Gain/Loss        %
AAPL     10.00  150.00  180.00   1500.00  1800.00    +300.00  +20.00%
TOTAL                            1500.00  1800.00    +300.00  +20.00%
```

**Run it:** from the `Task 02` folder, `python backend/portfolio.py`

---

## Task 03: Smart File Organizer

**Goal:** a desktop automation utility that tidies a cluttered folder (for example Downloads) by sorting files into category subfolders by extension.

**What it does**

- Reads each file's extension (case-insensitive) and maps it with a dictionary to `Documents`, `Images`, `Videos`, `Archives`, `Code` or `Others`.
- Scans with `os.scandir()` and relocates files with `shutil.move()`; category folders are created only when needed.
- **Never overwrites a file.** If the name already exists, the incoming file is renamed `name (1).ext`, `name (2).ext` and so on. The Python docs warn that `shutil.move` may overwrite an existing destination file depending on the platform, so collisions are checked before moving.
- Handles `PermissionError`, `FileNotFoundError` and other `OSError`s: the problem is logged and the run continues with the next file.
- Skips hidden files, symbolic links and the script itself, and refuses to run on drive roots or system folders.
- `--dry-run` previews every move without changing anything, and `--recursive` also organizes subfolders.
- Writes a log file (`logs/organizer.log`) and prints a formatted execution summary (files found, moved, renamed, skipped, errors, time, and a count per category).
- Covered by automated `pytest` tests that run on temporary folders, never on real user files.

**Example summary (format)**

```
================ ORGANIZER SUMMARY ================
Folder     : C:\Users\...\sandbox\messy_folder
Mode       : LIVE
Files found: 25
Moved      : 22
Renamed    : 2   (name collisions)
Skipped    : 2
Errors     : 1
---------------------------------------------------
```

**Run it:** from the `Task 03` folder, `python organizer.py <folder> --dry-run` to preview, then without `--dry-run` to sort.

---

## Task 04: Rule-Based Terminal Chatbot

**Goal:** an interactive customer-support assistant that answers questions from a JSON dataset using keywords, regular expressions and scoring, with no machine learning.

**What it does**

- **Data-driven:** every answer comes from `data/sample_faq.json`. Adding a new FAQ to the file makes the bot able to answer it with no code change.
- **Text normalization:** lowercase, punctuation removal, stop-word removal, simple stemming and a synonym dictionary, all with `re`.
- **Greeting detection with word boundaries** (`\b`), so "this" is not mistaken for "hi" and "they" is not mistaken for "hey". A greeting plus a question gets both a greeting and an answer.
- **Multi-intent matching:** a message such as "what are your hours and when will I get my certificate" is split into clauses and both questions are answered.
- **Confidence scoring:** a high score answers directly, a medium score asks "Did you mean ...?" and a low score gives a graceful fallback listing the available topics.
- **Business-hours context:** the hours answer adds whether support is OPEN or CLOSED right now (IST, UTC+05:30).
- **Conversation state machine** (`greeting -> listening -> clarifying -> ended`) and exit commands (`bye`, `exit`, `quit`).
- **Error handling:** clear messages for a missing or invalid dataset, empty input, and Ctrl+C, with no tracebacks.
- **32 automated tests** with `pytest`, using a fake clock for the hours logic.


**Run it:** from the `Task 04` folder, `python chatbot.py`. Run the tests with `python -m pytest`.

---

## Tools and technologies

| Category | Tools |
| Language | Python 3.14 (developed and tested on Windows) |
| Standard-library modules | `csv`, `json`, `re`, `os`, `shutil`, `pathlib`, `argparse`, `logging`, `datetime`, `enum`, `dataclasses` |
| Testing | `pytest` |
| Editors / IDEs | Visual Studio Code, Google Antigravity |
| Version control | Git and GitHub |
| Terminal | Windows PowerShell |
| AI assistance | Google Antigravity (code generation), Claude (mentoring and code review); see below |

## How to run any task

```bash
git clone https://github.com/SivaperumalMadushan/Datheon_Python_Programming_Internship.git
cd Datheon_Python_Programming_Internship
```

Each task needs only Python 3 and its own data files, which are already in the repository. Only the tests need an extra package: `python -m pip install pytest`.

---

## Experience and lessons learned

This internship was my first time working in VS Code, building command-line tools end to end, and publishing a multi-project repository. The biggest lessons:

- **Validate input and test with hand calculations.** In Task 02, checking one example by hand (10 shares bought at 150 and now worth 180 gives +20%) proved the maths. Reviewing the code also revealed that Python's `float()` accepts `nan` and `inf`, which bypass a simple `<= 0` check.
- **Real tools need safe defaults.** In Task 03, the official `shutil` docs showed that a move can silently overwrite an existing file. I added collision-safe renaming, a dry-run mode and a confirmation step so the tool can't destroy data.
- **Word boundaries matter in regex.** In Task 04, matching "hi" as a plain substring would trigger on "this". Using `\b` fixed it.
- **Data-driven design and tests that don't hardcode data.** My AI coding agent once rewrote my provided FAQ dataset. I found it by searching the files with PowerShell's `Select-String`, restored the original, and rewrote the tests to read their expected text from the dataset so they can't drift from the data again.
- **Environment debugging is part of the job.** On Windows, `python` showed a Microsoft Store message until I used the `py` launcher, and I learned about PATH and execution aliases.
- **Git workflow.** A rejected push taught me why you never force-push and how to organize one repository with one folder per task, cloning, copying and pulling before pushing.
- **Planning before coding.** Writing a precise specification first (features, edge cases, tests, definition of done) gave much better results than vague requests.

## How I used AI tools

I used AI assistants as a pair programmer and a mentor. Google Antigravity generated first drafts of the code from detailed written specifications, and Claude helped with planning, explaining concepts and reviewing code. I ran every project myself, tested edge cases, read the code, debugged , and can explain how each part works.
