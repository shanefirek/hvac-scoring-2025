#!/usr/bin/env python3
"""
Identify bad leads from Outscraper CSV by matching against Supabase
Phase 1 of surgical removal plan
"""
import csv
import os
from supabase import create_client, Client

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# CSV file path
OUTSCRAPER_CSV = "/Users/shanefirek/projects/appletree-outbound-2025/appletree-data-pipeline/data/processed/outscraper_valid_deduped.csv"

print("=" * 70)
print("Phase 1: Identify Bad Leads from Outscraper CSV")
print("=" * 70)

# Step 1: Read emails from CSV
print("\n📂 Reading emails from Outscraper CSV...")
outscraper_emails = set()

with open(OUTSCRAPER_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row['email'].strip().lower()
        if email:
            outscraper_emails.add(email)

print(f"✅ Found {len(outscraper_emails)} emails in Outscraper CSV")

# Step 2: Query Supabase for matching leads
print("\n🔍 Querying Supabase for matching leads...")
response = supabase.table("leads").select("id, email, tier, in_smartlead, smartlead_lead_id, smartlead_campaign_ids").execute()
all_leads = response.data

print(f"✅ Found {len(all_leads)} total leads in Supabase")

# Step 3: Match emails
print("\n🎯 Matching emails...")
matched_leads = []
for lead in all_leads:
    lead_email = lead['email'].strip().lower()
    if lead_email in outscraper_emails:
        matched_leads.append(lead)

print(f"✅ Matched {len(matched_leads)} bad leads")

# Step 4: Analyze distribution
print("\n📊 Bad Lead Distribution:")
print("-" * 70)

# By tier
tier_counts = {}
for lead in matched_leads:
    tier = lead.get('tier', 'unknown')
    tier_counts[tier] = tier_counts.get(tier, 0) + 1

print("\nBy Tier:")
for tier, count in sorted(tier_counts.items()):
    print(f"  {tier}: {count} leads")

# By Smartlead sync status
in_smartlead_count = sum(1 for lead in matched_leads if lead.get('in_smartlead'))
has_smartlead_id_count = sum(1 for lead in matched_leads if lead.get('smartlead_lead_id'))

print(f"\nSmartlead Status:")
print(f"  in_smartlead=true: {in_smartlead_count} leads")
print(f"  has smartlead_lead_id: {has_smartlead_id_count} leads")
print(f"  NOT in Smartlead: {len(matched_leads) - in_smartlead_count} leads")

# Step 5: Write output files
print("\n📝 Writing output files...")

# Write matched lead IDs (for SQL updates)
output_ids_file = "/tmp/bad_lead_ids.txt"
with open(output_ids_file, 'w') as f:
    for lead in matched_leads:
        f.write(f"{lead['id']}\n")
print(f"✅ Wrote lead IDs to {output_ids_file}")

# Write matched emails (for reference)
output_emails_file = "/tmp/bad_lead_emails.txt"
with open(output_emails_file, 'w') as f:
    for lead in matched_leads:
        f.write(f"{lead['email']}\n")
print(f"✅ Wrote emails to {output_emails_file}")

# Write full lead details (for Smartlead removal)
output_details_file = "/tmp/bad_lead_details.csv"
with open(output_details_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['id', 'email', 'tier', 'in_smartlead', 'smartlead_lead_id', 'smartlead_campaign_ids']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for lead in matched_leads:
        writer.writerow({
            'id': lead['id'],
            'email': lead['email'],
            'tier': lead.get('tier'),
            'in_smartlead': lead.get('in_smartlead'),
            'smartlead_lead_id': lead.get('smartlead_lead_id'),
            'smartlead_campaign_ids': lead.get('smartlead_campaign_ids')
        })
print(f"✅ Wrote full details to {output_details_file}")

# Step 6: Calculate expected good lead count
good_lead_count = len(all_leads) - len(matched_leads)
print(f"\n🎯 Expected Results:")
print(f"  Total leads in Supabase: {len(all_leads)}")
print(f"  Bad leads to suppress: {len(matched_leads)}")
print(f"  Good leads remaining: {good_lead_count}")

print("\n✅ Identification complete!")
print("\n📋 Next Steps:")
print("  1. Review /tmp/bad_lead_details.csv to verify matches")
print("  2. Run Phase 2: Add suppression columns to Supabase")
print("  3. Run Phase 3: Suppress bad leads in Supabase")
