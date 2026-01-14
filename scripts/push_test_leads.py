#!/usr/bin/env python3
"""
Push valid leads to 4 Smartlead test campaigns for A/B/C/D message variant testing.
Splits 498 leads evenly across campaigns (~125 each).
"""

import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Config
SMARTLEAD_API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Test campaigns
CAMPAIGNS = [
    {"id": 2757801, "name": "M&A Variant"},
    {"id": 2757802, "name": "35/100 Variant"},
    {"id": 2757804, "name": "Social Proof Variant"},
    {"id": 2757805, "name": "Direct Variant"},
]

def get_valid_leads():
    """Fetch all leads with email_status = 'valid' from Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table("leads").select(
        "email, first_name, last_name, company, domain, reviews_count"
    ).eq("email_status", "valid").order("id").execute()
    return result.data

def format_lead_for_smartlead(lead):
    """Format a lead for Smartlead API"""
    return {
        "email": lead["email"],
        "first_name": lead.get("first_name") or "",
        "last_name": lead.get("last_name") or "",
        "company_name": lead.get("company") or "",
        "custom_fields": {
            "domain": lead.get("domain") or "",
            "reviews_count": str(lead.get("reviews_count") or 0)
        }
    }

def push_leads_to_campaign(campaign_id, leads, batch_size=50):
    """Push leads to a Smartlead campaign in batches"""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads"
    params = {"api_key": SMARTLEAD_API_KEY}

    total_uploaded = 0
    total_duplicates = 0

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        formatted = [format_lead_for_smartlead(l) for l in batch]

        response = requests.post(url, params=params, json={"lead_list": formatted})

        if response.status_code == 200:
            data = response.json()
            total_uploaded += data.get("upload_count", 0)
            total_duplicates += data.get("duplicate_count", 0)
            print(f"  Batch {i//batch_size + 1}: +{data.get('upload_count', 0)} leads")
        else:
            print(f"  Batch {i//batch_size + 1}: ERROR - {response.text}")

    return total_uploaded, total_duplicates

def main():
    print("=" * 60)
    print("Push Valid Leads to Test Campaigns")
    print("=" * 60)

    # Get all valid leads
    print("\n1. Fetching valid leads from Supabase...")
    leads = get_valid_leads()
    print(f"   Found {len(leads)} valid leads")

    # Split leads across 4 campaigns
    leads_per_campaign = len(leads) // 4
    remainder = len(leads) % 4

    print(f"\n2. Splitting leads: {leads_per_campaign} per campaign (+{remainder} extra)")

    # Distribute leads
    start = 0
    for i, campaign in enumerate(CAMPAIGNS):
        # Give extra leads to first campaigns if there's a remainder
        count = leads_per_campaign + (1 if i < remainder else 0)
        campaign_leads = leads[start:start + count]
        start += count

        print(f"\n3.{i+1}. Pushing {len(campaign_leads)} leads to {campaign['name']} (ID: {campaign['id']})...")
        uploaded, dupes = push_leads_to_campaign(campaign["id"], campaign_leads)
        print(f"   Result: {uploaded} uploaded, {dupes} duplicates")

    print("\n" + "=" * 60)
    print("Done! All leads pushed to test campaigns.")
    print("=" * 60)

if __name__ == "__main__":
    main()
