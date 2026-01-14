#!/usr/bin/env python3
"""Export call list - leads with phone numbers and location data."""

import os
import csv
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def export_call_list():
    print("Fetching leads with phone + location data...")

    leads = []
    offset = 0
    while True:
        response = supabase.table("leads").select(
            "id, first_name, last_name, company, phone_number, email, city, state, tier, reviews_count, service_software"
        ).neq("phone_number", "").not_.is_("phone_number", "null").neq("state", "").not_.is_("state", "null").order("tier").order("state").range(offset, offset + 999).execute()

        if not response.data:
            break
        leads.extend(response.data)
        offset += 1000

    print(f"Found {len(leads)} leads")

    # Fetch email engagement data
    print("Fetching email engagement...")
    opens = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_OPEN").execute()
    clicks = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_LINK_CLICK").execute()

    # Count opens/clicks per lead
    open_counts = {}
    for e in opens.data:
        lid = e.get("lead_id")
        if lid:
            open_counts[lid] = open_counts.get(lid, 0) + 1

    click_counts = {}
    for e in clicks.data:
        lid = e.get("lead_id")
        if lid:
            click_counts[lid] = click_counts.get(lid, 0) + 1

    # Add engagement to leads
    for lead in leads:
        lead_id = lead.get("id")
        lead["email_opens"] = open_counts.get(lead_id, 0)
        lead["email_clicks"] = click_counts.get(lead_id, 0)
        del lead["id"]  # Don't export internal ID

    engaged_count = sum(1 for l in leads if l["email_opens"] > 0)
    print(f"Leads with opens: {engaged_count}")

    # Summary by tier
    tier_counts = {}
    for lead in leads:
        tier = lead.get("tier", "Unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print("\nBy tier:")
    for tier in sorted(tier_counts.keys()):
        print(f"  {tier}: {tier_counts[tier]}")

    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/exports/call_list_{timestamp}.csv"

    os.makedirs("data/exports", exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "first_name", "last_name", "company", "phone_number", "email", "city", "state", "tier", "reviews_count", "service_software", "email_opens", "email_clicks"
        ])
        writer.writeheader()
        writer.writerows(leads)

    print(f"\nExported to: {output_path}")
    return output_path

if __name__ == "__main__":
    export_call_list()
