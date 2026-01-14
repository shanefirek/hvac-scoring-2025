#!/usr/bin/env python3
"""
Backfill historical analytics events from Smartlead into Supabase.

This script:
1. Fetches all lead statistics from Smartlead campaigns
2. Parses event history (sends, opens, clicks, replies, etc.)
3. Compares with existing Supabase events
4. Inserts missing events into analytics_events table

Gap identified (from audit):
- A-Tier: 16 missing events
- B-Tier: 4 missing events
- C-Tier: 117 missing events
Total: ~137 missing events
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

load_dotenv()

# Configuration
SMARTLEAD_API_KEY = os.getenv("SMARTLEAD_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Campaign IDs
CAMPAIGNS = {
    "A-Tier": 2677089,
    "B-Tier": 2677090,
    "C-Tier": 2677091,
}

# Event type mapping: Smartlead -> Supabase
EVENT_TYPE_MAP = {
    "SENT": "EMAIL_SENT",
    "OPENED": "EMAIL_OPEN",
    "CLICKED": "EMAIL_LINK_CLICK",
    "REPLIED": "EMAIL_REPLIED",
    "BOUNCED": "EMAIL_BOUNCED",
    "UNSUBSCRIBED": "EMAIL_UNSUBSCRIBED",
    "SPAM": "EMAIL_SPAM_COMPLAINT",
}


def get_smartlead_lead_stats(campaign_id: int, limit: int = 100, offset: int = 0) -> Dict:
    """Fetch lead statistics from Smartlead API."""
    url = f"https://server.smartlead.ai/api/v1/campaigns/lead-stats"
    params = {
        "api_key": SMARTLEAD_API_KEY,
        "campaign_id": campaign_id,
        "limit": limit,
        "offset": offset,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_all_campaign_leads(campaign_id: int) -> List[Dict]:
    """Fetch all leads for a campaign with pagination."""
    all_leads = []
    offset = 0
    limit = 100

    print(f"  Fetching leads (batch size: {limit})...")

    while True:
        data = get_smartlead_lead_stats(campaign_id, limit=limit, offset=offset)
        leads = data.get("data", [])

        if not leads:
            break

        all_leads.extend(leads)
        print(f"    Fetched {len(all_leads)} leads so far...")

        # Check if there are more leads
        if not data.get("hasMore", False):
            break

        offset += limit

    print(f"  Total leads fetched: {len(all_leads)}")
    return all_leads


def parse_lead_events(lead: Dict, campaign_id: int) -> List[Dict]:
    """Parse events from a lead's history."""
    events = []
    lead_email = lead.get("to", "").lower()
    lead_id_smartlead = lead.get("lead_id")

    history = lead.get("history", [])

    for event in history:
        event_type = event.get("type")
        stats_id = event.get("stats_id")
        message_id = event.get("message_id")
        sent_time = event.get("time")
        open_count = event.get("open_count", 0)
        click_count = event.get("click_count", 0)
        seq_number = event.get("email_seq_number")

        # Add SENT event
        if event_type == "SENT" and sent_time:
            events.append({
                "email": lead_email,
                "smartlead_lead_id": lead_id_smartlead,
                "smartlead_campaign_id": campaign_id,
                "event_type": "EMAIL_SENT",
                "event_time": sent_time,
                "stats_id": stats_id,
                "message_id": message_id,
                "sequence_number": seq_number,
                "metadata": {
                    "subject": event.get("subject"),
                    "from": lead.get("from"),
                }
            })

        # Add OPEN events (based on open_count)
        # Note: We don't have individual open timestamps, so we'll use sent_time as approximation
        # This is a limitation - we can't backfill exact open times
        if open_count > 0:
            for i in range(open_count):
                events.append({
                    "email": lead_email,
                    "smartlead_lead_id": lead_id_smartlead,
                    "smartlead_campaign_id": campaign_id,
                    "event_type": "EMAIL_OPEN",
                    "event_time": sent_time,  # Approximation
                    "stats_id": stats_id,
                    "message_id": message_id,
                    "sequence_number": seq_number,
                    "metadata": {
                        "subject": event.get("subject"),
                        "open_number": i + 1,
                        "note": "Backfilled - exact timestamp unavailable"
                    }
                })

        # Add CLICK events (based on click_count)
        if click_count > 0:
            click_details = event.get("click_details", {})
            for i in range(click_count):
                events.append({
                    "email": lead_email,
                    "smartlead_lead_id": lead_id_smartlead,
                    "smartlead_campaign_id": campaign_id,
                    "event_type": "EMAIL_LINK_CLICK",
                    "event_time": sent_time,  # Approximation
                    "stats_id": stats_id,
                    "message_id": message_id,
                    "sequence_number": seq_number,
                    "metadata": {
                        "subject": event.get("subject"),
                        "click_number": i + 1,
                        "click_details": click_details,
                        "note": "Backfilled - exact timestamp unavailable"
                    }
                })

    return events


def get_existing_events(supabase: Client) -> Set[str]:
    """Get set of existing event identifiers to avoid duplicates."""
    response = supabase.table("analytics_events").select(
        "smartlead_campaign_id,event_type,stats_id,message_id,created_at"
    ).execute()

    # Create unique identifiers for existing events
    # Using stats_id + event_type as the unique key
    existing = set()
    for event in response.data:
        # For backfilled events without exact timestamps, we need fuzzy matching
        # Use stats_id + event_type as identifier
        stats_id = event.get("stats_id")
        event_type = event.get("event_type")
        if stats_id and event_type:
            existing.add(f"{stats_id}:{event_type}")

    return existing


def match_email_to_lead_id(supabase: Client, email: str) -> str:
    """Match email to lead_id in Supabase."""
    response = supabase.table("leads").select("id").eq("email", email.lower()).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]["id"]

    return None


def insert_analytics_events(supabase: Client, events: List[Dict], dry_run: bool = True) -> int:
    """Insert analytics events into Supabase."""
    if not events:
        print("  No new events to insert")
        return 0

    # Get existing events to avoid duplicates
    existing_events = get_existing_events(supabase)
    print(f"  Found {len(existing_events)} existing events in Supabase")

    # Filter out duplicates
    new_events = []
    skipped = 0

    for event in events:
        # Create event identifier
        stats_id = event.get("stats_id")
        event_type = event.get("event_type")
        event_id = f"{stats_id}:{event_type}"

        if event_id in existing_events:
            skipped += 1
            continue

        # Match email to lead_id
        email = event.get("email")
        lead_id = match_email_to_lead_id(supabase, email)

        if not lead_id:
            print(f"  WARNING: No lead found for email {email}, skipping event")
            continue

        # Prepare event for insertion
        new_events.append({
            "lead_id": lead_id,
            "smartlead_lead_id": str(event.get("smartlead_lead_id")),
            "smartlead_campaign_id": event.get("smartlead_campaign_id"),
            "event_type": event.get("event_type"),
            "stats_id": event.get("stats_id"),
            "message_id": event.get("message_id"),
            "sequence_number": event.get("sequence_number"),
            "metadata": event.get("metadata", {}),
            "created_at": event.get("event_time"),
        })

    print(f"  Skipped {skipped} duplicate events")
    print(f"  Prepared {len(new_events)} new events for insertion")

    if dry_run:
        print(f"  [DRY RUN] Would insert {len(new_events)} events")
        # Show sample events
        if new_events:
            print("\n  Sample events (first 3):")
            for event in new_events[:3]:
                print(f"    - {event['event_type']} for lead {event['lead_id'][:8]}... at {event['created_at']}")
        return len(new_events)

    # Insert in batches
    batch_size = 100
    inserted = 0

    for i in range(0, len(new_events), batch_size):
        batch = new_events[i:i + batch_size]
        response = supabase.table("analytics_events").insert(batch).execute()
        inserted += len(response.data)
        print(f"  Inserted batch {i//batch_size + 1}: {len(response.data)} events")

    return inserted


def backfill_campaign(campaign_name: str, campaign_id: int, supabase: Client, dry_run: bool = True) -> Dict:
    """Backfill analytics events for a single campaign."""
    print(f"\n{'='*60}")
    print(f"Processing {campaign_name} (Campaign ID: {campaign_id})")
    print(f"{'='*60}")

    # Fetch all leads
    leads = fetch_all_campaign_leads(campaign_id)

    # Parse all events
    all_events = []
    for lead in leads:
        events = parse_lead_events(lead, campaign_id)
        all_events.extend(events)

    # Summarize events
    event_summary = {}
    for event in all_events:
        event_type = event["event_type"]
        event_summary[event_type] = event_summary.get(event_type, 0) + 1

    print(f"\n  Event Summary from Smartlead:")
    for event_type, count in sorted(event_summary.items()):
        print(f"    {event_type}: {count}")
    print(f"  Total: {len(all_events)} events")

    # Insert events
    inserted = insert_analytics_events(supabase, all_events, dry_run=dry_run)

    return {
        "campaign": campaign_name,
        "total_leads": len(leads),
        "total_events": len(all_events),
        "events_summary": event_summary,
        "inserted": inserted,
    }


def main():
    """Main backfill function."""
    import argparse

    parser = argparse.ArgumentParser(description="Backfill analytics events from Smartlead")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Run without inserting data (default: True)")
    parser.add_argument("--execute", action="store_true",
                       help="Actually insert data into Supabase")
    parser.add_argument("--campaign", choices=["A-Tier", "B-Tier", "C-Tier", "all"],
                       default="all", help="Which campaign to backfill")

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.execute

    print(f"\n{'#'*60}")
    print(f"# Analytics Events Backfill Script")
    print(f"# Mode: {'DRY RUN (no data will be inserted)' if dry_run else 'EXECUTE (data will be inserted)'}")
    print(f"# Target: {args.campaign}")
    print(f"{'#'*60}\n")

    if not dry_run:
        confirm = input("Are you sure you want to INSERT data into Supabase? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Select campaigns to process
    campaigns_to_process = {}
    if args.campaign == "all":
        campaigns_to_process = CAMPAIGNS
    else:
        campaigns_to_process = {args.campaign: CAMPAIGNS[args.campaign]}

    # Process campaigns
    results = []
    for campaign_name, campaign_id in campaigns_to_process.items():
        result = backfill_campaign(campaign_name, campaign_id, supabase, dry_run=dry_run)
        results.append(result)

    # Print summary
    print(f"\n{'='*60}")
    print(f"BACKFILL SUMMARY")
    print(f"{'='*60}")

    total_leads = sum(r["total_leads"] for r in results)
    total_events = sum(r["total_events"] for r in results)
    total_inserted = sum(r["inserted"] for r in results)

    for result in results:
        print(f"\n{result['campaign']}:")
        print(f"  Leads processed: {result['total_leads']}")
        print(f"  Events found: {result['total_events']}")
        print(f"  Events {'would be' if dry_run else ''} inserted: {result['inserted']}")

    print(f"\nTOTALS:")
    print(f"  Leads: {total_leads}")
    print(f"  Events: {total_events}")
    print(f"  {'Would insert' if dry_run else 'Inserted'}: {total_inserted}")

    if dry_run:
        print(f"\n{'='*60}")
        print(f"This was a DRY RUN. No data was inserted.")
        print(f"To actually insert data, run with --execute flag:")
        print(f"  python {__file__} --execute")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
