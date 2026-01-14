#!/usr/bin/env python3
"""
Re-run software detection on Dec 7, 2025 leads that are missing service_software.

This script:
1. Queries Supabase for leads from Dec 7 where service_software IS NULL
2. Calls Railway software detection API for each domain
3. Updates Supabase with detected software
4. Recalculates scores and updates tiers

Usage:
    python scripts/enrichment/detect_software_dec7_leads.py
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional, Dict

# Load environment variables
load_dotenv()

# Configuration
RAILWAY_API_URL = "https://fastapi-production-85b6.up.railway.app/classify"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BATCH_SIZE = 10  # Process in batches to show progress
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def detect_software(domain: str) -> Optional[str]:
    """
    Call Railway API to detect software on a domain.

    Returns:
        - "ServiceTitan", "Jobber", or "Housecall Pro" if detected with high confidence
        - None if no software detected or API error
    """
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
        print(f"  ⚠️  Error detecting software for {domain}: {str(e)}")
        return None


def calculate_score(lead: Dict) -> int:
    """
    Calculate score based on lead signals.

    Scoring logic (max 30 points):
    - Service Software: +15
    - Franchise: +10
    - Reviews 500+: +10
    - Reviews 100-499: +7
    - Reviews 25-99: +4
    - Reviews 10-24: +2
    - LinkedIn: +3
    - Domain: +2
    """
    score = 0

    # Software detection (+15)
    if lead.get("service_software"):
        score += 15

    # Franchise (+10)
    if lead.get("is_franchise"):
        score += 10

    # Reviews
    reviews = lead.get("reviews_count", 0) or 0
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
    """Get tier based on score."""
    if score >= 20:
        return "A"
    elif score >= 10:
        return "B"
    else:
        return "C"


def update_lead_with_software(lead_id: str, software: str, new_score: int, new_tier: str):
    """Update lead with detected software, new score, and new tier."""
    try:
        supabase.table("leads").update({
            "service_software": software,
            "score": new_score,
            "tier": new_tier,
            "enriched_at": "now()"
        }).eq("id", lead_id).execute()
    except Exception as e:
        print(f"  ⚠️  Error updating lead {lead_id}: {str(e)}")


def main():
    print("=" * 80)
    print("SOFTWARE DETECTION - Dec 7, 2025 Leads")
    print("=" * 80)
    print()

    # Step 1: Fetch leads needing software detection
    print("📊 Fetching leads from Dec 7 that need software detection...")

    try:
        response = supabase.table("leads").select(
            "id, email, domain, company, service_software, score, tier, "
            "reviews_count, is_franchise, company_linkedin"
        ).gte(
            "created_at", "2025-12-07 00:00:00+00"
        ).lt(
            "created_at", "2025-12-08 00:00:00+00"
        ).is_(
            "service_software", "null"
        ).not_.is_(
            "domain", "null"
        ).execute()

        leads = response.data
        total_leads = len(leads)

        print(f"✅ Found {total_leads} leads needing software detection")
        print()

    except Exception as e:
        print(f"❌ Error fetching leads: {str(e)}")
        sys.exit(1)

    if total_leads == 0:
        print("✅ No leads need software detection!")
        return

    # Step 2: Process leads in batches
    print(f"🔍 Processing {total_leads} leads in batches of {BATCH_SIZE}...")
    print()

    stats = {
        "processed": 0,
        "software_detected": 0,
        "servicetitan": 0,
        "jobber": 0,
        "housecall_pro": 0,
        "no_software": 0,
        "tier_changes": {"A": 0, "B": 0, "C": 0},
        "errors": 0
    }

    for i, lead in enumerate(leads, 1):
        domain = lead["domain"]
        old_tier = lead["tier"]

        print(f"[{i}/{total_leads}] {lead['company'][:40]:40} | {domain[:35]:35}", end=" | ")

        # Detect software
        software = detect_software(domain)

        if software:
            print(f"✅ {software}")
            stats["software_detected"] += 1

            if software == "ServiceTitan":
                stats["servicetitan"] += 1
            elif software == "Jobber":
                stats["jobber"] += 1
            elif software == "Housecall Pro":
                stats["housecall_pro"] += 1

            # Update lead data for scoring
            lead["service_software"] = software

            # Recalculate score and tier
            new_score = calculate_score(lead)
            new_tier = get_tier(new_score)

            # Update Supabase
            update_lead_with_software(lead["id"], software, new_score, new_tier)

            # Track tier changes
            if new_tier != old_tier:
                stats["tier_changes"][new_tier] += 1
                print(f"      └─ Tier: {old_tier} → {new_tier} (score: {lead['score']} → {new_score})")

        else:
            print("❌ No software detected")
            stats["no_software"] += 1

        stats["processed"] += 1

        # Show progress summary every BATCH_SIZE leads
        if i % BATCH_SIZE == 0:
            print()
            print(f"  Progress: {i}/{total_leads} ({i*100//total_leads}%) | "
                  f"Detected: {stats['software_detected']} | "
                  f"None: {stats['no_software']}")
            print()

        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Final summary
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Processed:        {stats['processed']}")
    print(f"Software Detected:      {stats['software_detected']} ({stats['software_detected']*100//total_leads}%)")
    print()
    print("Software Breakdown:")
    print(f"  - ServiceTitan:       {stats['servicetitan']}")
    print(f"  - Jobber:             {stats['jobber']}")
    print(f"  - Housecall Pro:      {stats['housecall_pro']}")
    print()
    print(f"No Software:            {stats['no_software']} ({stats['no_software']*100//total_leads}%)")
    print()
    print("Tier Changes:")
    print(f"  - Moved to A-Tier:    {stats['tier_changes']['A']}")
    print(f"  - Moved to B-Tier:    {stats['tier_changes']['B']}")
    print(f"  - Stayed in C-Tier:   {stats['tier_changes']['C']}")
    print()

    if stats["errors"] > 0:
        print(f"⚠️  Errors: {stats['errors']}")

    print("✅ Software detection complete!")
    print()


if __name__ == "__main__":
    main()
