"""PhotoProof dataclass (13 fields).

Table: photo_proofs - photo proof metadata records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhotoProof:
    """One row in the photo_proofs table."""

    photo_id: str
    confirmation_id: str
    visit_id: str
    store_id: str
    campaign_id: str
    photo_type: str  # e.g. "posm", "planogram", "pricing", "display"
    photo_timestamp: str
    gps_lat: float
    gps_lon: float
    user_id: str
    validation_status: str  # "pass", "fail", "pending"
    validation_notes: str
    file_ref: str
