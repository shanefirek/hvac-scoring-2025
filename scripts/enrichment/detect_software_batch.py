#!/usr/bin/env python3
"""
Process software detection for Dec 7 leads in batches.

This script processes leads through Railway API to detect ServiceTitan,
Jobber, or Housecall Pro, then outputs SQL statements to update Supabase.
"""

import requests
import time
import sys

RAILWAY_API_URL = "https://fastapi-production-85b6.up.railway.app/classify"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# Sample leads to process (will be replaced with full set)
LEADS = [
    {"id": "ea1512d8-8fac-4233-b6d2-ad94f667a444", "domain": "sullivanservice.com", "tier": "B", "score": 12, "reviews_count": 3720},
    {"id": "447ac6b2-f993-448d-9e0c-4a6832551946", "domain": "charlesheatingandair.com", "tier": "B", "score": 12, "reviews_count": 2561},
    {"id": "f565829a-b3c1-4bd3-bdda-5cf963ff755a", "domain": "johnbetlem.com", "tier": "B", "score": 15, "reviews_count": 2454},
    {"id": "d5988e7a-92aa-4cf9-8126-b7172c5ab0db", "domain": "falsoserviceexperts.com", "tier": "B", "score": 15, "reviews_count": 2054},
    {"id": "a81c520f-5425-451d-ac1a-213c3047dab5", "domain": "bestbrooklynplumber.com", "tier": "B", "score": 15, "reviews_count": 1983},
]


def detect_software(domain):
    """Call Railway API to detect software."""
    try:
        response = requests.post(
            RAILWAY_API_URL,
            json={"domain": domain},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Check each software type with 95% confidence threshold
            if data.get("uses_servicetitan") and data.get("confidence", 0) >= 0.95:
                return "ServiceTitan"
            elif data.get("uses_housecallpro") and data.get("confidence", 0) >= 0.95:
                return "Housecall Pro"
            elif data.get("uses_jobber") and data.get("confidence", 0) >= 0.95:
                return "Jobber"

        return None

    except Exception as e:
        print(f"-- Error for {domain}: {e}", file=sys.stderr)
        return None


def calculate_score(lead, software):
    """Calculate new score with detected software."""
    score = 0

    # Software (+15)
    if software:
        score += 15

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

    # Assume domain exists (+2) for all leads in DB
    score += 2

    return score


def get_tier(score):
    """Get tier from score."""
    if score >= 20:
        return "A"
    elif score >= 10:
        return "B"
    else:
        return "C"


def main():
    print("-- Software Detection SQL Updates")
    print(f"-- Processing {len(LEADS)} leads")
    print()

    stats = {
        "processed": 0,
        "software_detected": 0,
        "servicetitan": 0,
        "jobber": 0,
        "housecall_pro": 0,
        "no_software": 0,
        "tier_changes": {"A": 0, "B": 0, "C": 0}
    }

    for i, lead in enumerate(LEADS, 1):
        domain = lead["domain"]
        old_tier = lead["tier"]
        old_score = lead["score"]

        print(f"-- [{i}/{len(LEADS)}] Processing: {domain}", file=sys.stderr)

        # Detect software
        software = detect_software(domain)

        if software:
            print(f"--   ✓ Detected: {software}", file=sys.stderr)
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

            # Output SQL UPDATE
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
                print(f"--   Tier: {old_tier} → {new_tier} (score: {old_score} → {new_score})", file=sys.stderr)
        else:
            print(f"--   ✗ No software detected", file=sys.stderr)
            stats["no_software"] += 1

        stats["processed"] += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)
        print(file=sys.stderr)

    # Summary
    print(file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Processed:         {stats['processed']}", file=sys.stderr)
    print(f"Software Detected: {stats['software_detected']}", file=sys.stderr)
    print(f"  - ServiceTitan:  {stats['servicetitan']}", file=sys.stderr)
    print(f"  - Jobber:        {stats['jobber']}", file=sys.stderr)
    print(f"  - Housecall Pro: {stats['housecall_pro']}", file=sys.stderr)
    print(f"No Software:       {stats['no_software']}", file=sys.stderr)
    print(f"Tier Changes:", file=sys.stderr)
    print(f"  - To A-Tier:     {stats['tier_changes']['A']}", file=sys.stderr)
    print(f"  - To B-Tier:     {stats['tier_changes']['B']}", file=sys.stderr)
    print(file=sys.stderr)


if __name__ == "__main__":
    main()
