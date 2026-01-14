#!/usr/bin/env python3
"""
Fix missing attribution data in Smartlead campaigns.

Updates review_count and service_software custom fields for all leads
that are missing this data by pulling from Supabase.
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
    """Build email -> data lookup from Supabase"""
    print("Fetching Supabase data...")
    response = supabase.table("leads").select(
        "email, reviews_count, service_software, company, first_name"
    ).execute()

    lookup = {}
    for lead in response.data:
        lookup[lead['email'].lower()] = {
            'reviews_count': lead.get('reviews_count') or 0,
            'service_software': lead.get('service_software') or ''
        }

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

def update_lead(campaign_id, lead_id, email, custom_fields):
    """Update a lead's custom fields in Smartlead"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads/{lead_id}"
    params = {"api_key": SMARTLEAD_API_KEY}
    data = {
        "email": email,
        "custom_fields": custom_fields
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

        # Check if needs update
        current_review = str(current_custom.get("review_count", "")).strip()
        current_software = str(current_custom.get("service_software", "")).strip()

        # Get Supabase data
        supabase_data = supabase_lookup.get(email)
        if not supabase_data:
            continue

        needs_update = False

        # Check if we need to update
        if not current_review or not current_software:
            needs_update = True

        if needs_update:
            to_update.append({
                'lead_id': lead_id,
                'email': email,
                'current_review': current_review,
                'current_software': current_software,
                'new_review': str(supabase_data['reviews_count']),
                'new_software': supabase_data['service_software']
            })

    print(f"Leads needing updates: {len(to_update)}/{len(leads)}")

    if len(to_update) == 0:
        print("✓ All leads already have attribution data!")
        return 0, 0

    # Confirm before proceeding
    print(f"\nStarting updates...")

    # Update leads
    updated = 0
    failed = 0

    for i, lead_update in enumerate(to_update, 1):
        # Merge with existing custom fields
        new_custom_fields = {
            'review_count': lead_update['new_review'],
            'service_software': lead_update['new_software']
        }

        success, error = update_lead(
            campaign_id,
            lead_update['lead_id'],
            lead_update['email'],
            new_custom_fields
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
    print("SMARTLEAD ATTRIBUTION FIX")
    print("="*70)
    print("\nThis will update review_count and service_software for all leads")
    print("that are missing this data by syncing from Supabase.\n")

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
