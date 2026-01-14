#!/usr/bin/env python3
"""
Process software detection for leads and generate SQL updates.

Reads leads from Supabase query, detects software via Railway API,
and outputs SQL statements for bulk update.
"""

import requests
import json
import time
import sys
from typing import Optional, Dict, List

RAILWAY_API_URL = "https://fastapi-production-85b6.up.railway.app/classify"
DELAY_BETWEEN_REQUESTS = 0.3  # seconds
BATCH_SIZE = 50  # Show progress every N leads


def detect_software(domain: str) -> Optional[str]:
    """Detect software via Railway API."""
    try:
        response = requests.post(
            RAILWAY_API_URL,
            json={"domain": domain},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Check each software with confidence threshold
            if data.get("uses_servicetitan") and data.get("confidence", 0) >= 0.95:
                return "ServiceTitan"
            elif data.get("uses_housecallpro") and data.get("confidence", 0) >= 0.95:
                return "Housecall Pro"
            elif data.get("uses_jobber") and data.get("confidence", 0) >= 0.95:
                return "Jobber"

        return None

    except Exception as e:
        print(f"Error for {domain}: {e}", file=sys.stderr)
        return None


def calculate_score(lead: Dict, software: Optional[str]) -> int:
    """Calculate score with detected software."""
    score = 0

    # Software (+15)
    if software:
        score += 15

    # Franchise (+10)
    if lead.get("is_franchise"):
        score += 10

    # Reviews
    reviews = lead.get("reviews_count") or 0
    if reviews >= 500:
        score += 10
    elif reviews >= 100:
        score += 7
    elif reviews >= 25:
        score += 4
    elif reviews >= 10:
        score += 2

    # LinkedIn (+3)
    if lead.get("company_linkedin"):
        score += 3

    # Domain (+2)
    if lead.get("domain"):
        score += 2

    return score


def get_tier(score: int) -> str:
    """Get tier from score."""
    if score >= 20:
        return "A"
    elif score >= 10:
        return "B"
    else:
        return "C"


def main():
    # Read leads from stdin (JSON array)
    print("Reading leads from stdin...", file=sys.stderr)
    leads = json.load(sys.stdin)
    total = len(leads)
    print(f"Loaded {total} leads", file=sys.stderr)
    print(file=sys.stderr)

    stats = {
        "processed": 0,
        "software_detected": 0,
        "servicetitan": 0,
        "jobber": 0,
        "housecall_pro": 0,
        "no_software": 0,
        "tier_changes": {"A": 0, "B": 0, "C": 0}
    }

    print("-- SQL Updates for Software Detection")
    print("-- Generated: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print()

    for i, lead in enumerate(leads, 1):
        domain = lead["domain"]
        old_tier = lead["tier"]

        # Detect software
        software = detect_software(domain)

        if software:
            stats["software_detected"] += 1

            if software == "ServiceTitan":
                stats["servicetitan"] += 1
            elif software == "Jobber":
                stats["jobber"] += 1
            elif software == "Housecall Pro":
                stats["housecall_pro"] += 1

            # Calculate new score and tier
            new_score = calculate_score(lead, software)
            new_tier = get_tier(new_score)

            # Output SQL
            print(f"UPDATE leads SET")
            print(f"  service_software = '{software}',")
            print(f"  score = {new_score},")
            print(f"  tier = '{new_tier}',")
            print(f"  enriched_at = NOW()")
            print(f"WHERE id = '{lead['id']}';")
            print()

            # Track tier changes
            if new_tier != old_tier:
                stats["tier_changes"][new_tier] += 1
                print(f"-- Tier change: {old_tier} → {new_tier}", file=sys.stderr)

        else:
            stats["no_software"] += 1

        stats["processed"] += 1

        # Progress
        if i % BATCH_SIZE == 0:
            pct = (i * 100) // total
            print(f"-- Progress: {i}/{total} ({pct}%) | Detected: {stats['software_detected']} | None: {stats['no_software']}", file=sys.stderr)

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    print(file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Total: {stats['processed']}", file=sys.stderr)
    print(f"Software Detected: {stats['software_detected']} ({stats['software_detected']*100//total}%)", file=sys.stderr)
    print(f"  - ServiceTitan: {stats['servicetitan']}", file=sys.stderr)
    print(f"  - Jobber: {stats['jobber']}", file=sys.stderr)
    print(f"  - Housecall Pro: {stats['housecall_pro']}", file=sys.stderr)
    print(f"No Software: {stats['no_software']}", file=sys.stderr)
    print(f"Tier Changes:", file=sys.stderr)
    print(f"  - To A-Tier: {stats['tier_changes']['A']}", file=sys.stderr)
    print(f"  - To B-Tier: {stats['tier_changes']['B']}", file=sys.stderr)
    print(file=sys.stderr)


if __name__ == "__main__":
    main()
