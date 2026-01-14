#!/usr/bin/env python3
"""
Run software detection on leads from CSV file.

Usage:
    python3 scripts/enrichment/run_software_detection.py /tmp/dec7_leads_simple.csv > updates.sql 2> progress.log
"""

import csv
import requests
import time
import sys

RAILWAY_API_URL = "https://fastapi-production-85b6.up.railway.app/classify"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds


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
        print(f"  ⚠️  Error for {domain}: {e}", file=sys.stderr)
        return None


def calculate_score(reviews_count, software):
    """Calculate new score with detected software."""
    score = 0

    # Software (+15)
    if software:
        score += 15

    # Reviews
    reviews = reviews_count or 0
    if reviews >= 500:
        score += 10
    elif reviews >= 100:
        score += 7
    elif reviews >= 25:
        score += 4
    elif reviews >= 10:
        score += 2

    # Domain (+2) - all leads in DB have domains
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
    if len(sys.argv) < 2:
        print("Usage: python3 run_software_detection.py <csv_file>", file=sys.stderr)
        sys.exit(1)

    csv_file = sys.argv[1]

    # Read leads from CSV
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    total = len(leads)
    print(f"Processing {total} leads...", file=sys.stderr)
    print(file=sys.stderr)

    # Statistics
    stats = {
        "processed": 0,
        "software_detected": 0,
        "servicetitan": 0,
        "jobber": 0,
        "housecall_pro": 0,
        "no_software": 0,
        "tier_changes": {"A": 0, "B": 0, "C": 0}
    }

    # Output SQL header
    print("-- Software Detection SQL Updates")
    print(f"-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Process each lead
    for i, lead in enumerate(leads, 1):
        lead_id = lead["id"]
        domain = lead["domain"]
        old_tier = lead["tier"]
        old_score = int(lead["score"])
        reviews = int(lead.get("reviews_count") or 0)

        print(f"[{i}/{total}] {domain[:40]:40}", end=" | ", file=sys.stderr)

        # Detect software
        software = detect_software(domain)

        if software:
            print(f"✅ {software}", file=sys.stderr)
            stats["software_detected"] += 1

            if software == "ServiceTitan":
                stats["servicetitan"] += 1
            elif software == "Jobber":
                stats["jobber"] += 1
            elif software == "Housecall Pro":
                stats["housecall_pro"] += 1

            # Calculate new score and tier
            new_score = calculate_score(reviews, software)
            new_tier = get_tier(new_score)

            # Output SQL UPDATE
            print(f"UPDATE leads SET")
            print(f"  service_software = '{software}',")
            print(f"  score = {new_score},")
            print(f"  tier = '{new_tier}',")
            print(f"  enriched_at = NOW()")
            print(f"WHERE id = '{lead_id}';")
            print()

            # Track tier changes
            if new_tier != old_tier:
                stats["tier_changes"][new_tier] += 1
                print(f"      └─ Tier: {old_tier} → {new_tier} (score: {old_score} → {new_score})", file=sys.stderr)
        else:
            print("❌ No software", file=sys.stderr)
            stats["no_software"] += 1

        stats["processed"] += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    print(file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Processed:         {stats['processed']}", file=sys.stderr)
    print(f"Software Detected: {stats['software_detected']} ({stats['software_detected']*100//total if total > 0 else 0}%)", file=sys.stderr)
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
