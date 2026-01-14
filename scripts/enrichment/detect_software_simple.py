#!/usr/bin/env python3
"""
Detect software for leads and output SQL update statements.

This script:
1. Reads leads from a file (exported from Supabase)
2. Calls Railway API for each domain
3. Outputs SQL UPDATE statements that can be executed via MCP

Usage:
    python scripts/enrichment/detect_software_simple.py > updates.sql
"""

import requests
import json
import sys
import time

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
            software = data.get("software")
            confidence = data.get("confidence", 0)

            # Only accept high-confidence detections (95%+)
            if software and confidence >= 0.95:
                return software

        return None

    except Exception as e:
        print(f"-- Error: {domain}: {str(e)}", file=sys.stderr)
        return None


def calculate_score(service_software, reviews_count, is_franchise, company_linkedin, domain):
    """Calculate score based on signals."""
    score = 0

    if service_software:
        score += 15
    if is_franchise:
        score += 10

    reviews = reviews_count or 0
    if reviews >= 500:
        score += 10
    elif reviews >= 100:
        score += 7
    elif reviews >= 25:
        score += 4
    elif reviews >= 10:
        score += 2

    if company_linkedin:
        score += 3
    if domain:
        score += 2

    return score


def get_tier(score):
    """Get tier based on score."""
    if score >= 20:
        return "A"
    elif score >= 10:
        return "B"
    else:
        return "C"


# Sample of leads to process (first 10 for testing)
# Format: (id, domain, reviews_count, is_franchise, company_linkedin, current_score, current_tier)
leads_sample = [
    ("cb92a053-6a8e-4569-9f20-dceb5ba05b4c", "searshomeservices.com", None, False, None, 15, "B"),
    ("19c5d624-fd6d-441a-963d-f38f4e2f3a90", "searshomeservices.com", None, False, None, 15, "B"),
    ("16d4449f-c583-47be-93e4-80905afa4ed9", "kclarson.com", None, False, None, 15, "B"),
]

print("-- Software Detection SQL Updates")
print("-- Generated:", time.strftime("%Y-%m-%d %H:%M:%S"))
print()

stats = {
    "processed": 0,
    "software_detected": 0,
    "servicetitan": 0,
    "jobber": 0,
    "housecall_pro": 0,
    "no_software": 0,
}

for lead_id, domain, reviews, is_franchise, linkedin, old_score, old_tier in leads_sample:
    print(f"-- Processing: {domain}", file=sys.stderr)

    software = detect_software(domain)

    if software:
        print(f"-- Detected: {software}", file=sys.stderr)
        stats["software_detected"] += 1

        if software == "ServiceTitan":
            stats["servicetitan"] += 1
        elif software == "Jobber":
            stats["jobber"] += 1
        elif software == "Housecall Pro":
            stats["housecall_pro"] += 1

        # Calculate new score and tier
        new_score = calculate_score(software, reviews, is_franchise, linkedin, domain)
        new_tier = get_tier(new_score)

        # Output SQL UPDATE
        print(f"UPDATE leads SET")
        print(f"  service_software = '{software}',")
        print(f"  score = {new_score},")
        print(f"  tier = '{new_tier}',")
        print(f"  enriched_at = NOW()")
        print(f"WHERE id = '{lead_id}';")
        print()

        if new_tier != old_tier:
            print(f"-- Tier changed: {old_tier} → {new_tier} (score: {old_score} → {new_score})", file=sys.stderr)

    else:
        print(f"-- No software detected", file=sys.stderr)
        stats["no_software"] += 1

    stats["processed"] += 1
    time.sleep(DELAY_BETWEEN_REQUESTS)
    print(file=sys.stderr)

print(f"-- Summary:", file=sys.stderr)
print(f"-- Processed: {stats['processed']}", file=sys.stderr)
print(f"-- Software Detected: {stats['software_detected']}", file=sys.stderr)
print(f"--   ServiceTitan: {stats['servicetitan']}", file=sys.stderr)
print(f"--   Jobber: {stats['jobber']}", file=sys.stderr)
print(f"--   Housecall Pro: {stats['housecall_pro']}", file=sys.stderr)
print(f"-- No Software: {stats['no_software']}", file=sys.stderr)
