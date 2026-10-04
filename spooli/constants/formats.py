"""Display formats, numeric precision, and table layouts for Spooli."""

# Decimal precision used across the application.
MONEY_DECIMALS = 4
GRAMS_DECIMALS = 2
WEIGHT_DECIMALS = 1
PERCENT_DECIMALS = 0

# Ready-to-use format specs, e.g. f"{value:{MONEY_FORMAT}}".
MONEY_FORMAT = f".{MONEY_DECIMALS}f"
GRAMS_FORMAT = f".{GRAMS_DECIMALS}f"

# Inventory table column widths, in characters.
COL_ID_WIDTH = 5
COL_BRAND_WIDTH = 15
COL_MATERIAL_WIDTH = 10
COL_COLOR_WIDTH = 12
COL_REMAINING_WIDTH = 16

# Print history table column widths, in characters.
COL_HISTORY_FILE_WIDTH = 28
COL_HISTORY_SPOOL_WIDTH = 7
COL_HISTORY_GRAMS_WIDTH = 8
COL_HISTORY_COST_WIDTH = 12
# The currency symbol is printed before the value, so it gets its own column.
COL_HISTORY_COST_VALUE_WIDTH = COL_HISTORY_COST_WIDTH - 1

# Recent-print table column widths, in characters.
COL_RECENT_ID_WIDTH = 6
COL_RECENT_FILE_WIDTH = 30
COL_RECENT_GRAMS_WIDTH = 10
RECENT_SEPARATOR_WIDTH = 60

# File name truncation limits for table cells.
FILE_NAME_HISTORY_LIMIT = 28
FILE_NAME_RECENT_LIMIT = 30

# Affirmative answers accepted by interactive confirmations.
YES_TOKENS = ("y", "yes", "s", "si", "sí")
