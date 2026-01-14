#!/usr/bin/env python3
"""
Extract ALL historical analytics events from Smartlead campaigns and save to CSV.
Then import into Supabase analytics_events table.
"""

import requests
import csv
from datetime import datetime

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    2677089: {"name": "A-Tier - Software & Scale", "tier": "A"},
    2677090: {"name": "B-Tier - Growth Signal", "tier": "B"},
    2677091: {"name": "C-Tier - Pain Focus", "tier": "C"}
}

def get_campaign_stats(campaign_id, limit=500):
    """Get email statistics for a campaign"""
    url = f"{BASE_URL}/campaigns/{campaign_id}/email-statistics"
    params = {
        "api_key": API_KEY,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"   ❌ Error fetching stats for campaign {campaign_id}: {e}")
        return []

def extract_events_from_stats(stats, campaign_id, tier):
    """Convert campaign stats into individual event records"""
    events = []

    for stat in stats:
        email = stat.get("lead_email", "").lower().strip()
        seq_num = stat.get("sequence_number", 1)
        sent_time = stat.get("sent_time")
        open_time = stat.get("open_time")
        click_time = stat.get("click_time")
        reply_time = stat.get("reply_time")
        open_count = stat.get("open_count", 0)
        click_count = stat.get("click_count", 0)
        is_bounced = stat.get("is_bounced", False)
        is_unsubscribed = stat.get("is_unsubscribed", False)
        stats_id = stat.get("stats_id", "")

        if not email:
            continue

        # EMAIL_SENT event
        if sent_time:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_SENT",
                "event_timestamp": sent_time,
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": "",
                "click_count": ""
            })

        # EMAIL_OPENED event (only if actually opened)
        if open_time and open_count > 0:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_OPENED",
                "event_timestamp": open_time,
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": open_count,
                "click_count": ""
            })

        # EMAIL_LINK_CLICK event
        if click_time and click_count > 0:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_LINK_CLICK",
                "event_timestamp": click_time,
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": "",
                "click_count": click_count
            })

        # EMAIL_REPLIED event
        if reply_time:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_REPLIED",
                "event_timestamp": reply_time,
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": "",
                "click_count": ""
            })

        # EMAIL_BOUNCED event
        if is_bounced:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_BOUNCED",
                "event_timestamp": sent_time,  # Use sent time as bounce time
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": "",
                "click_count": ""
            })

        # EMAIL_UNSUBSCRIBED event
        if is_unsubscribed:
            events.append({
                "lead_email": email,
                "event_type": "EMAIL_UNSUBSCRIBED",
                "event_timestamp": reply_time or open_time or sent_time,
                "campaign_id": campaign_id,
                "sequence_number": seq_num,
                "tier": tier,
                "stats_id": stats_id,
                "open_count": "",
                "click_count": ""
            })

    return events

def save_to_csv(events, output_path):
    """Save events to CSV"""
    print(f"\n💾 Saving {len(events)} events to {output_path}...")

    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'lead_email', 'event_type', 'event_timestamp',
            'campaign_id', 'sequence_number', 'tier',
            'stats_id', 'open_count', 'click_count'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

    print(f"✅ CSV saved successfully")

def main():
    print("\n" + "="*70)
    print("🚀 EXTRACTING SMARTLEAD ANALYTICS EVENTS")
    print("="*70 + "\n")

    all_events = []

    for campaign_id, config in CAMPAIGNS.items():
        campaign_name = config["name"]
        tier = config["tier"]

        print(f"📊 Campaign {campaign_id}: {campaign_name}")

        # Get all stats for this campaign
        stats = get_campaign_stats(campaign_id)

        if not stats:
            print(f"   ⚠️  No stats returned")
            continue

        print(f"   Found {len(stats)} email statistics")

        # Convert stats to individual events
        events = extract_events_from_stats(stats, campaign_id, tier)
        all_events.extend(events)

        # Count by event type
        event_types = {}
        for event in events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

        print(f"   Events extracted:")
        for event_type, count in sorted(event_types.items()):
            print(f"      {event_type}: {count}")
        print()

    # Save to CSV
    output_path = "data/smartlead_events_backfill.csv"
    save_to_csv(all_events, output_path)

    # Summary
    print("\n" + "="*70)
    print("📈 EXTRACTION SUMMARY")
    print("="*70)
    print(f"   Total events extracted: {len(all_events)}")

    event_summary = {}
    for event in all_events:
        event_type = event['event_type']
        event_summary[event_type] = event_summary.get(event_type, 0) + 1

    print(f"\n   By event type:")
    for event_type, count in sorted(event_summary.items()):
        print(f"      {event_type}: {count}")

    print(f"\n   Output file: {output_path}")
    print(f"\n✅ Extraction complete!")
    print(f"\n   Next: Run import script to load into Supabase\n")

if __name__ == "__main__":
    main()
