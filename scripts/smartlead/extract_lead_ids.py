#!/usr/bin/env python3
"""
Extract smartlead_lead_id and email from all campaigns using Smartlead API.
"""

import requests
import csv
import sys
from pathlib import Path

# API Configuration
API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Campaign IDs
CAMPAIGNS = {
    2677089: "A-Tier",
    2677090: "B-Tier",
    2677091: "C-Tier"
}

OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "smartlead_lead_ids.csv"

def get_campaign_leads(campaign_id, limit=20, offset=0):
    """Fetch leads from a campaign"""
    url = f"{BASE_URL}/campaigns/{campaign_id}/lead-stats"
    params = {
        "api_key": API_KEY,
        "limit": limit,
        "offset": offset
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching leads: {e}", file=sys.stderr)
        return None

def extract_leads_from_campaign(campaign_id, campaign_name):
    """Extract all leads from a campaign with pagination"""
    all_leads = []
    offset = 0
    limit = 50  # Batch size

    print(f"Extracting leads from {campaign_name} (ID: {campaign_id})...")

    while True:
        print(f"  Fetching offset {offset}...", end=" ")

        response = get_campaign_leads(campaign_id, limit=limit, offset=offset)

        if not response or "data" not in response:
            print("No data returned")
            break

        batch = response["data"]
        if not batch:
            print("No more leads")
            break

        # Extract email and lead_id from each lead
        for lead in batch:
            all_leads.append({
                "email": lead.get("to", ""),
                "smartlead_lead_id": lead.get("lead_id", ""),
                "campaign_id": campaign_id
            })

        print(f"Got {len(batch)} leads (total: {len(all_leads)})")

        # Check if there are more leads
        has_more = response.get("hasMore", False)
        if not has_more:
            print(f"  ✓ Complete")
            break

        offset += limit

    return all_leads

def main():
    """Main execution"""
    print("=" * 60)
    print("Smartlead Lead ID Extraction")
    print("=" * 60)
    print()

    all_leads = []

    # Extract from each campaign
    for campaign_id, campaign_name in CAMPAIGNS.items():
        leads = extract_leads_from_campaign(campaign_id, campaign_name)
        all_leads.extend(leads)
        print(f"✓ {campaign_name}: {len(leads)} leads extracted\n")

    # Save to CSV
    print(f"Saving {len(all_leads)} leads to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["email", "smartlead_lead_id", "campaign_id"])
        writer.writeheader()

        for lead in all_leads:
            writer.writerow(lead)

    print(f"✓ Saved to {OUTPUT_FILE}")
    print()
    print("Summary:")
    print(f"  Total leads extracted: {len(all_leads)}")
    for campaign_id, campaign_name in CAMPAIGNS.items():
        count = sum(1 for l in all_leads if l["campaign_id"] == campaign_id)
        print(f"  {campaign_name}: {count}")

if __name__ == "__main__":
    main()
