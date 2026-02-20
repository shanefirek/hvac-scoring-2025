#!/usr/bin/env python3
"""Import marketing agency leads from CSV to Supabase."""

import csv
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CSV_PATH = "data/marketingleadsappletree2026.csv"

def parse_csv():
    leads = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("Work Email", "").strip()
            if not email or "@" not in email:
                continue

            lead = {
                "email": email.lower(),
                "first_name": row.get("First Name", "").strip() or None,
                "last_name": row.get("Last Name", "").strip() or None,
                "company": row.get("Company Name", "").strip() or row.get("Company", "").strip() or None,
                "domain": row.get("Company Domain", "").strip() or None,
                "linkedin_url": row.get("LinkedIn Profile", "").strip() or None,
                "city": row.get("City", "").strip() or None,
                "state": row.get("State", "").strip() or None,
                "location": row.get("Location", "").strip() or None,
                "business_type": "marketing_agency",
                "clay_id": row.get("clay_id", "").strip() or None,
            }
            leads.append(lead)
    return leads

def insert_leads(leads):
    # Insert in batches of 100
    batch_size = 100
    inserted = 0
    skipped = 0

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        try:
            result = supabase.table("leads").upsert(
                batch,
                on_conflict="email"
            ).execute()
            inserted += len(batch)
            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} leads")
        except Exception as e:
            print(f"Error inserting batch: {e}")
            skipped += len(batch)

    return inserted, skipped

if __name__ == "__main__":
    print("Parsing CSV...")
    leads = parse_csv()
    print(f"Found {len(leads)} valid leads")

    print("\nInserting into Supabase...")
    inserted, skipped = insert_leads(leads)

    print(f"\nDone! Inserted: {inserted}, Skipped: {skipped}")
