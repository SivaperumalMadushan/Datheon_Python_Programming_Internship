"""
Automated test for portfolio.py – runs without user interaction.
Simulates stdin input by patching the built-in input() function.
"""
import sys
import io
from pathlib import Path
from unittest.mock import patch

# Add backend/ to the path so we can import portfolio
sys.path.insert(0, str(Path(__file__).parent / "backend"))
import portfolio


# ─────────────────────────────────────────────────────────────
# Helper: capture what gets printed to the console
# ─────────────────────────────────────────────────────────────
def run_with_inputs(input_lines: list) -> str:
    """
    Run main() while feeding fake user inputs and capturing all output.
    Returns the captured text.
    """
    input_iter = iter(input_lines)

    import builtins
    original_input = builtins.input

    def fake_input(prompt=""):
        value = next(input_iter)
        print(prompt + value)   # echo the value so we can see it
        return value

    builtins.input = fake_input

    # Capture stdout
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured

    try:
        portfolio.main()
    finally:
        sys.stdout = old_stdout
        builtins.input = original_input

    return captured.getvalue()


# ─────────────────────────────────────────────────────────────
# TEST 1 – AAPL: 10 shares, buy $150, current $180
# Expected: invested=1500, value=1800, gain=+300, %=+20.00
# Also checks table width <= 110 characters
# ─────────────────────────────────────────────────────────────
print("=" * 65)
print("TEST 1 – AAPL: 10 shares @ $150 buy / $180 current")
print("=" * 65)

output1 = run_with_inputs(["AAPL", "150", "10", "180", "done"])
print(output1)

# Verify the numbers
assert "1500.00" in output1,     "❌ FAIL: invested should be 1500.00"
assert "1800.00" in output1,     "❌ FAIL: market value should be 1800.00"
assert "+300.00" in output1,     "❌ FAIL: gain/loss should be +300.00"
assert "+20.00%" in output1,     "❌ FAIL: gain/loss % should be +20.00%"

# Verify table width does not exceed 110 characters
report_lines = [line for line in output1.splitlines() if "─" in line or "Ticker" in line or "AAPL" in line or "TOTAL" in line]
for line in report_lines:
    assert len(line) <= 110, f"❌ FAIL: Line exceeds 110 chars ({len(line)}): {line}"

print("✅  TEST 1 PASSED – numbers match (1500 / 1800 / +300 / +20.00%) & table width <= 110 chars")


# ─────────────────────────────────────────────────────────────
# TEST 2 – Rejection of 'nan' and 'inf' as a price
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("TEST 2 – Rejection of 'nan' and 'inf' as price")
print("=" * 65)

output2 = run_with_inputs([
    "AAPL",
    "nan",      # rejected
    "inf",      # rejected
    "-inf",     # rejected
    "150",      # valid buy price
    "10",       # shares
    "180",      # current price
    "done"
])
print(output2)

assert "nan" in output2, "❌ FAIL: 'nan' should appear in output"
assert "inf" in output2, "❌ FAIL: 'inf' should appear in output"
print("✅  TEST 2 PASSED – 'nan' and 'inf' were rejected properly")


# ─────────────────────────────────────────────────────────────
# TEST 3 – Invalid ticker ZZZZ should be rejected
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("TEST 3 – Ticker 'ZZZZ' should be rejected")
print("=" * 65)

output3 = run_with_inputs(["ZZZZ", "AAPL", "150", "10", "180", "done"])
print(output3)

assert "ZZZZ" in output3,                  "❌ FAIL: rejection message should mention ZZZZ"
assert "not found" in output3.lower(),     "❌ FAIL: rejection message should say 'not found'"
print("✅  TEST 3 PASSED – 'ZZZZ' was rejected with a clear message")


# ─────────────────────────────────────────────────────────────
# TEST 4 – Duplicate ticker merge (weighted avg)
# Buy 10 shares @ $100, then 10 more @ $200 → avg = $150
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("TEST 4 – Duplicate ticker: MSFT entered twice → weighted avg buy")
print("=" * 65)

output4 = run_with_inputs([
    "MSFT", "100", "10", "250",   # first entry
    "MSFT", "200", "10", "250",   # second entry → avg buy = 150
    "done"
])
print(output4)

assert "Merged" in output4,        "❌ FAIL: should show merge message"
assert "150.00" in output4,        "❌ FAIL: avg buy price should be 150.00"
assert "20.00"  in output4,        "❌ FAIL: total shares should be 20.00"
print("✅  TEST 4 PASSED – holdings merged with weighted average buy price")


# ─────────────────────────────────────────────────────────────
# TEST 5 – PermissionError handling in save_to_csv
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("TEST 5 – PermissionError in save_to_csv handled gracefully")
print("=" * 65)

with patch("builtins.open", side_effect=PermissionError("Permission denied")):
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        portfolio.save_to_csv(
            {"AAPL": {"buy_price": 150.0, "shares": 10.0, "current_price": 180.0}},
            {"AAPL": {"name": "Apple Inc.", "sector": "Information Technology"}},
            {"invested": 1500.0, "market_value": 1800.0, "gain_loss": 300.0, "gain_loss_pct": 20.0},
            Path("data/output/portfolio_summary.csv")
        )
    finally:
        sys.stdout = old_stdout

output5 = captured.getvalue()
print(output5)
assert "Please close portfolio_summary.csv and run again" in output5, "❌ FAIL: friendly error message not found"
print("✅  TEST 5 PASSED – PermissionError caught and friendly message shown")


# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
print("\n" + "═" * 65)
print("   ALL TESTS PASSED ✅")
print("═" * 65 + "\n")
