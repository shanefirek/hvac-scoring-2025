#!/usr/bin/env python3
"""
Check individual lead activity (bypasses analytics cache)
"""

import requests
from datetime import datetime, timezone

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = [2677089, 2677090, 2677091]

def api_call(endpoint):
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params={"api_key": API_KEY})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

print("🔍 CHECKING LEAD-LEVEL ACTIVITY (Bypasses cache)\n")

total_leads = 0
sent_leads = 0
opened_leads = 0
clicked_leads = 0
replied_leads = 0

for campaign_id in CAMPAIGNS:
    print(f"Campaign {campaign_id}:")

    # Get all leads
    leads = api_call(f"/campaigns/{campaign_id}/leads?limit=200")

    if not leads or "data" not in leads:
        print("   ❌ Could not fetch leads\n")
        continue

    lead_list = leads["data"]
    total_leads += len(lead_list)

    # Count lead statuses
    campaign_sent = sum(1 for l in lead_list if l.get("status") in ["SENT", "OPENED", "CLICKED", "REPLIED"])
    campaign_opened = sum(1 for l in lead_list if l.get("opened", False))
    campaign_clicked = sum(1 for l in lead_list if l.get("clicked", False))
    campaign_replied = sum(1 for l in lead_list if l.get("replied", False))

    sent_leads += campaign_sent
    opened_leads += campaign_opened
    clicked_leads += campaign_clicked
    replied_leads += campaign_replied

    print(f"   Total leads: {len(lead_list)}")
    print(f"   Sent: {campaign_sent}")
    print(f"   Opened: {campaign_opened}")
    print(f"   Clicked: {campaign_clicked}")
    print(f"   Replied: {campaign_replied}")

    # Show clicked leads
    if campaign_clicked > 0:
        print(f"\n   🖱️  CLICKED LEADS:")
        for lead in lead_list:
            if lead.get("clicked", False):
                email = lead.get("email", "unknown")
                company = lead.get("company_name", "unknown")
                last_clicked = lead.get("last_clicked_at")

                if last_clicked:
                    try:
                        dt = datetime.fromtimestamp(last_clicked, tz=timezone.utc)
                        time_str = dt.strftime("%b %d %I:%M %p")
                    except:
                        time_str = "unknown"
                else:
                    time_str = "unknown"

                print(f"      • {email} ({company}) - {time_str}")

    print()

print("="*70)
print(f"TOTALS: {total_leads} leads total")
print(f"   Sent: {sent_leads}")
print(f"   Opened: {opened_leads}")
print(f"   Clicked: {clicked_leads}")
print(f"   Replied: {replied_leads}")
print("="*70 + "\n")

if sent_leads == 0:
    print("⚠️  NO SENDS DETECTED")
    print("   Campaigns are either:")
    print("   1. Still processing (check UI in 5-10 mins)")
    print("   2. Not actually sending (need to verify UI status)")
    print("   3. API data is severely delayed\n")
elif clicked_leads > 0:
    print(f"✅ {clicked_leads} CLICKS! People are interested.")
    print("   Check Patrick's Calendly for bookings\n")
