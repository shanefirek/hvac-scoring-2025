#!/usr/bin/env python3
"""
Update Daily Send Limits for All Campaigns

Bumps send limits from conservative to aggressive:
- A-Tier: 10 → 30 leads/day
- B-Tier: 8 → 25 leads/day
- C-Tier: 10 → 30 leads/day

Usage:
    python update_send_limits.py
"""

import requests
import json

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    "A-Tier": {"id": 2677089, "old_limit": 10, "new_limit": 30},
    "B-Tier": {"id": 2677090, "old_limit": 8, "new_limit": 25},
    "C-Tier": {"id": 2677091, "old_limit": 10, "new_limit": 30}
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

def update_send_limit(tier, config):
    """Update send limit for a campaign"""
    campaign_id = config["id"]
    new_limit = config["new_limit"]

    print(f"\n📊 {tier} Campaign (ID: {campaign_id})")
    print(f"   Updating: {config['old_limit']}/day → {new_limit}/day")

    # Get current schedule settings
    info = api_call("GET", f"/campaigns/{campaign_id}")
    if not info:
        print(f"   ❌ Failed to get campaign info")
        return False

    schedule = info.get("scheduler_cron_value", {})

    # Update schedule with new limit
    data = {
        "timezone": schedule.get("tz", "America/New_York"),
        "days_of_the_week": schedule.get("days", [1, 2, 3, 4, 5]),
        "start_hour": schedule.get("startHour", "09:00"),
        "end_hour": schedule.get("endHour", "17:00"),
        "min_time_btw_emails": info.get("min_time_btwn_emails", 3),
        "max_new_leads_per_day": new_limit
    }

    result = api_call("POST", f"/campaigns/{campaign_id}/schedule", data)

    if result and result.get("ok"):
        print(f"   ✅ Updated to {new_limit} leads/day")
        return True
    else:
        print(f"   ❌ Failed to update")
        return False

def main():
    """Update all campaign limits"""
    print("\n" + "="*70)
    print("UPDATING DAILY SEND LIMITS")
    print("="*70)

    print("\nBumping from conservative to aggressive scale:")
    print("  - Faster lead burn rate")
    print("  - 3-4x send volume")
    print("  - Still well within safe limits for warmed accounts\n")

    success_count = 0

    for tier, config in CAMPAIGNS.items():
        if update_send_limit(tier, config):
            success_count += 1

    print("\n" + "="*70)
    print("UPDATE COMPLETE")
    print("="*70)

    if success_count == 3:
        print("\n✅ All 3 campaigns updated successfully!")
        print("\nNew daily capacity:")
        print("  A-Tier: 30 leads/day")
        print("  B-Tier: 25 leads/day")
        print("  C-Tier: 30 leads/day")
        print("  TOTAL: ~85 leads/day")
        print("\nWith 150 current leads:")
        print("  - All leads loaded by Thursday")
        print("  - Ready for next 150-lead batch Friday")
        print("  - ~85 sends/day across 3 accounts = ~28 sends/account")
    else:
        print(f"\n⚠️ Only {success_count}/3 campaigns updated")
        print("Check errors above and retry if needed")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
