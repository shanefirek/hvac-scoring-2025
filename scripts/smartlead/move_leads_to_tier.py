#!/usr/bin/env python3
"""
Move leads to correct tier campaigns based on Supabase scoring.

Identifies leads in wrong campaigns and moves them to correct tier:
- Deletes from current campaign
- Adds to correct campaign
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

def get_supabase_leads():
    """Get all leads from Supabase with tier info"""
    print("Fetching Supabase data...")
    response = supabase.table("leads").select(
        "email, tier, score, company, first_name, last_name, reviews_count, service_software"
    ).execute()

    lookup = {}
    for lead in response.data:
        lookup[lead['email'].lower()] = lead

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

def delete_lead_from_campaign(campaign_id, lead_id):
    """Delete a lead from a campaign"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads/{lead_id}"
    params = {"api_key": SMARTLEAD_API_KEY}

    try:
        response = requests.delete(url, params=params, timeout=10)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"{response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def add_lead_to_campaign(campaign_id, lead_data):
    """Add a lead to a campaign"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads"
    params = {"api_key": SMARTLEAD_API_KEY}

    # Prepare lead data with correct API format (rebuild custom_fields from Supabase data)
    payload = {
        "lead_list": [{
            "first_name": lead_data.get("first_name") or "",
            "last_name": lead_data.get("last_name") or "",
            "email": lead_data["email"],
            "company_name": lead_data.get("company") or "",
            "custom_fields": {
                "tier": lead_data.get("tier", ""),
                "score": str(lead_data.get("score", 0)),
                "review_count": str(lead_data.get("reviews_count", 0)),
                "service_software": lead_data.get("service_software") or ""
            }
        }],
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_duplicate_leads_in_other_campaign": True  # Allow moving between campaigns
        }
    }

    try:
        response = requests.post(url, params=params, json=payload, timeout=10)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"{response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def identify_mismatches(campaign_tier, campaign_id, supabase_leads):
    """Identify leads that need to be moved"""
    print(f"\nAnalyzing {campaign_tier}-tier campaign...")
    leads = get_campaign_leads(campaign_id)
    print(f"✓ Loaded {len(leads)} leads")

    to_move = []

    for lead_data in leads:
        lead = lead_data.get("lead", {})
        lead_id = lead.get("id")
        email = lead.get("email", "").lower()

        # Skip if not in Supabase
        if email not in supabase_leads:
            continue

        supabase_tier = supabase_leads[email]["tier"]

        # Check if in wrong campaign
        if supabase_tier != campaign_tier:
            supabase_data = supabase_leads[email]
            to_move.append({
                "lead_id": lead_id,
                "email": email,
                "current_tier": campaign_tier,
                "tier": supabase_tier,  # renamed for clarity
                "first_name": supabase_data.get("first_name") or lead.get("first_name"),
                "last_name": supabase_data.get("last_name") or lead.get("last_name"),
                "company": supabase_data.get("company") or lead.get("company_name"),
                "score": supabase_data["score"],
                "reviews_count": supabase_data.get("reviews_count", 0),
                "service_software": supabase_data.get("service_software", "")
            })

    print(f"  → Found {len(to_move)} leads to move")
    return to_move

def move_leads(leads_to_move):
    """Move leads to correct campaigns"""
    if not leads_to_move:
        print("\n✓ No leads to move!")
        return 0, 0

    print(f"\nMoving {len(leads_to_move)} leads...")
    print("=" * 70)

    moved = 0
    failed = 0

    for i, lead_info in enumerate(leads_to_move, 1):
        current_campaign = CAMPAIGNS[lead_info["current_tier"]]
        target_campaign = CAMPAIGNS[lead_info["tier"]]

        print(f"\n[{i}/{len(leads_to_move)}] {lead_info['email']}")
        print(f"  {lead_info['current_tier']} → {lead_info['tier']} (score: {lead_info['score']})")

        # Step 1: Delete from current campaign
        success, error = delete_lead_from_campaign(current_campaign, lead_info["lead_id"])
        if not success:
            print(f"  ✗ Failed to delete: {error}")
            failed += 1
            continue

        time.sleep(0.15)  # Rate limiting

        # Step 2: Add to target campaign
        success, error = add_lead_to_campaign(target_campaign, lead_info)
        if not success:
            print(f"  ✗ Failed to add: {error}")
            failed += 1
            continue

        moved += 1
        if moved % 10 == 0:
            print(f"\n  ✓ Progress: {moved} moved, {failed} failed")

        time.sleep(0.15)  # Rate limiting

    return moved, failed

def main():
    print("\n" + "=" * 70)
    print("MOVE LEADS TO CORRECT TIER CAMPAIGNS")
    print("=" * 70)

    # Get Supabase data
    supabase_leads = get_supabase_leads()

    # Identify mismatches in each campaign
    all_moves = []

    for tier in ["A", "B", "C"]:
        mismatches = identify_mismatches(tier, CAMPAIGNS[tier], supabase_leads)
        all_moves.extend(mismatches)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY OF MOVES")
    print("=" * 70)

    move_summary = {}
    for lead in all_moves:
        key = f"{lead['current_tier']} → {lead['tier']}"
        move_summary[key] = move_summary.get(key, 0) + 1

    for move_type, count in sorted(move_summary.items()):
        print(f"  {move_type}: {count} leads")

    print(f"\n  TOTAL: {len(all_moves)} leads to move")

    # Execute moves
    moved, failed = move_leads(all_moves)

    # Final summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"\n✓ Successfully moved: {moved}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print()

if __name__ == "__main__":
    main()
