#!/usr/bin/env python3
"""
Enable Click Tracking on Active Campaigns

Re-enables click tracking via API (UI doesn't work for active campaigns).

Usage:
    python enable_click_tracking.py
"""

import requests
import json

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    "A-Tier": 2677089,
    "B-Tier": 2677090,
    "C-Tier": 2677091
}

def api_call(method, endpoint, data=None):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)
        else:
            response = requests.get(url, params=params, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   {e.response.text[:200]}")
        return None

def enable_tracking(tier, campaign_id):
    """Enable click tracking for a campaign"""
    print(f"\n📊 {tier} (ID: {campaign_id})")

    # Empty array = enable all tracking (opens + clicks)
    # track_settings uses NEGATIVE values (DONT_TRACK_*), so empty = track everything
    data = {
        "track_settings": [],  # Enable both opens and clicks
        "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "follow_up_percentage": 100,
        "enable_ai_esp_matching": True,
        "send_as_plain_text": False
    }

    result = api_call("POST", f"/campaigns/{campaign_id}/settings", data)

    if result and result.get("ok"):
        print(f"   ✅ Click tracking enabled")
        return True
    else:
        print(f"   ❌ Failed to enable tracking")
        return False

def main():
    """Enable click tracking on all campaigns"""
    print("\n" + "="*70)
    print("ENABLING CLICK TRACKING")
    print("="*70)

    print("\nRe-enabling click tracking for active campaigns...")
    print("(UI doesn't work due to cache, using API)\n")

    success_count = 0

    for tier, campaign_id in CAMPAIGNS.items():
        if enable_tracking(tier, campaign_id):
            success_count += 1

    print("\n" + "="*70)
    print("UPDATE COMPLETE")
    print("="*70)

    if success_count == 3:
        print("\n✅ Click tracking enabled on all 3 campaigns!")
        print("\nYou'll now see:")
        print("  • Who clicks Calendly links")
        print("  • Click-through rates by sequence")
        print("  • Which tier drives most engagement")
        print("\nNote: Only tracks clicks on emails sent AFTER this change.")
    else:
        print(f"\n⚠️ Only {success_count}/3 campaigns updated")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
