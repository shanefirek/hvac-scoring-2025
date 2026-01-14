#!/usr/bin/env python3
"""
Restore smartlead_lead_id and clay_id from validated CSV to Supabase.

The Dec 10 restore didn't carry over these attribution fields.
The CSV has 527 smartlead_lead_id and 424 clay_id values that need restoring.
"""
import os
import csv
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

CSV_PATH = 'data/raw/HVAC_clay_validated_manual_12_10_2025.csv'

def main():
    print("=" * 60)
    print("Attribution Recovery from CSV")
    print("=" * 60)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Read CSV
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\nCSV contains {len(rows)} rows")

    # Count attribution data in CSV
    csv_with_smartlead_id = [r for r in rows if r.get('smartlead_lead_id') and r['smartlead_lead_id'].strip()]
    csv_with_clay_id = [r for r in rows if r.get('clay_id') and r['clay_id'].strip()]

    print(f"  - {len(csv_with_smartlead_id)} with smartlead_lead_id")
    print(f"  - {len(csv_with_clay_id)} with clay_id")

    # Get current Supabase state
    result = supabase.table('leads').select('email, smartlead_lead_id, clay_id').execute()
    supabase_leads = {r['email'].lower(): r for r in result.data}

    print(f"\nSupabase contains {len(supabase_leads)} leads")
    supabase_with_smartlead = sum(1 for r in result.data if r['smartlead_lead_id'])
    supabase_with_clay = sum(1 for r in result.data if r['clay_id'])
    print(f"  - {supabase_with_smartlead} with smartlead_lead_id")
    print(f"  - {supabase_with_clay} with clay_id")

    # Process updates
    updates_smartlead = 0
    updates_clay = 0
    errors = []

    print("\nProcessing updates...")

    for row in rows:
        email = row.get('email', '').lower().strip()
        if not email:
            continue

        if email not in supabase_leads:
            continue

        smartlead_id = row.get('smartlead_lead_id', '').strip()
        clay_id = row.get('clay_id', '').strip()

        # Skip if nothing to update
        if not smartlead_id and not clay_id:
            continue

        # Build update payload
        update_data = {}

        if smartlead_id:
            try:
                update_data['smartlead_lead_id'] = int(smartlead_id)
                update_data['in_smartlead'] = True
            except ValueError:
                pass

        if clay_id:
            update_data['clay_id'] = clay_id

        if not update_data:
            continue

        try:
            supabase.table('leads').update(update_data).eq('email', email).execute()
            if 'smartlead_lead_id' in update_data:
                updates_smartlead += 1
            if 'clay_id' in update_data:
                updates_clay += 1
        except Exception as e:
            errors.append(f"{email}: {e}")

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print("=" * 60)
    print(f"smartlead_lead_id updates: {updates_smartlead}")
    print(f"clay_id updates: {updates_clay}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  - {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Verify final state
    result = supabase.table('leads').select('email, smartlead_lead_id, clay_id, in_smartlead').execute()
    final_smartlead = sum(1 for r in result.data if r['smartlead_lead_id'])
    final_clay = sum(1 for r in result.data if r['clay_id'])
    final_in_smartlead = sum(1 for r in result.data if r['in_smartlead'])

    print(f"\nFinal Supabase state:")
    print(f"  - {final_smartlead} with smartlead_lead_id ({final_smartlead/len(result.data)*100:.1f}%)")
    print(f"  - {final_clay} with clay_id ({final_clay/len(result.data)*100:.1f}%)")
    print(f"  - {final_in_smartlead} with in_smartlead=true")
    print("=" * 60)

if __name__ == '__main__':
    main()
