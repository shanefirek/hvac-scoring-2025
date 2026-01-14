#!/usr/bin/env python3
"""Cross-reference Smartlead and Supabase data, generate gap analysis."""

import csv
from datetime import datetime


def load_smartlead():
    """Load Smartlead export."""
    leads = {}
    with open("data/audit/smartlead_full_export.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").lower().strip()
            if email:
                if email not in leads:
                    leads[email] = []
                leads[email].append(row)
    return leads


def load_supabase():
    """Load Supabase export."""
    leads = {}
    with open("data/audit/supabase_full_export.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").lower().strip()
            if email:
                leads[email] = row
    return leads


def analyze():
    print("Loading exports...")
    smartlead = load_smartlead()
    supabase = load_supabase()

    print(f"Smartlead unique emails: {len(smartlead)}")
    print(f"Supabase unique emails: {len(supabase)}")

    sl_emails = set(smartlead.keys())
    sb_emails = set(supabase.keys())

    # Gap analysis
    in_both = sl_emails & sb_emails
    only_smartlead = sl_emails - sb_emails
    only_supabase = sb_emails - sl_emails

    print(f"\nOverlap Analysis:")
    print(f"  In both: {len(in_both)}")
    print(f"  Only in Smartlead: {len(only_smartlead)}")
    print(f"  Only in Supabase: {len(only_supabase)}")

    # Analyze leads in both systems
    engaged_no_phone = []
    engaged_no_state = []
    mismatched_tier = []
    bounced = []
    unsubscribed = []

    for email in in_both:
        sl = smartlead[email][0]  # Take first if duplicated
        sb = supabase[email]

        is_engaged = sb.get("has_opens") == "✓" or sb.get("has_clicks") == "✓"
        has_phone = sb.get("has_phone") == "✓"
        has_state = sb.get("has_state") == "✓"
        is_bounced = sb.get("is_bounced") == "✓"

        if is_engaged and not has_phone:
            engaged_no_phone.append({
                "email": email,
                "company": sb.get("company"),
                "tier": sb.get("tier"),
                "has_opens": sb.get("has_opens"),
                "has_clicks": sb.get("has_clicks"),
                "smartlead_status": sl.get("status"),
            })

        if is_engaged and not has_state:
            engaged_no_state.append(email)

        if is_bounced:
            bounced.append({
                "email": email,
                "company": sb.get("company"),
                "tier": sb.get("tier"),
            })

        if sl.get("is_unsubscribed") == "True":
            unsubscribed.append({
                "email": email,
                "company": sb.get("company"),
            })

    # Leads only in Smartlead (not in Supabase)
    smartlead_orphans = []
    for email in only_smartlead:
        sl = smartlead[email][0]
        smartlead_orphans.append({
            "email": email,
            "first_name": sl.get("first_name"),
            "last_name": sl.get("last_name"),
            "company": sl.get("company"),
            "campaign": sl.get("campaign_name"),
            "status": sl.get("status"),
        })

    # Generate report
    report = f"""# Appletree Lead Data Audit Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview

| Metric | Count |
|--------|-------|
| Smartlead unique emails | {len(smartlead)} |
| Supabase unique emails | {len(supabase)} |
| In both systems | {len(in_both)} |
| Only in Smartlead | {len(only_smartlead)} |
| Only in Supabase | {len(only_supabase)} |

## Data Quality Issues

### Priority Re-Enrichment (Engaged but Missing Phone): {len(engaged_no_phone)}
These leads have opened/clicked emails but we don't have their phone number.

| Email | Company | Tier | Opens | Clicks |
|-------|---------|------|-------|--------|
"""
    for lead in engaged_no_phone[:50]:  # Top 50
        report += f"| {lead['email']} | {lead['company']} | {lead['tier']} | {lead['has_opens']} | {lead['has_clicks']} |\n"

    if len(engaged_no_phone) > 50:
        report += f"\n*...and {len(engaged_no_phone) - 50} more*\n"

    report += f"""

### Bounced Leads (Archive Candidates): {len(bounced)}
"""
    for lead in bounced[:20]:
        report += f"- {lead['email']} ({lead['company']}) - {lead['tier']}\n"

    report += f"""

### Unsubscribed Leads: {len(unsubscribed)}
"""
    for lead in unsubscribed[:20]:
        report += f"- {lead['email']} ({lead['company']})\n"

    report += f"""

### Orphaned Leads (In Smartlead, Not in Supabase): {len(smartlead_orphans)}
These leads exist in Smartlead campaigns but have no matching record in Supabase.

| Email | Name | Company | Campaign | Status |
|-------|------|---------|----------|--------|
"""
    for lead in smartlead_orphans[:30]:
        name = f"{lead['first_name']} {lead['last_name']}".strip()
        report += f"| {lead['email']} | {name} | {lead['company']} | {lead['campaign']} | {lead['status']} |\n"

    if len(smartlead_orphans) > 30:
        report += f"\n*...and {len(smartlead_orphans) - 30} more*\n"

    report += f"""

## Recommendations

1. **Re-enrich {len(engaged_no_phone)} engaged leads** - These have shown interest, worth getting phone numbers
2. **Archive {len(bounced)} bounced leads** - Move to leads_archived table
3. **Archive {len(unsubscribed)} unsubscribed leads** - Move to leads_archived table
4. **Investigate {len(smartlead_orphans)} orphaned leads** - Sync from Smartlead to Supabase or cleanup

## Files Generated
- `data/audit/smartlead_full_export.csv` - All Smartlead leads
- `data/audit/supabase_full_export.csv` - All Supabase leads with quality flags
- `data/audit/priority_reenrich.csv` - Leads needing phone numbers (engaged)
- `data/audit/gap_analysis_report.md` - This report
"""

    # Write report
    with open("data/audit/gap_analysis_report.md", "w") as f:
        f.write(report)

    # Export priority re-enrichment list
    with open("data/audit/priority_reenrich.csv", "w", newline="") as f:
        if engaged_no_phone:
            writer = csv.DictWriter(f, fieldnames=engaged_no_phone[0].keys())
            writer.writeheader()
            writer.writerows(engaged_no_phone)

    # Export orphaned leads
    with open("data/audit/smartlead_orphans.csv", "w", newline="") as f:
        if smartlead_orphans:
            writer = csv.DictWriter(f, fieldnames=smartlead_orphans[0].keys())
            writer.writeheader()
            writer.writerows(smartlead_orphans)

    # Export bounced for archival
    with open("data/audit/bounced_leads.csv", "w", newline="") as f:
        if bounced:
            writer = csv.DictWriter(f, fieldnames=bounced[0].keys())
            writer.writeheader()
            writer.writerows(bounced)

    print(f"\n{'='*50}")
    print("Gap Analysis Complete!")
    print(f"\nKey Findings:")
    print(f"  Priority re-enrich: {len(engaged_no_phone)} leads")
    print(f"  Bounced (archive): {len(bounced)} leads")
    print(f"  Unsubscribed (archive): {len(unsubscribed)} leads")
    print(f"  Orphaned in Smartlead: {len(smartlead_orphans)} leads")
    print(f"\nFiles generated:")
    print(f"  data/audit/gap_analysis_report.md")
    print(f"  data/audit/priority_reenrich.csv")
    print(f"  data/audit/smartlead_orphans.csv")
    print(f"  data/audit/bounced_leads.csv")


if __name__ == "__main__":
    analyze()
