#!/usr/bin/env python3
"""
Extract historical events from Smartlead using MCP tools.

This uses the Smartlead MCP tools to fetch campaign stats
and extract individual event records for backfilling.
"""

import csv
import json
import subprocess
from collections import Counter

# Campaign definitions
CAMPAIGNS = [
    {'id': 2677089, 'name': 'A-Tier', 'tier': 'A'},
    {'id': 2677090, 'name': 'B-Tier', 'tier': 'B'},
    {'id': 2677091, 'name': 'C-Tier', 'tier': 'C'},
]

def get_campaign_stats_via_mcp(campaign_id, limit=100, offset=0):
    """Fetch campaign stats using MCP tool via CLI."""
    import os
    import sys

    # Check if we're in an environment with MCP access
    # Since MCP tools are available, we'll need to use a different approach
    print(f"⚠️  Cannot directly call MCP tools from Python")
    print(f"    Solution: Using direct API calls instead")
    return None

def extract_events_from_stats(stats, campaign_id, tier):
    """Convert campaign stats into individual event records."""
    events = []

    for stat in stats:
        lead_email = stat.get('lead_email')
        stats_id = stat.get('stats_id')
        sequence_number = stat.get('sequence_number')

        # EMAIL_SENT event
        sent_time = stat.get('sent_time')
        if sent_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_SENT',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': '',
                'click_count': '',
            })

        # EMAIL_OPENED event(s)
        open_time = stat.get('open_time')
        open_count = stat.get('open_count', 0)
        if open_time and open_count > 0:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_OPENED',
                'event_timestamp': open_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': open_count,
                'click_count': '',
            })

        # EMAIL_LINK_CLICK event(s)
        click_time = stat.get('click_time')
        click_count = stat.get('click_count', 0)
        if click_time and click_count > 0:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_LINK_CLICK',
                'event_timestamp': click_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': '',
                'click_count': click_count,
            })

        # EMAIL_REPLIED event
        reply_time = stat.get('reply_time')
        if reply_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_REPLIED',
                'event_timestamp': reply_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': '',
                'click_count': '',
            })

        # EMAIL_BOUNCED event
        is_bounced = stat.get('is_bounced', False)
        if is_bounced and sent_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_BOUNCED',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': '',
                'click_count': '',
            })

        # EMAIL_UNSUBSCRIBED event
        is_unsubscribed = stat.get('is_unsubscribed', False)
        if is_unsubscribed and sent_time:
            events.append({
                'lead_email': lead_email,
                'smartlead_lead_id': '',
                'event_type': 'EMAIL_UNSUBSCRIBED',
                'event_timestamp': sent_time,
                'campaign_id': campaign_id,
                'sequence_number': sequence_number,
                'tier': tier,
                'stats_id': stats_id,
                'open_count': '',
                'click_count': '',
            })

    return events

def load_stats_from_json(filepath):
    """Load campaign stats from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('data', [])

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
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

    print(f"\n✅ Saved {len(events)} events to {output_path}")

def print_summary(events):
    """Print summary of extracted events."""
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
    """Main function to extract events."""
    print("Smartlead Historical Event Extraction (via JSON files)")
    print("="*60)
    print("\nThis script expects JSON files with campaign stats data.")
    print("Run MCP calls manually and save outputs to JSON files, then process them.\n")

    # For now, I'll provide instructions
    print("📝 INSTRUCTIONS:")
    print("1. The MCP tools have already been called and data is in the conversation")
    print("2. I'll manually process the data from the MCP responses")
    print("3. Then generate the CSV file")

    print("\n⚠️  This script needs to be run after manually collecting MCP data")
    print("    Use the alternative approach: direct API calls")

if __name__ == '__main__':
    main()
