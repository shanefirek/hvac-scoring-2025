#!/usr/bin/env python3
"""
Add leads from Supabase to correct tier campaigns if they're missing.

Recovers from failed move operation by adding leads that are in Supabase
but not in any Smartlead campaign.
"""

import os
import sys
import time
import requests
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

SMARTLEAD_API_KEY = os.getenv("SMARTLEAD_API_KEY")
SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    "A": 2677089,
    "B": 2677090,
    "C": 2677091
}

def get_supabase_leads():
    """Get all leads from Supabase"""
    print("Fetching Supabase data...")
    response = supabase.table("leads").select(
        "email, tier, score, company, first_name, last_name, reviews_count, service_software"
    ).execute()

    lookup = {}
    tier_counts = defaultdict(int)

    for lead in response.data:
        email = lead['email'].lower()
        lookup[email] = lead
        tier_counts[lead['tier']] += 1

    print(f"✓ Loaded {len(lookup)} leads from Supabase")
    print(f"  A-tier: {tier_counts['A']}, B-tier: {tier_counts['B']}, C-tier: {tier_counts['C']}\n")
    return lookup

def get_campaign_leads(campaign_id):
    """Get all leads from a Smartlead campaign"""
    all_leads = []
    offset = 0
    limit = 100

    while True:
        url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads"
        params = {"api_key": SMARTLEAD_API_KEY, "limit": limit, "offset": offset}

        response = requests.get(url, params=params)
        data = response.json()

        leads = data.get("data", [])
        all_leads.extend(leads)

        total = int(data.get("total_leads", 0))
        if offset + limit >= total:
            break

        offset += limit

    return all_leads

def add_leads_to_campaign(campaign_id, leads_batch):
    """Add a batch of leads to a campaign (max 100)"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads"
    params = {"api_key": SMARTLEAD_API_KEY}

    # Format leads for API
    lead_list = []
    for lead in leads_batch:
        lead_list.append({
            "first_name": lead.get("first_name") or "",
            "last_name": lead.get("last_name") or "",
            "email": lead["email"],
            "company_name": lead.get("company") or "",
            "custom_fields": {
                "tier": lead["tier"],
                "score": str(lead.get("score", 0)),
                "review_count": str(lead.get("reviews_count", 0)),
                "service_software": lead.get("service_software") or ""
            }
        })

    payload = {
        "lead_list": lead_list,
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_duplicate_leads_in_other_campaign": True
        }
    }

    try:
        response = requests.post(url, params=params, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            # API returns the count of successfully uploaded leads
            uploaded = result.get("upload_count", len(lead_list))
            return True, uploaded, result
        else:
            return False, 0, f"{response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, 0, str(e)

def find_missing_leads(tier, campaign_id, supabase_leads):
    """Find leads in Supabase but not in campaign"""
    print(f"\nAnalyzing {tier}-tier campaign...")
    smartlead_leads = get_campaign_leads(campaign_id)
    print(f"✓ Loaded {len(smartlead_leads)} leads from Smartlead")

    # Get emails in campaign
    smartlead_emails = set()
    for lead_data in smartlead_leads:
        lead = lead_data.get("lead", {})
        email = lead.get("email", "").lower()
        smartlead_emails.add(email)

    # Find missing
    missing = []
    for email, lead_data in supabase_leads.items():
        if lead_data["tier"] == tier and email not in smartlead_emails:
            missing.append(lead_data)

    print(f"  → Found {len(missing)} leads to add")
    return missing

def main():
    print("\n" + "=" * 70)
    print("ADD MISSING LEADS TO CAMPAIGNS")
    print("=" * 70)

    # Get Supabase data
    supabase_leads = get_supabase_leads()

    # Find and add missing leads for each tier
    total_added = 0
    total_failed = 0

    for tier in ["A", "B", "C"]:
        campaign_id = CAMPAIGNS[tier]
        missing_leads = find_missing_leads(tier, campaign_id, supabase_leads)

        if not missing_leads:
            print(f"  ✓ No missing leads for {tier}-tier")
            continue

        print(f"\nAdding {len(missing_leads)} leads to {tier}-tier campaign...")

        # Process in batches of 100 (API limit)
        for i in range(0, len(missing_leads), 100):
            batch = missing_leads[i:i+100]

            success, added_count, result = add_leads_to_campaign(campaign_id, batch)

            if success:
                total_added += added_count
                print(f"  ✓ Batch {i//100 + 1}: Added {added_count}/{len(batch)} leads")
                if isinstance(result, dict):
                    print(f"     Duplicates: {result.get('duplicate', 0)}, Invalid: {result.get('invalid_email_count', 0)}")
            else:
                total_failed += len(batch)
                print(f"  ✗ Failed to add batch: {result}")

            time.sleep(0.2)  # Rate limiting

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"\n✓ Successfully added: {total_added}")
    if total_failed > 0:
        print(f"✗ Failed: {total_failed}")
    print()

if __name__ == "__main__":
    main()
