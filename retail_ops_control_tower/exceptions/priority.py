"""Priority score formula.

    priority_score = (severity_weight * 100) + age_pressure + business_impact + campaign_urgency

    - severity_weight: Critical=3, Watch=2, Info=1
    - age_pressure: (days_open / sla_window_days) * 50, capped at 50
    - business_impact: hero SKU or flagship store = 30, standard = 15, low-velocity = 5
    - campaign_urgency: 20 if active launch window, 10 if active outside, 0 if no campaign

The PRD states a range of 1-200, but the formula and worked examples produce
scores up to 400 (critical severity * 100 = 300 alone). The formula is the
source of truth; the range cap is documented as a known discrepancy for v2
review.

Worked examples (PRD Section 9):
    1. Critical stockout, launch window: 3*100 + 50 + 30 + 20 = 400
    2. Watch qty mismatch, day 3:    2*100 + 50 + 15 + 0  = 265
    3. Info receiving variance, day 5: 1*100 + 50 + 5 + 0  = 155  (note: age 5/7*50=35.7 -> 135.7 -> 141 with rounding)
    4. Missing photo, flagship, day 2: 2*100 + 50 + 30 + 20 = 300
"""

from __future__ import annotations

from retail_ops_control_tower.constants import SEVERITY_WEIGHTS, Severity

# Business impact scores
BUSINESS_IMPACT_HERO = 30
BUSINESS_IMPACT_STANDARD = 15
BUSINESS_IMPACT_LOW = 5

# Campaign urgency scores
CAMPAIGN_URGENCY_LAUNCH = 20
CAMPAIGN_URGENCY_ACTIVE = 10
CAMPAIGN_URGENCY_NONE = 0


def compute_priority_score(
    severity: Severity,
    days_open: int,
    sla_window_days: int,
    business_impact: str,
    campaign_urgency: str,
) -> int:
    """Compute the priority score (1-200)."""
    severity_weight = SEVERITY_WEIGHTS[severity]
    age_pressure = min((days_open / max(sla_window_days, 1)) * 50, 50)

    impact_map = {
        "hero": BUSINESS_IMPACT_HERO,
        "flagship": BUSINESS_IMPACT_HERO,
        "standard": BUSINESS_IMPACT_STANDARD,
        "low-velocity": BUSINESS_IMPACT_LOW,
    }
    impact = impact_map.get(business_impact, BUSINESS_IMPACT_STANDARD)

    urgency_map = {
        "launch": CAMPAIGN_URGENCY_LAUNCH,
        "active": CAMPAIGN_URGENCY_ACTIVE,
        "none": CAMPAIGN_URGENCY_NONE,
    }
    urgency = urgency_map.get(campaign_urgency, CAMPAIGN_URGENCY_NONE)

    score = int(severity_weight * 100 + age_pressure + impact + urgency)
    return max(1, score)
