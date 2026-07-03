"""Rule-to-taxonomy mapping (24 rules -> 8 types).

Maps each EX rule code to one of the 8 exception categories defined in
constants.py.
"""

from __future__ import annotations

from retail_ops_control_tower.constants import ExceptionType

# 24 rules mapped to 8 taxonomy types (PRD Section 5)
RULE_TO_TAXONOMY: dict[str, ExceptionType] = {
    "EX-03": ExceptionType.MISSING_CONFIRMATION,
    "EX-07": ExceptionType.MISSING_CONFIRMATION,
    "EX-01": ExceptionType.QUANTITY_MISMATCH,
    "EX-02": ExceptionType.QUANTITY_MISMATCH,
    "EX-04": ExceptionType.QUANTITY_MISMATCH,
    "EX-05": ExceptionType.QUANTITY_MISMATCH,
    "EX-06": ExceptionType.QUANTITY_MISMATCH,
    "EX-16": ExceptionType.QUANTITY_MISMATCH,
    "EX-17": ExceptionType.QUANTITY_MISMATCH,
    "EX-18": ExceptionType.QUANTITY_MISMATCH,
    "EX-23": ExceptionType.QUANTITY_MISMATCH,
    "EX-08": ExceptionType.LATE_SETUP,
    "EX-09": ExceptionType.LATE_SETUP,
    "EX-10": ExceptionType.STOCKOUT_RISK,
    "EX-11": ExceptionType.OVERSTOCK_RISK,
    "EX-12": ExceptionType.OVERSTOCK_RISK,
    "EX-13": ExceptionType.LOW_SELL_THROUGH,
    "EX-14": ExceptionType.LOW_SELL_THROUGH,
    "EX-15": ExceptionType.LOW_SELL_THROUGH,
    "EX-19": ExceptionType.LOW_SELL_THROUGH,
    "EX-20": ExceptionType.UNRESOLVED_ISSUE_AGING,
    "EX-21": ExceptionType.UNRESOLVED_ISSUE_AGING,
    "EX-22": ExceptionType.UNRESOLVED_ISSUE_AGING,
}
