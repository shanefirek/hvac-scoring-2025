#!/usr/bin/env python3
"""
Extract historical analytics events from Smartlead campaigns.

This script pulls email statistics from all three active campaigns and converts
them into individual event records for backfilling the analytics_events table.

Events extracted:
- EMAIL_SENT (sent_time)
- EMAIL_OPENED (open_time, with open_count for multiple opens)
- EMAIL_LINK_CLICK (click_time, with click_count)
- EMAIL_REPLIED (reply_time)
- EMAIL_BOUNCED (if is_bounced=true)
- EMAIL_UNSUBSCRIBED (if is_unsubscribed=true)

Campaign IDs:
- 2677089: A-Tier (HVAC A-Tier - Software & Scale)
- 2677090: B-Tier (HVAC B-Tier - Growth Signal)
- 2677091: C-Tier (HVAC C-Tier - Pain Focus)
"""

import os
import csv
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

SMARTLEAD_API_KEY = os.getenv('SMARTLEAD_API_KEY')
SMARTLEAD_BASE_URL = 'https://server.smartlead.ai/api/v1'

# Campaign definitions
CAMPAIGNS = [
    {'id': 2677089, 'name': 'A-Tier', 'tier': 'A'},
    {'id': 2677090, 'name': 'B-Tier', 'tier': 'B'},
    {'id': 2677091, 'name': 'C-Tier', 'tier': 'C'},
]

def get_campaign_stats(campaign_id, limit=100, offset=0):
    """Fetch campaign statistics from Smartlead API."""
    # Correct endpoint based on MCP tool usage
    url = f"{SMARTLEAD_BASE_URL}/campaigns/stats"
    params = {
        'api_key': SMARTLEAD_API_KEY,
        'campaign_id': campaign_id,
        'limit': limit,
        'offset': offset
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_all_campaign_stats(campaign_id):
    """Fetch all stats for a campaign using pagination."""
    all_stats = []
    offset = 0
    limit = 100

    print(f"Fetching stats for campaign {campaign_id}...")

    while True:
        data = get_campaign_stats(campaign_id, limit=limit, offset=offset)
        stats = data.get('data', [])

        if not stats:
            break

        all_stats.extend(stats)
        print(f"  Fetched {len(stats)} records (total: {len(all_stats)})")

        # Check if we got all records
        total_stats = int(data.get('total_stats', 0))
        if len(all_stats) >= total_stats:
            break

        offset += limit

    print(f"  Total stats fetched: {len(all_stats)}")
    return all_stats

def extract_events_from_stats(stats, campaign_id, tier):
    """Convert campaign stats into individual event records."""
    events = []

    for stat in stats:
        lead_email = stat.get('lead_email')
        stats_id = stat.get('stats_id')
        sequence_number = stat.get('sequence_number')

        # Extract stats_id as a proxy for smartlead_lead_id
        # Note: stats_id is the email stats ID, not the lead ID
        # We'll need to match by email in Supabase

        # EMAIL_SENT event (always present if sent_time exists)
        sent_time = stat.get('sent_time')
        if sent_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,  # Will be populated during import
                'event_type': 'EMAIL_SENT',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
            })

        # EMAIL_OPENED event(s)
        open_time = stat.get('open_time')
        open_count = stat.get('open_count', 0)
        if open_time and open_count > 0:
            # Create one event for first open (with timestamp)
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,
                'event_type': 'EMAIL_OPENED',
                'event_timestamp': open_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': open_count,
            })

        # EMAIL_LINK_CLICK event(s)
        click_time = stat.get('click_time')
        click_count = stat.get('click_count', 0)
        if click_time and click_count > 0:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,
                'event_type': 'EMAIL_LINK_CLICK',
                'event_timestamp': click_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'click_count': click_count,
            })

        # EMAIL_REPLIED event
        reply_time = stat.get('reply_time')
        if reply_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,
                'event_type': 'EMAIL_REPLIED',
                'event_timestamp': reply_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
            })

        # EMAIL_BOUNCED event
        is_bounced = stat.get('is_bounced', False)
        if is_bounced and sent_time:
            # Use sent_time as bounce time (actual bounce time not provided)
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,
                'event_type': 'EMAIL_BOUNCED',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
            })

        # EMAIL_UNSUBSCRIBED event
        is_unsubscribed = stat.get('is_unsubscribed', False)
        if is_unsubscribed and sent_time:
            # Use sent_time as unsubscribe time (actual time not provided)
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': None,
                'event_type': 'EMAIL_UNSUBSCRIBED',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
            })

    return events

def save_events_to_csv(events, output_path):
    """Save events to CSV file."""
    fieldnames = [
        'lead_email',
        'smartlead_lead_id',
        'event_type',
        'event_timestamp',
        'campaign_id',
        'sequence_number',
        'tier',
        'stats_id',
        'open_count',
        'click_count',
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for event in events:
            # Fill in optional fields
            row = {field: event.get(field, '') for field in fieldnames}
            writer.writerow(row)

    print(f"\nSaved {len(events)} events to {output_path}")

def print_summary(events):
    """Print summary of extracted events."""
    from collections import Counter

    print("\n" + "="*60)
    print("EVENT EXTRACTION SUMMARY")
    print("="*60)

    # Count by event type
    event_types = Counter(e['event_type'] for e in events)
    print("\nEvents by Type:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type:20s}: {count:4d}")

    # Count by campaign
    campaigns = Counter(e['campaign_id'] for e in events)
    print("\nEvents by Campaign:")
    for campaign_id, count in sorted(campaigns.items()):
        campaign_name = next((c['name'] for c in CAMPAIGNS if c['id'] == campaign_id), 'Unknown')
        print(f"  Campaign {campaign_id} ({campaign_name}): {count:4d}")

    # Count by tier
    tiers = Counter(e['tier'] for e in events)
    print("\nEvents by Tier:")
    for tier, count in sorted(tiers.items()):
        print(f"  Tier {tier}: {count:4d}")

    print(f"\nTotal Events: {len(events)}")
    print("="*60)

def main():
    """Main execution function."""
    print("Smartlead Historical Event Extraction")
    print("="*60)

    all_events = []

    # Extract events from each campaign
    for campaign in CAMPAIGNS:
        campaign_id = campaign['id']
        campaign_name = campaign['name']
        tier = campaign['tier']

        print(f"\nProcessing Campaign {campaign_id} ({campaign_name})...")

        # Fetch all stats
        stats = fetch_all_campaign_stats(campaign_id)

        # Extract events
        events = extract_events_from_stats(stats, campaign_id, tier)
        print(f"  Extracted {len(events)} events")

        all_events.extend(events)

    # Print summary
    print_summary(all_events)

    # Save to CSV
    output_path = '/Users/shanefirek/projects/appletree-outbound-2025/appletree-data-pipeline/data/smartlead_events_backfill.csv'
    save_events_to_csv(all_events, output_path)

    print(f"\n✅ Successfully extracted {len(all_events)} events")
    print(f"📁 Saved to: {output_path}")
    print("\nNext steps:")
    print("1. Review the CSV file")
    print("2. Import events into Supabase analytics_events table")
    print("3. Match smartlead_lead_id by joining on email addresses")

if __name__ == '__main__':
    main()
