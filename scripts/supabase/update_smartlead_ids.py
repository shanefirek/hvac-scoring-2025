#!/usr/bin/env python3
"""
Update Supabase leads table with smartlead_lead_id from CSV export.
Backfills the missing IDs to fix data integrity issues.
"""

import os
import csv
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CSV_PATH = "data/smartlead_lead_ids.csv"

def update_leads():
    """Read CSV and update all leads with smartlead_lead_id"""

    print("\n" + "="*70)
    print("🚀 UPDATING SUPABASE WITH SMARTLEAD LEAD IDs")
    print("="*70 + "\n")

    # Read CSV
    leads_to_update = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads_to_update.append({
                'email': row['email'].lower().strip(),
                'smartlead_lead_id': int(row['smartlead_lead_id']),
                'campaign_id': int(row['campaign_id'])
            })

    print(f"📄 Loaded {len(leads_to_update)} leads from CSV\n")

    # Update in batches
    batch_size = 25
    updated = 0
    not_found = 0
    errors = 0

    for i in range(0, len(leads_to_update), batch_size):
        batch = leads_to_update[i:i+batch_size]
        print(f"⏳ Processing batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(leads_to_update))} of {len(leads_to_update)})...")

        for lead in batch:
            try:
                # Update the lead
                result = supabase.table('leads').update({
                    'smartlead_lead_id': lead['smartlead_lead_id']
                }).eq('email', lead['email']).execute()

                if result.data:
                    updated += 1
                    print(f"  ✅ {lead['email'][:40]:<40} → {lead['smartlead_lead_id']}")
                else:
                    not_found += 1
                    print(f"  ⚠️  {lead['email'][:40]:<40} → Not found in database")

            except Exception as e:
                errors += 1
                print(f"  ❌ {lead['email'][:40]:<40} → Error: {e}")

    # Final verification
    print("\n" + "="*70)
    print("📊 UPDATE SUMMARY")
    print("="*70)
    print(f"   ✅ Successfully updated: {updated}")
    print(f"   ⚠️  Not found in database: {not_found}")
    print(f"   ❌ Errors: {errors}")
    print(f"   📝 Total processed: {len(leads_to_update)}")

    # Check final state
    print("\n🔍 Verifying final database state...")
    result = supabase.table('leads').select('smartlead_lead_id', count='exact').not_.is_('smartlead_lead_id', 'null').execute()
    total_with_id = result.count

    result = supabase.table('leads').select('id', count='exact').execute()
    total_leads = result.count

    print(f"\n📈 FINAL STATE:")
    print(f"   Total leads in database: {total_leads}")
    print(f"   Leads with smartlead_lead_id: {total_with_id}")
    print(f"   Leads without smartlead_lead_id: {total_leads - total_with_id}")
    print(f"   Coverage: {(total_with_id/total_leads*100):.1f}%\n")

    if total_with_id >= 468:
        print("✅ SUCCESS! All Smartlead leads now have IDs in Supabase\n")
    else:
        print(f"⚠️  WARNING: Expected 468+ leads with IDs, but only found {total_with_id}\n")

if __name__ == "__main__":
    update_leads()
