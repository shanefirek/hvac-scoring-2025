#!/usr/bin/env python3
"""
Sync first_name from Supabase to Smartlead for all leads.
Fixes the "there" issue by setting first_name to empty string in Smartlead.
"""

import os
import requests
import time
from supabase import create_client

# Config
SUPABASE_URL = "https://rlmuovkdvbxzyylbiunj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsbXVvdmtkdmJ4enl5bGJpdW5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDEyODQ2MywiZXhwIjoyMDc1NzA0NDYzfQ.9r1jmAlIvL_YMmcbOT8xAS_hIknNthfuAL-5BHIr53o"
SMARTLEAD_API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"

def get_leads_to_sync(supabase):
    """Get all leads that need first_name synced to Smartlead"""
    result = supabase.table('leads').select(
        'id, smartlead_lead_id, smartlead_campaign_ids, email, first_name, last_name'
    ).not_.is_('smartlead_lead_id', 'null').execute()

    return result.data

def update_smartlead_lead(campaign_id, lead_id, email, first_name):
    """Update a lead's first_name in Smartlead"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads/{lead_id}?api_key={SMARTLEAD_API_KEY}"

    payload = {
        "email": email,
        "first_name": first_name if first_name else ""  # Empty string if null
    }

    response = requests.post(url, json=payload)
    return response.status_code == 200, response.text

def main():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Fetching leads from Supabase...")
    leads = get_leads_to_sync(supabase)
    print(f"Found {len(leads)} leads to sync")

    success_count = 0
    error_count = 0

    for i, lead in enumerate(leads):
        smartlead_id = lead['smartlead_lead_id']
        campaign_ids = lead['smartlead_campaign_ids'] or []
        email = lead['email']
        first_name = lead['first_name']

        # Update in each campaign the lead is part of
        for campaign_id in campaign_ids:
            success, response = update_smartlead_lead(campaign_id, smartlead_id, email, first_name)

            if success:
                success_count += 1
            else:
                error_count += 1
                if error_count <= 5:  # Only print first 5 errors
                    print(f"Error updating {email} in campaign {campaign_id}: {response}")

        # Progress update every 100 leads
        if (i + 1) % 100 == 0:
            print(f"Progress: {i + 1}/{len(leads)} leads processed ({success_count} success, {error_count} errors)")

        # Rate limiting - small delay between requests
        time.sleep(0.1)

    print(f"\nDone! {success_count} successful updates, {error_count} errors")

if __name__ == "__main__":
    main()
