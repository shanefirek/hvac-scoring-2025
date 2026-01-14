#!/usr/bin/env python3
"""Export all Supabase leads with data quality flags."""

import os
import csv
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def export_all():
    print("Exporting all Supabase leads with quality flags...")

    # Get all leads with pagination
    all_leads = []
    offset = 0
    while True:
        batch = supabase.table("leads").select("*").range(offset, offset + 999).execute()
        if not batch.data:
            break
        all_leads.extend(batch.data)
        offset += 1000
        print(f"  Fetched {len(all_leads)} leads...")

    print(f"Total leads: {len(all_leads)}")

    # Get engagement data
    print("\nFetching engagement data...")
    opens = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_OPEN").execute()
    clicks = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_LINK_CLICK").execute()
    replies = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_REPLIED").execute()
    bounces = supabase.table("analytics_events").select("lead_id").eq("event_type", "EMAIL_BOUNCED").execute()

    open_ids = set(e["lead_id"] for e in opens.data if e.get("lead_id"))
    click_ids = set(e["lead_id"] for e in clicks.data if e.get("lead_id"))
    reply_ids = set(e["lead_id"] for e in replies.data if e.get("lead_id"))
    bounce_ids = set(e["lead_id"] for e in bounces.data if e.get("lead_id"))

    print(f"  Opens: {len(open_ids)} leads")
    print(f"  Clicks: {len(click_ids)} leads")
    print(f"  Replies: {len(reply_ids)} leads")
    print(f"  Bounces: {len(bounce_ids)} leads")

    # Process leads with quality flags
    export_data = []
    for lead in all_leads:
        lead_id = lead.get("id")

        export_data.append({
            "id": lead_id,
            "email": lead.get("email", ""),
            "first_name": lead.get("first_name", ""),
            "last_name": lead.get("last_name", ""),
            "company": lead.get("company", ""),
            "phone_number": lead.get("phone_number", ""),
            "city": lead.get("city", ""),
            "state": lead.get("state", ""),
            "tier": lead.get("tier", ""),
            "score": lead.get("score", ""),
            "reviews_count": lead.get("reviews_count", ""),
            "service_software": lead.get("service_software", ""),
            "domain": lead.get("domain", ""),
            "clay_id": lead.get("clay_id", ""),
            "smartlead_lead_id": lead.get("smartlead_lead_id", ""),
            "in_smartlead": lead.get("in_smartlead", False),
            "created_at": lead.get("created_at", ""),
            # Quality flags
            "has_email": "✓" if lead.get("email") else "✗",
            "has_phone": "✓" if lead.get("phone_number") else "✗",
            "has_city": "✓" if lead.get("city") else "✗",
            "has_state": "✓" if lead.get("state") else "✗",
            "has_clay_id": "✓" if lead.get("clay_id") else "✗",
            "has_smartlead_id": "✓" if lead.get("smartlead_lead_id") else "✗",
            # Engagement flags
            "has_opens": "✓" if lead_id in open_ids else "✗",
            "has_clicks": "✓" if lead_id in click_ids else "✗",
            "has_replies": "✓" if lead_id in reply_ids else "✗",
            "is_bounced": "✓" if lead_id in bounce_ids else "✗",
        })

    # Export to CSV
    output_path = "data/audit/supabase_full_export.csv"
    with open(output_path, "w", newline="") as f:
        if export_data:
            writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)

    print(f"\n{'='*50}")
    print(f"Exported {len(export_data)} leads to {output_path}")

    # Quality summary
    print("\nData Quality Summary:")
    total = len(export_data)
    has_phone = sum(1 for l in export_data if l["has_phone"] == "✓")
    has_city = sum(1 for l in export_data if l["has_city"] == "✓")
    has_state = sum(1 for l in export_data if l["has_state"] == "✓")
    has_clay_id = sum(1 for l in export_data if l["has_clay_id"] == "✓")
    has_smartlead_id = sum(1 for l in export_data if l["has_smartlead_id"] == "✓")
    has_opens = sum(1 for l in export_data if l["has_opens"] == "✓")
    has_clicks = sum(1 for l in export_data if l["has_clicks"] == "✓")
    is_bounced = sum(1 for l in export_data if l["is_bounced"] == "✓")

    print(f"  Has phone: {has_phone}/{total} ({100*has_phone/total:.1f}%)")
    print(f"  Has city: {has_city}/{total} ({100*has_city/total:.1f}%)")
    print(f"  Has state: {has_state}/{total} ({100*has_state/total:.1f}%)")
    print(f"  Has clay_id: {has_clay_id}/{total} ({100*has_clay_id/total:.1f}%)")
    print(f"  Has smartlead_id: {has_smartlead_id}/{total} ({100*has_smartlead_id/total:.1f}%)")
    print(f"  Has opens: {has_opens}/{total} ({100*has_opens/total:.1f}%)")
    print(f"  Has clicks: {has_clicks}/{total} ({100*has_clicks/total:.1f}%)")
    print(f"  Is bounced: {is_bounced}/{total} ({100*is_bounced/total:.1f}%)")

    # Priority re-enrichment: has engagement but missing phone
    priority = sum(1 for l in export_data if l["has_opens"] == "✓" and l["has_phone"] == "✗")
    print(f"\n  PRIORITY RE-ENRICH (has opens, no phone): {priority}")

    return export_data


if __name__ == "__main__":
    export_all()
