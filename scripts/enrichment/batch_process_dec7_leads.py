#!/usr/bin/env python3
"""
Process Dec 7 leads in batches - query from Supabase, detect software, generate SQL.

This script outputs SQL statements that can be executed via MCP tools.

Usage:
    python3 scripts/enrichment/batch_process_dec7_leads.py > /tmp/dec7_updates.sql 2> /tmp/dec7_progress.log
"""

import requests
import time
import sys

RAILWAY_API_URL = "https://fastapi-production-85b6.up.railway.app/classify"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# All 493 leads from Dec 7 - truncated list for demonstration
# In production, this would be loaded from a file or database query
LEADS = [
    {"id": "ea1512d8-8fac-4233-b6d2-ad94f667a444", "domain": "sullivanservice.com", "tier": "B", "score": 12, "reviews_count": 3720},
    {"id": "447ac6b2-f993-448d-9e0c-4a6832551946", "domain": "charlesheatingandair.com", "tier": "B", "score": 12, "reviews_count": 2561},
    # ... (would include all 493 leads)
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
    """Calculate new score."""
    score = 0
    if software:
        score += 15

    reviews = reviews_count or 0
    if reviews >= 500:
        score += 10
    elif reviews >= 100:
        score += 7
    elif reviews >= 25:
        score += 4
    elif reviews >= 10:
        score += 2

    score += 2  # domain
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
    total = len(LEADS)
    print(f"Processing {total} leads...", file=sys.stderr)
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

    print("-- Software Detection SQL Updates for Dec 7 Leads")
    print(f"-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    for i, lead in enumerate(LEADS, 1):
        domain = lead["domain"]
        old_tier = lead["tier"]
        old_score = lead["score"]
        reviews = lead.get("reviews_count", 0)

        print(f"[{i}/{total}] {domain[:50]:50}", end=" | ", file=sys.stderr)

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

            new_score = calculate_score(reviews, software)
            new_tier = get_tier(new_score)

            print(f"UPDATE leads SET")
            print(f"  service_software = '{software}',")
            print(f"  score = {new_score},")
            print(f"  tier = '{new_tier}',")
            print(f"  enriched_at = NOW()")
            print(f"WHERE id = '{lead['id']}';")
            print()

            if new_tier != old_tier:
                stats["tier_changes"][new_tier] += 1
                print(f"      └─ Tier: {old_tier} → {new_tier} (score: {old_score} → {new_score})", file=sys.stderr)
        else:
            print("❌ No software", file=sys.stderr)
            stats["no_software"] += 1

        stats["processed"] += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
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
