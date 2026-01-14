#!/usr/bin/env python3
"""
Backfill analytics_events from Smartlead API

This script pulls campaign stats from Smartlead and inserts events into Supabase.
Uses MCP-style pagination to handle large datasets.

Usage:
    python scripts/recovery/backfill_analytics_from_smartlead.py
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid

load_dotenv()

# Config
SMARTLEAD_API_KEY = os.getenv("SMARTLEAD_API_KEY", "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Campaign mapping
CAMPAIGNS = {
    2677089: "A-Tier",
    2677090: "B-Tier",
    2677091: "C-Tier"
}

def get_supabase_client() -> Client:
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_lead_email_map(supabase: Client) -> dict:
    """Get email -> lead_id mapping from Supabase"""
    result = supabase.table("leads").select("id, email, smartlead_lead_id").execute()
    return {row["email"].lower(): {"id": row["id"], "smartlead_lead_id": row["smartlead_lead_id"]}
            for row in result.data}

def get_campaign_stats(campaign_id: int, limit: int = 100, offset: int = 0) -> dict:
    """Fetch campaign stats from Smartlead API with pagination"""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/statistics"
    params = {
        "api_key": SMARTLEAD_API_KEY,
        "limit": limit,
        "offset": offset
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_all_campaign_stats(campaign_id: int) -> list:
    """Fetch all stats for a campaign using pagination"""
    all_stats = []
    offset = 0
    limit = 100

    while True:
        result = get_campaign_stats(campaign_id, limit, offset)
        stats = result.get("data", [])
        if not stats:
            break
        all_stats.extend(stats)
        print(f"  Fetched {len(all_stats)} stats (offset={offset})")
        if len(stats) < limit:
            break
        offset += limit

    return all_stats

def create_events_from_stat(stat: dict, campaign_id: int, lead_info: dict) -> list:
    """Create analytics events from a single stat record"""
    events = []
    lead_id = lead_info["id"]
    smartlead_lead_id = lead_info.get("smartlead_lead_id")
    stats_id = stat.get("stats_id")
    sequence_number = stat.get("sequence_number")
    email_subject = stat.get("email_subject")

    # EMAIL_SENT event
    if stat.get("sent_time"):
        events.append({
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "smartlead_campaign_id": campaign_id,
            "smartlead_lead_id": smartlead_lead_id,
            "event_type": "EMAIL_SENT",
            "sequence_number": sequence_number,
            "email_subject": email_subject,
            "email_stats_id": stats_id,
            "event_data": {"source": "backfill", "original_time": stat.get("sent_time")},
            "created_at": stat.get("sent_time")
        })

    # EMAIL_OPEN event
    if stat.get("open_time"):
        events.append({
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "smartlead_campaign_id": campaign_id,
            "smartlead_lead_id": smartlead_lead_id,
            "event_type": "EMAIL_OPEN",
            "sequence_number": sequence_number,
            "email_subject": email_subject,
            "email_stats_id": stats_id,
            "event_data": {"source": "backfill", "open_count": stat.get("open_count", 1)},
            "created_at": stat.get("open_time")
        })

    # EMAIL_LINK_CLICK event
    if stat.get("click_time"):
        events.append({
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "smartlead_campaign_id": campaign_id,
            "smartlead_lead_id": smartlead_lead_id,
            "event_type": "EMAIL_LINK_CLICK",
            "sequence_number": sequence_number,
            "email_subject": email_subject,
            "email_stats_id": stats_id,
            "event_data": {"source": "backfill", "click_count": stat.get("click_count", 1)},
            "created_at": stat.get("click_time")
        })

    # EMAIL_REPLIED event
    if stat.get("reply_time"):
        events.append({
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "smartlead_campaign_id": campaign_id,
            "smartlead_lead_id": smartlead_lead_id,
            "event_type": "EMAIL_REPLIED",
            "sequence_number": sequence_number,
            "email_subject": email_subject,
            "email_stats_id": stats_id,
            "event_data": {"source": "backfill"},
            "created_at": stat.get("reply_time")
        })

    # EMAIL_BOUNCED event
    if stat.get("is_bounced"):
        events.append({
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "smartlead_campaign_id": campaign_id,
            "smartlead_lead_id": smartlead_lead_id,
            "event_type": "EMAIL_BOUNCED",
            "sequence_number": sequence_number,
            "email_subject": email_subject,
            "email_stats_id": stats_id,
            "event_data": {"source": "backfill"},
            "created_at": stat.get("sent_time")  # Use sent_time for bounces
        })

    return events

def main():
    print("=" * 60)
    print("Backfill Analytics Events from Smartlead")
    print("=" * 60)

    # Initialize clients
    print("\n1. Connecting to Supabase...")
    supabase = get_supabase_client()

    # Get lead mapping
    print("2. Loading lead email -> UUID mapping...")
    email_map = get_lead_email_map(supabase)
    print(f"   Found {len(email_map)} leads in Supabase")

    # Get existing events to avoid duplicates
    print("3. Checking existing analytics_events...")
    existing = supabase.table("analytics_events").select("email_stats_id, event_type").execute()
    existing_keys = {(e["email_stats_id"], e["event_type"]) for e in existing.data if e["email_stats_id"]}
    print(f"   Found {len(existing_keys)} existing events")

    # Process each campaign
    all_events = []
    unmatched_emails = set()

    for campaign_id, tier in CAMPAIGNS.items():
        print(f"\n4. Processing Campaign {campaign_id} ({tier})...")
        stats = get_all_campaign_stats(campaign_id)
        print(f"   Total stats: {len(stats)}")

        for stat in stats:
            email = stat.get("lead_email", "").lower()
            if email not in email_map:
                unmatched_emails.add(email)
                continue

            lead_info = email_map[email]
            events = create_events_from_stat(stat, campaign_id, lead_info)

            # Filter out duplicates
            for event in events:
                key = (event["email_stats_id"], event["event_type"])
                if key not in existing_keys:
                    all_events.append(event)
                    existing_keys.add(key)

    print(f"\n5. Summary:")
    print(f"   Total new events to insert: {len(all_events)}")
    print(f"   Unmatched emails: {len(unmatched_emails)}")

    if unmatched_emails:
        print(f"\n   Sample unmatched emails:")
        for email in list(unmatched_emails)[:5]:
            print(f"     - {email}")

    # Insert events in batches
    if all_events:
        print(f"\n6. Inserting events in batches...")
        batch_size = 50
        inserted = 0

        for i in range(0, len(all_events), batch_size):
            batch = all_events[i:i + batch_size]
            try:
                supabase.table("analytics_events").insert(batch).execute()
                inserted += len(batch)
                print(f"   Inserted batch {i // batch_size + 1}: {len(batch)} events (total: {inserted})")
            except Exception as e:
                print(f"   Error inserting batch: {e}")
                # Try inserting one by one
                for event in batch:
                    try:
                        supabase.table("analytics_events").insert(event).execute()
                        inserted += 1
                    except Exception as e2:
                        print(f"     Failed single insert: {e2}")

        print(f"\n   Total inserted: {inserted}")

    # Final count
    print("\n7. Final analytics_events count:")
    count = supabase.table("analytics_events").select("id", count="exact").execute()
    print(f"   {count.count} total events")

    print("\n" + "=" * 60)
    print("Backfill complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
