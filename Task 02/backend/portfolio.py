"""
backend/portfolio.py
─────────────────────────────────────────────────────────────────────────────
Stock Portfolio Performance Tracker  –  Phase 1 (Console Script)
─────────────────────────────────────────────────────────────────────────────

What this script does:
  1. Loads the S&P 500 company list (data/constituents.csv) so it can
     validate ticker symbols and look up company names / sectors.
  2. Asks the user to enter one or more stock holdings interactively.
  3. Calculates performance metrics for each holding.
  4. Prints a nicely aligned table in the console.
  5. Saves the results to data/output/portfolio_summary.csv.

Standard library only – no pip installs needed.
"""

import csv                        # reading/writing CSV files
from datetime import datetime     # timestamps for the output file
import math                       # checking for finite numbers (reject nan/inf)
from pathlib import Path          # cross-platform file paths

# ─────────────────────────────────────────────────────────────────────────────
# File paths
#   Path(__file__)         → absolute path of this script
#   .resolve()             → resolve any symlinks
#   .parent                → backend/ folder
#   .parent.parent         → project root (Task 02/)
# ─────────────────────────────────────────────────────────────────────────────
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent          # Task 02/
_DATA_DIR = _PROJECT_ROOT / "data"               # Task 02/data/
_OUTPUT_DIR = _DATA_DIR / "output"               # Task 02/data/output/

CSV_INPUT = _DATA_DIR / "constituents.csv"        # S&P 500 reference data
CSV_OUTPUT = _OUTPUT_DIR / "portfolio_summary.csv"  # results go here


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 1 – load_securities
# ═════════════════════════════════════════════════════════════════════════════
def load_securities(csv_path: Path) -> dict:
    """
    Read constituents.csv and build a lookup dictionary.

    Returns:
        {
            "AAPL": {"name": "Apple Inc.", "sector": "Information Technology"},
            "MSFT": {"name": "Microsoft",  "sector": "Information Technology"},
            ...
        }
    """
    securities = {}

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)      # reads the header row automatically
        for row in reader:
            ticker = row["Symbol"].strip().upper()
            securities[ticker] = {
                "name":   row["Security"].strip(),
                "sector": row["GICS Sector"].strip(),
            }

    return securities


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 2 – get_valid_ticker
# ═════════════════════════════════════════════════════════════════════════════
def get_valid_ticker(securities: dict):
    """
    Prompt the user for a ticker symbol and validate it.

    Rules:
      - Input is automatically converted to uppercase (so "aapl" → "AAPL").
      - Typing 'done' (any case) finishes the input loop → returns None.
      - Any ticker not found in the S&P 500 list is rejected and re-asked.

    Returns:
        str  – a valid ticker that exists in `securities`
        None – the user typed 'done'
    """
    while True:
        raw = input("\nEnter ticker symbol (or 'done' to finish): ").strip()

        # Allow the user to signal they are finished
        if raw.lower() == "done":
            return None

        ticker = raw.upper()

        # Check the S&P 500 list
        if ticker in securities:
            return ticker

        # Ticker not found – explain clearly and loop
        print(f"  ❌  '{ticker}' was not found in the S&P 500 list.")
        print("      Please check the symbol and try again.")


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 3 – get_positive_number
# ═════════════════════════════════════════════════════════════════════════════
def get_positive_number(prompt: str) -> float:
    """
    Prompt the user for a positive number and keep asking until they give one.

    Rules:
      - Non-numeric text is rejected.
      - Zero and negative numbers are rejected.

    Returns:
        float – a valid positive number
    """
    while True:
        raw = input(prompt).strip()

        # Try converting to float
        try:
            value = float(raw)
        except ValueError:
            print(f"  ❌  '{raw}' is not a valid number. Please enter a positive value.")
            continue

        # Reject nan, inf, -inf
        if not math.isfinite(value):
            print(f"  ❌  '{raw}' is not a valid number. Please enter a positive, finite value.")
            continue

        # Must be greater than zero
        if value <= 0:
            print(f"  ❌  Value must be greater than 0. You entered: {value}")
            continue

        return value


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 4 – add_holding
# ═════════════════════════════════════════════════════════════════════════════
def add_holding(
    holdings: dict,
    ticker: str,
    buy_price: float,
    shares: float,
    current_price: float,
) -> None:
    """
    Add a new holding or merge it with an existing one.

    The holdings dict maps: ticker → {buy_price, shares, current_price}

    Merge rules (when the same ticker is entered a second time):
      ┌────────────────┬─────────────────────────────────────────────────────┐
      │ Field          │ Rule                                                │
      ├────────────────┼─────────────────────────────────────────────────────┤
      │ shares         │ old shares + new shares                             │
      │ buy_price      │ weighted average cost:                              │
      │                │   (old_buy × old_shares + new_buy × new_shares)    │
      │                │   ÷ total_shares                                    │
      │ current_price  │ newest value wins (overwritten)                     │
      └────────────────┴─────────────────────────────────────────────────────┘
    """
    if ticker in holdings:
        # ── Merge ──────────────────────────────────────────────
        old = holdings[ticker]
        total_shares = old["shares"] + shares

        # Weighted average buy price (preserves the true cost basis)
        avg_buy = (
            (old["buy_price"] * old["shares"]) + (buy_price * shares)
        ) / total_shares

        holdings[ticker] = {
            "buy_price":     avg_buy,
            "shares":        total_shares,
            "current_price": current_price,   # newest price wins
        }
        print(
            f"  ✔  Merged {ticker}: "
            f"{total_shares:.2f} total shares, "
            f"avg buy price ${avg_buy:.2f}"
        )
    else:
        # ── New holding ────────────────────────────────────────
        holdings[ticker] = {
            "buy_price":     buy_price,
            "shares":        shares,
            "current_price": current_price,
        }
        print(f"  ✔  Added {ticker} to your portfolio.")


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 5 – calculate_holding
# ═════════════════════════════════════════════════════════════════════════════
def calculate_holding(holding: dict) -> dict:
    """
    Compute performance metrics for a single stock holding.

    Formulas:
        invested      = buy_price  × shares
        market_value  = current_price × shares
        gain_loss     = market_value − invested
        gain_loss_pct = (current_price − buy_price) / buy_price × 100

    Returns a dict with the four computed values.
    """
    buy_price     = holding["buy_price"]
    shares        = holding["shares"]
    current_price = holding["current_price"]

    invested      = buy_price     * shares
    market_value  = current_price * shares
    gain_loss     = market_value  - invested
    gain_loss_pct = (current_price - buy_price) / buy_price * 100

    return {
        "invested":      invested,
        "market_value":  market_value,
        "gain_loss":     gain_loss,
        "gain_loss_pct": gain_loss_pct,
    }


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 6 – calculate_totals
# ═════════════════════════════════════════════════════════════════════════════
def calculate_totals(holdings: dict) -> dict:
    """
    Sum the invested capital and market value across every holding.
    Derive overall gain/loss from those sums (not by averaging percentages).

    Returns a dict with portfolio-wide totals.
    """
    total_invested     = 0.0
    total_market_value = 0.0

    for holding in holdings.values():
        metrics = calculate_holding(holding)
        total_invested     += metrics["invested"]
        total_market_value += metrics["market_value"]

    total_gain_loss = total_market_value - total_invested

    # Avoid division by zero if somehow everything is 0
    if total_invested != 0:
        total_gain_loss_pct = total_gain_loss / total_invested * 100
    else:
        total_gain_loss_pct = 0.0

    return {
        "invested":      total_invested,
        "market_value":  total_market_value,
        "gain_loss":     total_gain_loss,
        "gain_loss_pct": total_gain_loss_pct,
    }


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 7 – sector_allocation
# ═════════════════════════════════════════════════════════════════════════════
def sector_allocation(holdings: dict, securities: dict) -> dict:
    """
    Group market value by GICS sector and return each sector's
    percentage of the total portfolio market value.

    Returns:
        { "Information Technology": 65.00, "Health Care": 35.00, ... }
    """
    sector_totals = {}   # { sector_name: cumulative_market_value }

    for ticker, holding in holdings.items():
        sector       = securities[ticker]["sector"]
        metrics      = calculate_holding(holding)
        market_value = metrics["market_value"]

        # Add this holding's value to its sector bucket
        sector_totals[sector] = sector_totals.get(sector, 0.0) + market_value

    total_portfolio_value = sum(sector_totals.values())

    # Convert raw values to percentages
    sector_pct = {}
    for sector, value in sector_totals.items():
        if total_portfolio_value != 0:
            sector_pct[sector] = value / total_portfolio_value * 100
        else:
            sector_pct[sector] = 0.0

    return sector_pct


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 8 – print_report
# ═════════════════════════════════════════════════════════════════════════════
def print_report(holdings: dict, securities: dict, totals: dict) -> None:
    """
    Print a formatted performance table to the console.

    Layout:
      ┌──────────────────────────────────── header ─────┐
      │ Ticker | Company | Sector | Shares | Buy$ | ... │
      ├──── one row per holding ────────────────────────┤
      │ TOTAL row                                       │
      └─────────────────────────────────────────────────┘
      Then a sector allocation summary below.
    """

    # ── Helper: format a number with an explicit +/- sign ──────────────────
    def signed(value: float, decimals: int = 2) -> str:
        """Return a string like '+300.00' or '-45.50'."""
        prefix = "+" if value >= 0 else ""    # minus is added automatically
        return f"{prefix}{value:.{decimals}f}"

    # ── Helper: truncate text and append '...' if it exceeds width ────────
    def truncate(text: str, width: int) -> str:
        """Fit text into width chars; append '...' if it had to be cut."""
        if len(text) <= width:
            return text
        if width <= 3:
            return text[:width]
        return text[:width - 3] + "..."

    # ── Column widths (characters) ─────────────────────────────────────────
    # Total table width = sum(widths) + 9 spaces = 101 + 9 = 110 characters
    W = {
        "ticker":   7,
        "company": 14,
        "sector":   9,
        "shares":   8,
        "buy":      9,
        "current":  9,
        "invested": 12,
        "value":   12,
        "gain":    12,
        "pct":      9,
    }

    # ── Build header string ────────────────────────────────────────────────
    header = (
        f"{'Ticker':<{W['ticker']}} "
        f"{'Company':<{W['company']}} "
        f"{'Sector':<{W['sector']}} "
        f"{'Shares':>{W['shares']}} "
        f"{'Buy $':>{W['buy']}} "
        f"{'Curr $':>{W['current']}} "
        f"{'Invested':>{W['invested']}} "
        f"{'Value':>{W['value']}} "
        f"{'Gain/Loss':>{W['gain']}} "
        f"{'%':>{W['pct']}}"
    )
    separator = "─" * len(header)

    # ── Print header ───────────────────────────────────────────────────────
    print("\n" + separator)
    print("  STOCK PORTFOLIO PERFORMANCE REPORT")
    print(separator)
    print(header)
    print(separator)

    # ── Print one row per holding ──────────────────────────────────────────
    for ticker, holding in holdings.items():
        info    = securities[ticker]
        metrics = calculate_holding(holding)

        # Truncate long names with "..." so they fit in the column
        company = truncate(info["name"],   W["company"])
        sector  = truncate(info["sector"], W["sector"])

        # Format gain/loss values as signed strings, then right-align them
        gain_str = signed(metrics["gain_loss"])
        pct_str  = signed(metrics["gain_loss_pct"]) + "%"

        row = (
            f"{ticker:<{W['ticker']}} "
            f"{company:<{W['company']}} "
            f"{sector:<{W['sector']}} "
            f"{holding['shares']:>{W['shares']}.2f} "
            f"{holding['buy_price']:>{W['buy']}.2f} "
            f"{holding['current_price']:>{W['current']}.2f} "
            f"{metrics['invested']:>{W['invested']}.2f} "
            f"{metrics['market_value']:>{W['value']}.2f} "
            f"{gain_str:>{W['gain']}} "
            f"{pct_str:>{W['pct']}}"
        )
        print(row)

    # ── Totals row ─────────────────────────────────────────────────────────
    print(separator)

    total_gain_str = signed(totals["gain_loss"])
    total_pct_str  = signed(totals["gain_loss_pct"]) + "%"

    # Build the label section (left side of the totals row)
    label_width = (
        W["ticker"] + 1 +
        W["company"] + 1 +
        W["sector"] + 1 +
        W["shares"] + 1 +
        W["buy"] + 1 +
        W["current"]
    )
    totals_row = (
        f"{'TOTAL':<{label_width}} "
        f"{totals['invested']:>{W['invested']}.2f} "
        f"{totals['market_value']:>{W['value']}.2f} "
        f"{total_gain_str:>{W['gain']}} "
        f"{total_pct_str:>{W['pct']}}"
    )
    print(totals_row)
    print(separator)

    # ── Sector allocation summary ──────────────────────────────────────────
    alloc = sector_allocation(holdings, securities)

    print("\n  SECTOR ALLOCATION  (% of total portfolio value)")
    print("─" * 55)

    # Sort sectors from largest to smallest allocation
    for sector, pct in sorted(alloc.items(), key=lambda item: -item[1]):
        # Simple ASCII bar chart: one block per 2%
        bar = "█" * max(1, int(pct / 2))
        print(f"  {sector:<30}  {pct:>6.2f}%  {bar}")

    print("─" * 55 + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 9 – save_to_csv
# ═════════════════════════════════════════════════════════════════════════════
def save_to_csv(
    holdings: dict,
    securities: dict,
    totals: dict,
    output_path: Path,
) -> None:
    """
    Append this run's results to the portfolio_summary.csv file.

    Behaviour:
      - Creates data/output/ folder automatically if it does not exist.
      - Writes the CSV header ONLY when the file does not yet exist.
      - Appends one data row per holding.
      - Appends a TOTAL row at the end of each run so you can tell runs apart.
    """
    # Create the output folder if it doesn't exist yet
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Decide whether to write the header
    file_is_new = not output_path.exists()

    # Column names (must match the order we write data)
    fieldnames = [
        "timestamp",
        "ticker",
        "company",
        "sector",
        "shares",
        "buy_price",
        "current_price",
        "invested",
        "market_value",
        "gain_loss",
        "gain_loss_pct",
    ]

    # Timestamp for every row in this run
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Open in APPEND mode so previous runs are not erased
    try:
        with open(output_path, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Header: only once, when the file is brand new
            if file_is_new:
                writer.writeheader()

            # One data row per holding
            for ticker, holding in holdings.items():
                info    = securities[ticker]
                metrics = calculate_holding(holding)

                writer.writerow({
                    "timestamp":      timestamp,
                    "ticker":         ticker,
                    "company":        info["name"],
                    "sector":         info["sector"],
                    "shares":         round(holding["shares"], 2),
                    "buy_price":      round(holding["buy_price"], 2),
                    "current_price":  round(holding["current_price"], 2),
                    "invested":       round(metrics["invested"], 2),
                    "market_value":   round(metrics["market_value"], 2),
                    "gain_loss":      round(metrics["gain_loss"], 2),
                    "gain_loss_pct":  round(metrics["gain_loss_pct"], 2),
                })

            # TOTAL row for this run
            writer.writerow({
                "timestamp":      timestamp,
                "ticker":         "TOTAL",
                "company":        "",
                "sector":         "",
                "shares":         "",
                "buy_price":      "",
                "current_price":  "",
                "invested":       round(totals["invested"], 2),
                "market_value":   round(totals["market_value"], 2),
                "gain_loss":      round(totals["gain_loss"], 2),
                "gain_loss_pct":  round(totals["gain_loss_pct"], 2),
            })

        print(f"  ✔  Results saved → {output_path}")
    except PermissionError:
        print("  ❌  Could not write to portfolio_summary.csv.")
        print("      Please close portfolio_summary.csv and run again.")


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 10 – main
# ═════════════════════════════════════════════════════════════════════════════
def main() -> None:
    """
    Orchestrate the whole program in five steps:
      1. Load the S&P 500 reference data.
      2. Collect holdings from the user (interactive loop).
      3. Calculate portfolio totals.
      4. Print the report to the console.
      5. Save results to portfolio_summary.csv.
    """
    # ── Banner ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 65)
    print("   📈  Stock Portfolio Performance Tracker  –  Phase 1")
    print("═" * 65)

    # ── Step 1: Load the securities reference data ─────────────────────────
    if not CSV_INPUT.exists():
        print(f"\n❌  Cannot find: {CSV_INPUT}")
        print("    Make sure data/constituents.csv is in the project root.")
        return

    securities = load_securities(CSV_INPUT)
    print(f"\n✔  Loaded {len(securities)} S&P 500 securities from constituents.csv")

    # ── Step 2: Interactive input loop ─────────────────────────────────────
    # holdings maps:  ticker (str) → {buy_price, shares, current_price}
    holdings: dict = {}

    print("\n  Enter your stock holdings below.")
    print("  Type 'done' when you have finished entering all holdings.\n")

    while True:
        ticker = get_valid_ticker(securities)

        # None means the user typed 'done'
        if ticker is None:
            break

        # Ask for the three numbers – each is re-asked until valid
        buy_price     = get_positive_number(f"  Buy price for {ticker} ($): ")
        shares        = get_positive_number(f"  Number of shares for {ticker}: ")
        current_price = get_positive_number(f"  Current price for {ticker} ($): ")

        # Add (or merge) this holding into the dict
        add_holding(holdings, ticker, buy_price, shares, current_price)

    # ── Guard: nothing was entered ─────────────────────────────────────────
    if not holdings:
        print("\n⚠  No holdings were entered. Exiting.\n")
        return

    # ── Step 3: Calculate portfolio-wide totals ────────────────────────────
    totals = calculate_totals(holdings)

    # ── Step 4: Print the report ───────────────────────────────────────────
    print_report(holdings, securities, totals)

    # ── Step 5: Save to CSV ────────────────────────────────────────────────
    save_to_csv(holdings, securities, totals, CSV_OUTPUT)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point – this block runs only when you execute the script directly:
#   python backend/portfolio.py
# It does NOT run if another script imports this file as a module.
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
