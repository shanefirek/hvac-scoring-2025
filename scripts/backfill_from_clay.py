#!/usr/bin/env python3
"""Backfill phone/city/state from Clay CSV to Supabase leads."""

import os
import csv
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_clay_data(filepath):
    """Load Clay CSV and extract relevant fields."""
    data = {}
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('Email', '').strip().lower()
            if not email:
                continue

            data[email] = {
                'phone': row.get('Phone', '').strip(),
                'city': row.get('City', '').strip(),
                'state': row.get('State', '').strip(),
                'place_id': row.get('place_id', '').strip(),
            }
    return data

def backfill():
    print("Loading Clay data...")
    clay_data = load_clay_data('data/november_clay_data_12_19_2025.csv')
    print(f"Loaded {len(clay_data)} emails from Clay")

    # Get leads that need backfill
    print("\nFetching leads from Supabase...")
    all_leads = []
    offset = 0
    while True:
        batch = supabase.table('leads').select('id, email, phone_number, city, state, place_id').range(offset, offset + 999).execute()
        if not batch.data:
            break
        all_leads.extend(batch.data)
        offset += 1000

    print(f"Found {len(all_leads)} leads in Supabase")

    # Find matches and updates needed
    updates = []
    matched = 0
    for lead in all_leads:
        email = (lead.get('email') or '').lower()
        if email not in clay_data:
            continue

        matched += 1
        clay = clay_data[email]
        update = {'id': lead['id']}
        changed = False

        # Only update if Supabase is missing and Clay has data
        if (not lead.get('phone_number')) and clay['phone']:
            update['phone_number'] = clay['phone']
            changed = True

        if (not lead.get('city')) and clay['city']:
            update['city'] = clay['city']
            changed = True

        if (not lead.get('state')) and clay['state']:
            update['state'] = clay['state']
            changed = True

        if (not lead.get('place_id')) and clay['place_id']:
            update['place_id'] = clay['place_id']
            changed = True

        if changed:
            updates.append(update)

    print(f"\nMatched {matched} leads by email")
    print(f"Updates needed: {len(updates)}")

    if not updates:
        print("Nothing to update!")
        return

    # Preview
    print("\nSample updates:")
    for u in updates[:5]:
        fields = [k for k in u.keys() if k != 'id']
        print(f"  {u['id'][:8]}... -> {fields}")

    # Confirm
    confirm = input(f"\nApply {len(updates)} updates? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    # Apply updates
    print("\nApplying updates...")
    success = 0
    for update in updates:
        lead_id = update.pop('id')
        try:
            supabase.table('leads').update(update).eq('id', lead_id).execute()
            success += 1
        except Exception as e:
            print(f"  Error updating {lead_id}: {e}")

    print(f"\nDone! Updated {success}/{len(updates)} leads")

if __name__ == "__main__":
    backfill()
