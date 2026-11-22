# 📈 Stock Portfolio Performance Tracker

A command-line Python application that lets you track the performance of your
stock portfolio using S&P 500 companies as the reference universe.
Enter your holdings interactively, and the script calculates gain/loss,
prints an aligned report, and saves results to a CSV file — all with
**zero external dependencies** (standard library only).

---

## Folder Structure

```
Task 02/
├── data/
│   ├── constituents.csv        ← S&P 500 reference data (ticker, company, sector)
│   └── output/
│       └── portfolio_summary.csv   ← generated on first run
├── backend/
│   ├── portfolio.py            ← Phase 1 console script  ← run this
│   ├── requirements.txt        ← Phase 2 API dependencies (placeholder)
│   ├── .env.example            ← MongoDB connection string template
│   └── app/
│       ├── __init__.py         ← Phase 2 placeholder
│       ├── main.py             ← Phase 2 placeholder
│       ├── db.py               ← Phase 2 placeholder
│       ├── routers/            ← Phase 2 placeholder
│       └── services/           ← Phase 2 placeholder
├── tests/                      ← Phase 2 placeholder
├── database/
│   ├── seed_securities.py      ← Phase 2 placeholder
│   ├── create_indexes.py       ← Phase 2 placeholder
│   └── schema.md               ← Phase 2 placeholder
├── docs/                       ← Phase 3 placeholder
├── README.md
└── .gitignore
```

---

## How to Run (Phase 1)

No installation needed — Python 3.8+ is all you need.

```bash
# From the project root (Task 02/)
python backend/portfolio.py
```

The script will:
1. Prompt you for ticker symbols (e.g. `AAPL`, `MSFT`, `TSLA`)
2. Ask for buy price, number of shares, and current price for each
3. Print a performance table in the console
4. Append results to `data/output/portfolio_summary.csv`

### Example session

```
Enter ticker symbol (or 'done' to finish): AAPL
  Buy price for AAPL ($): 150
  Number of shares for AAPL: 10
  Current price for AAPL ($): 180
  ✔  Added AAPL to your portfolio.

Enter ticker symbol (or 'done' to finish): done
```

Expected output:
```
Ticker   Company                      Sector                     Shares   Buy $  Curr $     Invested        Value    Gain/Loss         %
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
AAPL    Apple Inc.                   Information Technology      10.00   150.00  180.00      1500.00      1800.00      +300.00  +20.00%
```

---

## Validation

| Input       | Behaviour                                        |
|-------------|--------------------------------------------------|
| `ZZZZ`      | ❌ Rejected — not in the S&P 500 list            |
| `-50` price | ❌ Rejected — must be greater than 0             |
| `abc` price | ❌ Rejected — not a valid number                 |
| `AAPL` twice| ✔ Merged — weighted average buy price, shares added |

---

## Roadmap

| Phase | Description                              | Status      |
|-------|------------------------------------------|-------------|
| **1** | Console script (`portfolio.py`)          | ✅ Complete  |
| **2** | REST API with FastAPI + MongoDB backend  | 🔜 Planned   |
| **3** | React Native / Expo mobile app           | 🔜 Planned   |

---

## Project Info

- **Internship:** Datheon Python Programming Internship
- **Task:** 02 — Stock Portfolio Performance Tracker
- **Language:** Python 3.8+
- **Dependencies (Phase 1):** None (standard library only)
