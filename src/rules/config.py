"""
Configuration constants for deterministic risk rules (R01 - R04).

All rule thresholds and windows are defined here as named configuration constants
to ensure maintainability, determinism, and clear documentation.
"""

# R01: Unusually Large Transfer Configuration
R01_AMOUNT_PERCENTILE_KEY = "p95"  # Compare transaction amount against customer P95 baseline

# R02: Burst to a Newly Added Payee Configuration
R02_BURST_WINDOW_HOURS = 24  # Time window (in hours) to evaluate payee transaction concentration
R02_BURST_MIN_TRANSACTIONS = 3  # Minimum transaction count within window to trigger a burst

# R03: Odd-Hours Activity Configuration
# Documented deterministic window: 00:00 through 04:59 inclusive
R03_ODD_HOURS_START = 0  # Hour 0 (00:00)
R03_ODD_HOURS_END = 5    # Hour 5 (05:00 exclusive upper bound, so 00:00 to 04:59)

# R04: Established Pattern Deviation Configuration
R04_AMOUNT_PERCENTILE_KEY = "p75"  # Amount threshold for pattern deviation check
