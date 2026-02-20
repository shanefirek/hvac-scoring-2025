#!/usr/bin/env python3
"""Push marketing agency leads from Supabase to Smartlead."""

import os
import sys
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CAMPAIGN_ID = 2885428  # Marketing Agencies v2 - Tax Season 2026
BATCH_SIZE = 100

def get_unsent_leads():
    """Get marketing agency leads not yet in Smartlead."""
    all_leads = []
    offset = 0
    page_size = 1000

    while True:
        result = supabase.table("leads").select(
            "email,first_name,last_name,company,domain,phone_number,city,state"
        ).eq("business_type", "marketing_agency").is_("smartlead_lead_id", "null").range(offset, offset + page_size - 1).execute()

        if not result.data:
            break

        all_leads.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size

    return all_leads

def format_lead(lead):
    """Format lead for Smartlead API."""
    return {
        "email": lead["email"],
        "first_name": lead.get("first_name") or "there",
        "last_name": lead.get("last_name") or "",
        "company_name": lead.get("company") or "",
        "custom_fields": {
            "website": lead.get("domain") or "",
            "phone": lead.get("phone_number") or "",
            "city": lead.get("city") or "",
            "state": lead.get("state") or "",
        }
    }

def add_leads_batch(leads):
    """Add a batch of leads to Smartlead."""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{CAMPAIGN_ID}/leads?api_key={SMARTLEAD_API_KEY}"

    payload = {
        "lead_list": [format_lead(l) for l in leads],
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_duplicate_leads_in_other_campaign": False
        }
    }

    response = requests.post(url, json=payload)
    return response.status_code, response.json() if response.status_code == 200 else response.text

def main():
    leads = get_unsent_leads()
    print(f"Found {len(leads)} marketing agency leads to push")

    if not leads:
        return

    total_added = 0
    for i in range(0, len(leads), BATCH_SIZE):
        batch = leads[i:i + BATCH_SIZE]
        status, result = add_leads_batch(batch)

        if status == 200:
            added = result.get("upload_count", len(batch))
            total_added += added
            print(f"Batch {i//BATCH_SIZE + 1}: {added} added")
        else:
            print(f"Batch {i//BATCH_SIZE + 1} FAILED: {str(result)[:200]}")

    print(f"\nTotal: {total_added} leads added to campaign {CAMPAIGN_ID}")

if __name__ == "__main__":
    main()
