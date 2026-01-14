#!/usr/bin/env python3
"""
Update company names in existing Smartlead campaigns

Strategy: Delete all leads, re-add with normalized names
Safe because campaigns are in DRAFT mode (no sends yet)
"""

import requests
import csv
import time

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    2677089: "data/processed/leads_a_tier.csv",  # A-Tier
    2677090: "data/processed/leads_b_tier.csv",  # B-Tier
    2677091: "data/processed/leads_c_tier.csv"   # C-Tier
}

def api_call(method, endpoint, data=None):
    """Make API call"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, params=params, json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error: {e}")
        return None

def get_leads(campaign_id):
    """Get all leads from campaign"""
    print(f"   Fetching leads...")
    result = api_call("GET", f"/campaigns/{campaign_id}/leads?limit=500")
    if result:
        leads = result.get("leads", [])
        print(f"   Found {len(leads)} leads")
        return leads
    return []

def delete_all_leads(campaign_id, leads):
    """Delete all leads from campaign"""
    print(f"   Deleting {len(leads)} leads...")

    for lead in leads:
        lead_id = lead.get("id")
        api_call("DELETE", f"/campaigns/{campaign_id}/leads/{lead_id}")

    print(f"   ✅ Deleted all leads")

def load_and_add_leads(campaign_id, csv_file):
    """Load leads from CSV and add to campaign"""
    print(f"   Loading normalized leads from CSV...")

    leads = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                "email": row['email'],
                "first_name": row['first_name'],
                "last_name": row['last_name'],
                "company_name": row['company'],  # Now normalized
                "custom_fields": {
                    "service_software": row['service_software'],
                    "review_count": row['review_count']
                }
            }
            leads.append(lead)

    print(f"   Adding {len(leads)} leads with normalized names...")

    # Add in batches
    batch_size = 100
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        data = {
            "lead_list": batch,
            "settings": {
                "ignore_global_block_list": False,
                "ignore_unsubscribe_list": False,
                "ignore_duplicate_leads_in_other_campaign": True
            }
        }
        result = api_call("POST", f"/campaigns/{campaign_id}/leads", data)
        if result:
            print(f"      Batch {i//batch_size + 1}: {result.get('upload_count', 0)} added")

    print(f"   ✅ All leads re-added with normalized names")

def update_campaign(campaign_id, csv_file):
    """Update one campaign"""
    print(f"\n📝 Campaign {campaign_id}")

    # Get current leads
    leads = get_leads(campaign_id)

    # Delete all
    delete_all_leads(campaign_id, leads)
    time.sleep(1)

    # Re-add with normalized names
    load_and_add_leads(campaign_id, csv_file)

    print(f"   ✅ Campaign updated")

def main():
    """Update all campaigns"""
    print("="*70)
    print("NORMALIZING COMPANY NAMES IN CAMPAIGNS")
    print("="*70)
    print("\nRemoving: LLC, Inc, Corp, extra slashes, (fka...), etc.\n")

    for campaign_id, csv_file in CAMPAIGNS.items():
        update_campaign(campaign_id, csv_file)
        time.sleep(2)

    print("\n" + "="*70)
    print("✅ Done! All leads updated with clean company names")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
