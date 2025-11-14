"""
Simplified consequence checker for destructive Movi agent requests.

The helper inspects natural-language requests, fetches trip metadata, and emits
the exact warning copy required by the assignment when bookings exist.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from database.client import get_client

logger = logging.getLogger(__name__)

WARNING_TEMPLATE = (
    "I can remove the vehicle. However, please be aware the '{trip}' trip is already "
    "{percent}% booked by employees. Removing the vehicle will cancel these bookings "
    "and a trip-sheet will fail to generate. Do you want to proceed?"
)

TRIP_NAME_REGEX = re.compile(r"'([^']+)'|\"([^\"]+)\"")
DESTRUCTIVE_KEYWORDS = ("remove", "delete", "unassign", "cancel")


@dataclass
class ConsequenceWarning:
    trip_name: str
    trip_id: int
    booking_percentage: float
    total_bookings: int
    message: str
    deployment_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


def analyze_trip_removal_request(message: str) -> Optional[ConsequenceWarning]:
    """Return a warning if the message targets a booked trip."""

    if not message:
        return None

    lowered = message.lower()
    if not any(word in lowered for word in DESTRUCTIVE_KEYWORDS):
        return None
    if "vehicle" not in lowered and "deployment" not in lowered:
        return None

    trip_name = _extract_trip_name(message)
    if not trip_name:
        return None

    record = _fetch_trip(trip_name)
    if not record:
        return None

    bookings = float(record.get("booking_status_percentage") or 0)
    total = int(record.get("total_bookings") or 0)
    if bookings <= 0 and total <= 0:
        return None

    message_text = WARNING_TEMPLATE.format(
        trip=trip_name, percent=int(bookings or 0)
    )

    trip_id = int(record.get("trip_id"))
    deployment = _fetch_active_deployment(trip_id)
    deployment_id = (
        int(deployment.get("deployment_id")) if deployment and deployment.get("deployment_id") else None
    )

    return ConsequenceWarning(
        trip_name=trip_name,
        trip_id=trip_id,
        booking_percentage=bookings,
        total_bookings=total,
        message=message_text,
        deployment_id=deployment_id,
        metadata={"trip": record, "deployment": deployment},
    )


def _extract_trip_name(text: str) -> Optional[str]:
    match = TRIP_NAME_REGEX.search(text)
    if not match:
        return None
    return (match.group(1) or match.group(2) or "").strip()


def _fetch_trip(trip_name: str) -> Optional[Dict[str, Any]]:
    client = get_client()
    try:
        exact = (
            client.table("daily_trips")
            .select("*")
            .eq("display_name", trip_name)
            .limit(1)
            .execute()
        )
        if exact.data:
            return exact.data[0]

        fuzzy = (
            client.table("daily_trips")
            .select("*")
            .ilike("display_name", f"%{trip_name}%")
            .limit(1)
            .execute()
        )
        if fuzzy.data:
            return fuzzy.data[0]
    except Exception as err:  # pragma: no cover - defensive log only
        logger.warning("Trip lookup failed for '%s': %s", trip_name, err)
    return None


def _fetch_active_deployment(trip_id: int) -> Optional[Dict[str, Any]]:
    if not trip_id:
        return None
    client = get_client()
    try:
        result = (
            client.table("deployments")
            .select("*")
            .eq("trip_id", trip_id)
            .is_("deleted_at", None)
            .order("assigned_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception as err:  # pragma: no cover - defensive log only
        logger.warning("Deployment lookup failed for trip %s: %s", trip_id, err)
    return None


__all__ = ["ConsequenceWarning", "analyze_trip_removal_request"]


