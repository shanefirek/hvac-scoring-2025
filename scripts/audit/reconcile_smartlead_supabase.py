#!/usr/bin/env python3
"""
Reconciliation script to compare Smartlead leads vs Supabase leads.
Generates a comprehensive report of differences, gaps, and duplicates.
"""

import csv
import json
import os
from collections import defaultdict
from supabase import create_client

# Initialize Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Loading Smartlead data from CSV...")
smartlead_by_email = defaultdict(list)
campaigns = {}

with open('data/audit/smartlead_full_export.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row['email'].lower().strip()
        campaign_id = row['campaign_id']

        # Track campaigns
        if campaign_id not in campaigns:
            campaigns[campaign_id] = {
                'name': row['campaign_name'],
                'tier': row['campaign_tier']
            }

        smartlead_by_email[email].append({
            'campaign_id': campaign_id,
            'campaign_name': row['campaign_name'],
            'campaign_tier': row['campaign_tier'],
            'smartlead_lead_id': row['smartlead_lead_id'],
            'status': row['status'],
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'company': row['company'],
            'phone_number': row['phone_number'],
            'city': row['city'],
            'state': row['state']
        })

print(f"Loaded {len(smartlead_by_email)} unique emails from Smartlead")

print("\nLoading Supabase data...")
response = supabase.table('leads').select(
    'id, email, tier, smartlead_lead_id, in_smartlead, first_name, last_name, company, created_at'
).execute()

supabase_leads = {lead['email'].lower().strip(): lead for lead in response.data}
print(f"Loaded {len(supabase_leads)} leads from Supabase")

# Analysis
in_both = set(smartlead_by_email.keys()) & set(supabase_leads.keys())
smartlead_only = set(smartlead_by_email.keys()) - set(supabase_leads.keys())
supabase_only = set(supabase_leads.keys()) - set(smartlead_by_email.keys())

# Duplicates in Smartlead (same email in multiple campaigns)
duplicates = {email: records for email, records in smartlead_by_email.items() if len(records) > 1}

# Tier mismatches
tier_mismatches = []
for email in in_both:
    sb_lead = supabase_leads[email]
    sl_records = smartlead_by_email[email]

    # Compare tier from first campaign
    sb_tier = sb_lead['tier']
    sl_tier = sl_records[0]['campaign_tier']

    if sb_tier != sl_tier:
        tier_mismatches.append({
            'email': email,
            'supabase_tier': sb_tier,
            'smartlead_tier': sl_tier,
            'company': sb_lead['company']
        })

# Missing smartlead_lead_id linkage
missing_linkage = []
for email in in_both:
    sb_lead = supabase_leads[email]
    if not sb_lead['smartlead_lead_id']:
        missing_linkage.append({
            'email': email,
            'company': sb_lead['company'],
            'smartlead_ids': [r['smartlead_lead_id'] for r in smartlead_by_email[email]]
        })

# Generate report
report = []
report.append("# Smartlead ↔ Supabase Reconciliation Report")
report.append(f"\n**Generated:** {os.popen('date').read().strip()}")
report.append(f"\n**Smartlead Export:** data/audit/smartlead_full_export.csv (Dec 19, 2025)")
report.append(f"\n**Supabase Query:** Live query from production database")
report.append("\n---\n")

# Summary Stats
report.append("## Summary Statistics\n")
report.append("| Metric | Count | Notes |")
report.append("|--------|-------|-------|")
report.append(f"| **Total Smartlead records** | {sum(len(v) for v in smartlead_by_email.values())} | Including duplicates |")
report.append(f"| **Unique Smartlead emails** | {len(smartlead_by_email)} | Deduplicated |")
report.append(f"| **Supabase leads** | {len(supabase_leads)} | Source of truth |")
report.append(f"| **In BOTH systems** | {len(in_both)} | {len(in_both)/len(supabase_leads)*100:.1f}% of Supabase |")
report.append(f"| **Smartlead ONLY** | {len(smartlead_only)} | Orphaned campaigns |")
report.append(f"| **Supabase ONLY** | {len(supabase_only)} | Not synced yet |")
report.append(f"| **Duplicates** | {len(duplicates)} | Same email in multiple campaigns |")
report.append(f"| **Tier mismatches** | {len(tier_mismatches)} | Different tier in Supabase vs Smartlead |")
report.append(f"| **Missing linkage** | {len(missing_linkage)} | In both but smartlead_lead_id is NULL |")
report.append("")

# Campaigns
report.append("## Smartlead Campaigns\n")
report.append("| Campaign ID | Name | Tier | Lead Count |")
report.append("|-------------|------|------|------------|")
campaign_counts = defaultdict(int)
for records in smartlead_by_email.values():
    for record in records:
        campaign_counts[record['campaign_id']] += 1

for cid, info in campaigns.items():
    report.append(f"| {cid} | {info['name']} | {info['tier']} | {campaign_counts[cid]} |")
report.append("")

# Duplicates
if duplicates:
    report.append(f"## Duplicates in Smartlead ({len(duplicates)} emails)\n")
    report.append("These emails appear in multiple campaigns:\n")
    report.append("| Email | Company | Campaigns | Lead IDs |")
    report.append("|-------|---------|-----------|----------|")

    for email, records in sorted(duplicates.items())[:50]:  # Limit to first 50
        campaigns_str = ", ".join([f"{r['campaign_name']}" for r in records])
        lead_ids_str = ", ".join([r['smartlead_lead_id'] for r in records])
        company = records[0]['company']
        report.append(f"| {email} | {company} | {campaigns_str} | {lead_ids_str} |")

    if len(duplicates) > 50:
        report.append(f"\n*Showing first 50 of {len(duplicates)} duplicates*")
    report.append("")

# Smartlead Only
if smartlead_only:
    report.append(f"## Leads in Smartlead ONLY ({len(smartlead_only)} orphans)\n")
    report.append("These leads exist in Smartlead campaigns but NOT in Supabase:\n")
    report.append("| Email | Company | Campaign | Smartlead ID | Status |")
    report.append("|-------|---------|----------|--------------|--------|")

    for email in sorted(smartlead_only)[:100]:  # Limit to first 100
        records = smartlead_by_email[email]
        for record in records:
            company = record['company'] or '(none)'
            report.append(f"| {email} | {company} | {record['campaign_name']} | {record['smartlead_lead_id']} | {record['status']} |")

    if len(smartlead_only) > 100:
        report.append(f"\n*Showing first 100 of {len(smartlead_only)} orphaned leads*")
    report.append("")

# Supabase Only
if supabase_only:
    report.append(f"## Leads in Supabase ONLY ({len(supabase_only)} not synced)\n")
    report.append("These leads exist in Supabase but NOT in any Smartlead campaign:\n")
    report.append("| Email | Company | Tier | In Smartlead Flag | Created At |")
    report.append("|-------|---------|------|-------------------|------------|")

    for email in sorted(supabase_only)[:100]:  # Limit to first 100
        lead = supabase_leads[email]
        company = lead['company'] or '(none)'
        created = lead['created_at'][:10] if lead['created_at'] else 'N/A'
        report.append(f"| {email} | {company} | {lead['tier']} | {lead['in_smartlead']} | {created} |")

    if len(supabase_only) > 100:
        report.append(f"\n*Showing first 100 of {len(supabase_only)} unsynced leads*")
    report.append("")

# Tier Mismatches
if tier_mismatches:
    report.append(f"## Tier Mismatches ({len(tier_mismatches)})\n")
    report.append("Leads where Supabase tier differs from Smartlead campaign tier:\n")
    report.append("| Email | Company | Supabase Tier | Smartlead Tier |")
    report.append("|-------|---------|---------------|----------------|")

    for mismatch in tier_mismatches[:50]:
        report.append(f"| {mismatch['email']} | {mismatch['company']} | {mismatch['supabase_tier']} | {mismatch['smartlead_tier']} |")

    if len(tier_mismatches) > 50:
        report.append(f"\n*Showing first 50 of {len(tier_mismatches)} mismatches*")
    report.append("")

# Missing Linkage
if missing_linkage:
    report.append(f"## Missing smartlead_lead_id Linkage ({len(missing_linkage)})\n")
    report.append("Leads in both systems but smartlead_lead_id is NULL in Supabase:\n")
    report.append("| Email | Company | Smartlead Lead IDs |")
    report.append("|-------|---------|-------------------|")

    for lead in missing_linkage[:50]:
        ids_str = ", ".join(lead['smartlead_ids'])
        report.append(f"| {lead['email']} | {lead['company']} | {ids_str} |")

    if len(missing_linkage) > 50:
        report.append(f"\n*Showing first 50 of {len(missing_linkage)} missing linkages*")
    report.append("")

# Recommendations
report.append("## Recommendations\n")
report.append("### High Priority\n")

if smartlead_only:
    report.append(f"1. **{len(smartlead_only)} orphaned leads in Smartlead** - These should either be:")
    report.append("   - Added to Supabase if they're legitimate leads")
    report.append("   - Removed from Smartlead if they're duplicates/junk")
    report.append("")

if supabase_only:
    report.append(f"2. **{len(supabase_only)} leads in Supabase not in Smartlead** - These should be:")
    report.append("   - Added to appropriate campaigns if ready")
    report.append("   - Marked with `in_smartlead = false` to track sync status")
    report.append("")

if missing_linkage:
    report.append(f"3. **{len(missing_linkage)} leads missing smartlead_lead_id** - Run backfill script:")
    report.append("   ```bash")
    report.append("   python scripts/smartlead/sync_smartlead_to_supabase.py")
    report.append("   ```")
    report.append("")

if duplicates:
    report.append(f"4. **{len(duplicates)} duplicate emails across campaigns** - Review for:")
    report.append("   - A/B test leads (expected)")
    report.append("   - Accidental duplicates (should consolidate)")
    report.append("")

if tier_mismatches:
    report.append(f"5. **{len(tier_mismatches)} tier mismatches** - Decide which is source of truth:")
    report.append("   - Supabase tier is based on scoring logic")
    report.append("   - Smartlead tier is what campaign they're in")
    report.append("   - May indicate leads moved tiers but weren't migrated")
    report.append("")

report.append("### Data Quality\n")
report.append("- **Coverage:** {:.1f}% of Supabase leads are in Smartlead".format(len(in_both)/len(supabase_leads)*100))
report.append("- **Linkage:** {:.1f}% have smartlead_lead_id populated".format((len(in_both)-len(missing_linkage))/len(supabase_leads)*100))
report.append("")

# Write report
output_path = 'data/audit/reconciliation_report.md'
with open(output_path, 'w') as f:
    f.write('\n'.join(report))

print(f"\n✅ Report written to: {output_path}")
print(f"\nKey findings:")
print(f"  - {len(in_both)} leads in both systems ({len(in_both)/len(supabase_leads)*100:.1f}%)")
print(f"  - {len(smartlead_only)} orphaned in Smartlead")
print(f"  - {len(supabase_only)} not yet in Smartlead")
print(f"  - {len(duplicates)} duplicate emails")
print(f"  - {len(tier_mismatches)} tier mismatches")
print(f"  - {len(missing_linkage)} missing smartlead_lead_id")
