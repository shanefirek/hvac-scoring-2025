#!/usr/bin/env python3
"""Export all Smartlead campaign leads with engagement metrics."""

import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SMARTLEAD_API_KEY")
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = [
    {"id": 2677089, "name": "HVAC A-Tier - Software & Scale", "tier": "A"},
    {"id": 2677090, "name": "HVAC B-Tier - Growth Signal", "tier": "B"},
    {"id": 2677091, "name": "HVAC C-Tier - Pain Focus", "tier": "C"},
    {"id": 2757801, "name": "HVAC Test - M&A Variant", "tier": "Test"},
    {"id": 2757802, "name": "HVAC Test - 35/100 Variant", "tier": "Test"},
    {"id": 2757804, "name": "HVAC Test - Social Proof", "tier": "Test"},
    {"id": 2757805, "name": "HVAC Test - Direct Variant", "tier": "Test"},
]


def get_campaign_leads(campaign_id, limit=100, offset=0):
    """Fetch leads from a campaign."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/leads"
    params = {"api_key": API_KEY, "limit": limit, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()


def get_campaign_stats(campaign_id):
    """Fetch campaign statistics."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/statistics"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    return response.json()


def export_all():
    print("Exporting all Smartlead campaign leads...")

    all_leads = []
    campaign_stats = {}

    for campaign in CAMPAIGNS:
        cid = campaign["id"]
        tier = campaign["tier"]
        name = campaign["name"]

        print(f"\nProcessing {name} (ID: {cid})...")

        # Get campaign stats
        try:
            stats = get_campaign_stats(cid)
            campaign_stats[cid] = stats
            print(f"  Stats: {stats.get('sent_count', 0)} sent, {stats.get('open_count', 0)} opens")
        except Exception as e:
            print(f"  Warning: Could not get stats - {e}")
            campaign_stats[cid] = {}

        # Get all leads with pagination
        offset = 0
        campaign_leads = []
        while True:
            try:
                result = get_campaign_leads(cid, limit=100, offset=offset)
                data = result.get("data", [])
                if not data:
                    break
                campaign_leads.extend(data)
                offset += 100
                print(f"  Fetched {len(campaign_leads)} leads...")
            except Exception as e:
                print(f"  Error fetching leads: {e}")
                break

        # Process leads
        for lead_data in campaign_leads:
            lead = lead_data.get("lead", {})
            custom = lead.get("custom_fields", {})

            all_leads.append({
                "campaign_id": cid,
                "campaign_name": name,
                "campaign_tier": tier,
                "smartlead_lead_id": lead.get("id"),
                "email": lead.get("email", "").lower(),
                "first_name": lead.get("first_name", ""),
                "last_name": lead.get("last_name", ""),
                "company": lead.get("company_name", ""),
                "phone_number": lead.get("phone_number") or custom.get("phone_number", ""),
                "city": custom.get("city", ""),
                "state": custom.get("state", ""),
                "domain": custom.get("domain", ""),
                "service_software": custom.get("service_software", ""),
                "reviews_count": custom.get("reviews_count") or custom.get("review_count", ""),
                "status": lead_data.get("status", ""),
                "lead_category_id": lead_data.get("lead_category_id"),
                "is_unsubscribed": lead.get("is_unsubscribed", False),
                "created_at": lead_data.get("created_at", ""),
            })

        print(f"  Total: {len(campaign_leads)} leads")

    # Export to CSV
    output_path = "data/audit/smartlead_full_export.csv"
    with open(output_path, "w", newline="") as f:
        if all_leads:
            writer = csv.DictWriter(f, fieldnames=all_leads[0].keys())
            writer.writeheader()
            writer.writerows(all_leads)

    print(f"\n{'='*50}")
    print(f"Exported {len(all_leads)} total leads to {output_path}")

    # Summary by campaign
    print("\nSummary by campaign:")
    for campaign in CAMPAIGNS:
        count = sum(1 for l in all_leads if l["campaign_id"] == campaign["id"])
        print(f"  {campaign['name']}: {count}")

    return all_leads


if __name__ == "__main__":
    export_all()
