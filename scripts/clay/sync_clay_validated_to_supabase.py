#!/usr/bin/env python3
"""
Sync Clay-validated leads back to Supabase.
Clears existing leads table and imports fresh validated data.
"""
import csv
import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Input CSV
CSV_FILE = "/Users/shanefirek/projects/appletree-outbound-2025/appletree-data-pipeline/data/raw/HVAC_clay_validated_manual_12_10_2025.csv"

def clean_value(value):
    """Clean CSV values - handle empty strings, 'true'/'false', etc."""
    if value == '' or value is None:
        return None
    if value == 'true':
        return True
    if value == 'false':
        return False
    # Handle numeric fields that might be strings
    return value

def parse_array(value):
    """Parse array-like string to list"""
    if not value or value == '[]' or value == '':
        return []
    # Try to eval safely for arrays
    try:
        import ast
        return ast.literal_eval(value)
    except:
        return []

def parse_json(value):
    """Parse JSON string to dict"""
    if not value or value == '{}' or value == '':
        return {}
    import json
    try:
        return json.loads(value)
    except:
        return {}

def main():
    print("=" * 60)
    print("Clay Validated Leads → Supabase Sync")
    print("=" * 60)
    print()

    # Read CSV
    print(f"📖 Reading CSV: {CSV_FILE}")
    leads = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map CSV columns to Supabase columns
            lead = {
                'id': row['id'],
                'clay_id': clean_value(row.get('clay_id')),
                'email': clean_value(row['email']) or clean_value(row['Email']),  # Handle both columns
                'first_name': clean_value(row.get('first_name')),
                'last_name': clean_value(row.get('last_name')),
                'company': clean_value(row.get('company')),
                'domain': clean_value(row.get('domain')),
                'linkedin_url': clean_value(row.get('linkedin_url')),
                'reviews_count': int(float(row['reviews_count'])) if row.get('reviews_count') and row['reviews_count'] != '' else None,
                'service_software': clean_value(row.get('service_software')),
                'score': int(float(row['score'])) if row.get('score') and row['score'] != '' else 0,
                'tier': clean_value(row.get('tier')) or 'C',
                'phone_number': clean_value(row.get('phone_number')),
                'location': clean_value(row.get('location')),
                'city': clean_value(row.get('city')),
                'state': clean_value(row.get('state')),
                'postal_code': clean_value(row.get('postal_code')),
                'place_id': clean_value(row.get('place_id')),
                'site': clean_value(row.get('site')),
                'messaging_strategy': clean_value(row.get('messaging_strategy')),
                'score_breakdown': parse_json(row.get('score_breakdown', '{}')),
                'clay_data': parse_json(row.get('clay_data', '{}')),
                'suppressed': clean_value(row.get('suppressed')) == True or row.get('suppressed') == 'true',
                'suppressed_reason': clean_value(row.get('suppressed_reason')),
                'suppressed_at': clean_value(row.get('suppressed_at')),
                'smartlead_lead_id': int(row['smartlead_lead_id']) if row.get('smartlead_lead_id') and row['smartlead_lead_id'] != '' else None,
                'in_smartlead': clean_value(row.get('in_smartlead')) == True or row.get('in_smartlead') == 'true',
                'smartlead_campaign_ids': parse_array(row.get('smartlead_campaign_ids', '[]')),
                'last_smartlead_sync': clean_value(row.get('last_smartlead_sync')),
                'data_source_priority': parse_json(row.get('data_source_priority', '{}')),
                'enriched_at': clean_value(row.get('enriched_at')),
                'last_enriched_at': clean_value(row.get('last_enriched_at')),
                'created_at': clean_value(row.get('created_at')),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Normalize email to lowercase
            if lead['email']:
                lead['email'] = lead['email'].lower().strip()

            leads.append(lead)

    print(f"✅ Read {len(leads)} leads from CSV")
    print()

    # Proceeding with deletion and sync
    print("⚠️  WARNING: Deleting all existing leads in Supabase")
    print(f"⚠️  and replacing with {len(leads)} validated leads from Clay")
    print()
    print("🗑️  Deleting all existing leads...")
    try:
        supabase.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("✅ Deleted all existing leads")
    except Exception as e:
        print(f"❌ Error deleting leads: {e}")
        return

    print()
    print(f"📥 Inserting {len(leads)} validated leads...")

    # Insert in batches of 100
    batch_size = 100
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        try:
            supabase.table('leads').insert(batch).execute()
            print(f"   ✅ Inserted batch {i//batch_size + 1} ({len(batch)} leads)")
        except Exception as e:
            print(f"   ❌ Error inserting batch {i//batch_size + 1}: {e}")
            print(f"   First lead in failed batch: {batch[0].get('email', 'unknown')}")
            # Continue with next batch

    print()
    print("=" * 60)
    print("✅ Sync Complete!")
    print("=" * 60)
    print()

    # Verify counts
    result = supabase.table('leads').select('id', count='exact').execute()
    print(f"📊 Total leads in Supabase: {result.count}")

    # Tier distribution
    result = supabase.table('leads').select('tier', count='exact').execute()
    print()
    print("📊 Tier Distribution:")
    tier_counts = {}
    for lead in result.data:
        tier = lead.get('tier', 'Unknown')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    for tier in sorted(tier_counts.keys()):
        print(f"   {tier}-Tier: {tier_counts[tier]}")

    # Address data completeness
    result = supabase.table('leads').select('city,state').execute()
    has_address = sum(1 for lead in result.data if lead.get('city') and lead.get('state'))
    print()
    print(f"📊 Address Data: {has_address}/{len(result.data)} have city/state ({has_address/len(result.data)*100:.1f}%)")

if __name__ == '__main__':
    main()
