#!/usr/bin/env python3
"""Push leads from Supabase to Smartlead campaigns based on score."""

import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Campaign mapping by score
CAMPAIGNS = {
    "A": 2677089,  # Score 20-30
    "B": 2677090,  # Score 10-19
    "C": 2677091,  # Score 0-9
}

def get_unsent_leads():
    """Get all leads not yet in Smartlead."""
    result = supabase.table("leads").select("*").or_(
        "in_smartlead.eq.false,in_smartlead.is.null"
    ).or_(
        "suppressed.eq.false,suppressed.is.null"
    ).execute()
    return result.data

def get_tier_from_score(score):
    """Determine tier from score."""
    if score >= 20:
        return "A"
    elif score >= 10:
        return "B"
    return "C"

def add_lead_to_campaign(campaign_id, lead):
    """Add a single lead to a Smartlead campaign."""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={SMARTLEAD_API_KEY}"

    payload = {
        "lead_list": [{
            "email": lead["email"],
            "first_name": lead.get("first_name") or "there",
            "last_name": lead.get("last_name") or "",
            "company_name": lead.get("company") or "",
            "custom_fields": {
                "reviews_count": str(lead.get("reviews_count") or 0),
                "service_software": lead.get("service_software") or "",
                "website": lead.get("domain") or "",
                "phone": lead.get("phone_number") or "",
                "city": lead.get("city") or "",
                "state": lead.get("state") or "",
            }
        }],
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_duplicate_leads_in_other_campaign": False
        }
    }

    response = requests.post(url, json=payload)
    return response.status_code, response.text

def update_supabase_flag(email, campaign_id, smartlead_id=None):
    """Mark lead as synced in Supabase."""
    update_data = {
        "in_smartlead": True,
        "smartlead_campaign_ids": [campaign_id]
    }
    if smartlead_id:
        update_data["smartlead_lead_id"] = smartlead_id

    supabase.table("leads").update(update_data).eq("email", email).execute()

def main():
    leads = get_unsent_leads()
    print(f"Found {len(leads)} unsent leads")

    # Group by tier
    tiers = {"A": [], "B": [], "C": []}
    for lead in leads:
        tier = get_tier_from_score(lead.get("score") or 0)
        tiers[tier].append(lead)

    print(f"A-tier: {len(tiers['A'])}, B-tier: {len(tiers['B'])}, C-tier: {len(tiers['C'])}")

    # Push to campaigns
    for tier, tier_leads in tiers.items():
        campaign_id = CAMPAIGNS[tier]
        print(f"\nPushing {len(tier_leads)} leads to {tier}-tier campaign {campaign_id}...")

        success = 0
        failed = 0
        for i, lead in enumerate(tier_leads):
            status, response = add_lead_to_campaign(campaign_id, lead)
            if status == 200:
                success += 1
                update_supabase_flag(lead["email"], campaign_id)
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{len(tier_leads)}")
            else:
                failed += 1
                if failed <= 3:
                    print(f"  Failed: {lead['email']} - {status}: {response[:100]}")

        print(f"  Done: {success} success, {failed} failed")

if __name__ == "__main__":
    main()
