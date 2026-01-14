#!/usr/bin/env python3
"""
Backfill missing tier fields in Smartlead custom_fields.

Updates leads that are in the correct campaigns but have empty tier field.
"""

import os
import sys
import time
import requests
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

def get_supabase_lookup():
    """Build email -> tier lookup from Supabase"""
    print("Fetching Supabase data...")
    response = supabase.table("leads").select("email, tier").execute()

    lookup = {}
    for lead in response.data:
        lookup[lead['email'].lower()] = lead['tier']

    print(f"✓ Loaded {len(lookup)} leads from Supabase\n")
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

def update_lead_tier(campaign_id, lead_id, email, tier):
    """Update a lead's tier field in custom_fields"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads/{lead_id}"
    params = {"api_key": SMARTLEAD_API_KEY}
    data = {
        "email": email,
        "custom_fields": {
            "tier": tier
        }
    }

    try:
        response = requests.post(url, params=params, json=data, timeout=10)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"{response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def process_campaign(tier, campaign_id, supabase_lookup):
    """Process all leads in a campaign"""
    print(f"\n{'='*70}")
    print(f"{tier}-TIER CAMPAIGN (ID: {campaign_id})")
    print(f"{'='*70}")

    # Get all leads
    print(f"Fetching leads from Smartlead...")
    leads = get_campaign_leads(campaign_id)
    print(f"✓ Loaded {len(leads)} leads\n")

    # Analyze what needs updating
    to_update = []

    for lead_data in leads:
        lead = lead_data.get("lead", {})
        lead_id = lead.get("id")
        email = lead.get("email", "").lower()
        current_custom = lead.get("custom_fields", {})

        # Check if tier field is missing or empty
        current_tier = str(current_custom.get("tier", "")).strip()

        if not current_tier and email in supabase_lookup:
            to_update.append({
                'lead_id': lead_id,
                'email': email,
                'tier': supabase_lookup[email]
            })

    print(f"Leads needing tier field: {len(to_update)}/{len(leads)}")

    if len(to_update) == 0:
        print("✓ All leads already have tier field!")
        return 0, 0

    # Update leads
    print(f"\nStarting updates...")

    updated = 0
    failed = 0

    for i, lead_update in enumerate(to_update, 1):
        success, error = update_lead_tier(
            campaign_id,
            lead_update['lead_id'],
            lead_update['email'],
            lead_update['tier']
        )

        if success:
            updated += 1
            if updated % 25 == 0:
                print(f"  ✓ Updated {updated}/{len(to_update)} leads...")
        else:
            failed += 1
            print(f"  ✗ Failed {lead_update['email']}: {error}")

        # Rate limiting - 6-7 requests per second max
        time.sleep(0.15)

    print(f"\n✓ Completed: {updated} updated, {failed} failed")
    return updated, failed

def main():
    print("\n" + "="*70)
    print("BACKFILL MISSING TIER FIELDS")
    print("="*70)
    print("\nThis will update the tier field in custom_fields for leads")
    print("that are missing this data.\n")

    # Get Supabase data
    supabase_lookup = get_supabase_lookup()

    # Process each campaign
    total_updated = 0
    total_failed = 0

    for tier in ["A", "B", "C"]:
        campaign_id = CAMPAIGNS[tier]
        updated, failed = process_campaign(tier, campaign_id, supabase_lookup)
        total_updated += updated
        total_failed += failed

        # Brief pause between campaigns
        time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print(f"\n✓ Total updated: {total_updated}")
    if total_failed > 0:
        print(f"✗ Total failed: {total_failed}")
    print()

if __name__ == "__main__":
    main()
