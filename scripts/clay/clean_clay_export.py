#!/usr/bin/env python3
"""
Clean Clay HVAC export for Smartlead import

Transforms Clay export CSV into 3 clean CSVs (A/B/C tiers) ready for Smartlead.

Usage:
    python clean_clay_export.py
"""

import csv
import os

# Input/output files
INPUT_FILE = "data/raw/Clay_HVAC_export_11132025.csv"
OUTPUT_DIR = "data/processed"

# Tier thresholds based on scoring logic
def calculate_tier(score):
    """Calculate tier from score (20-30=A, 10-19=B, 0-9=C)"""
    try:
        score_int = int(score) if score else 0
    except (ValueError, TypeError):
        score_int = 0

    if score_int >= 20:
        return "A"
    elif score_int >= 10:
        return "B"
    else:
        return "C"

def extract_last_name(full_name):
    """Extract last name from full name"""
    if not full_name:
        return ""

    parts = full_name.strip().split()
    if len(parts) > 1:
        return parts[-1]  # Last word is last name
    return ""

def normalize_company_name(name):
    """Clean up company name - remove LLC, Inc, extra slashes"""
    if not name:
        return ""

    # Remove common suffixes
    suffixes = [', LLC', ' LLC', ', Inc', ' Inc', ', Inc.', ' Inc.',
                ', Corp', ' Corp', ', Corporation', ' Corporation']
    for suffix in suffixes:
        name = name.replace(suffix, '')

    # Remove everything after slash or parenthesis
    name = name.split('/')[0].strip()
    name = name.split('(')[0].strip()

    # Remove (fka ...) patterns
    if '(fka' in name.lower():
        name = name.split('(')[0].strip()

    return name.strip()

def clean_csv():
    """Clean and split Clay export into tier-specific CSVs"""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read input CSV
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Storage for each tier
        leads_by_tier = {"A": [], "B": [], "C": []}

        for row in reader:
            # Skip if email not verified
            verified = row.get('Verified (2)', '').strip().lower()
            if verified != 'true':
                continue

            # Extract fields
            company = normalize_company_name(row.get('Company', '').strip())
            first_name = row.get('Normalized First Name', '').strip()
            full_name = row.get('Normalized Name', '').strip()
            email = row.get('Final Email', '').strip()
            reviews_count = row.get('Reviews Count', '0').strip()
            service_software = row.get('Field Service Tech', '').strip()
            score = row.get('Score', '0').strip()

            # Skip if missing critical fields
            if not email or not company or not first_name:
                continue

            # Extract last name
            last_name = extract_last_name(full_name)

            # Calculate tier
            tier = calculate_tier(score)

            # Clean service software value (remove empty strings)
            if not service_software or service_software.lower() == 'none':
                service_software = ''

            # Clean reviews count
            try:
                reviews_count = int(reviews_count) if reviews_count else 0
            except ValueError:
                reviews_count = 0

            # Create cleaned lead record
            lead = {
                'email': email.lower(),  # Lowercase for consistency
                'first_name': first_name,
                'last_name': last_name,
                'company': company,
                'tier': tier,
                'service_software': service_software,
                'review_count': reviews_count
            }

            # Add to appropriate tier
            leads_by_tier[tier].append(lead)

    # Write output CSVs for each tier
    for tier, leads in leads_by_tier.items():
        output_file = os.path.join(OUTPUT_DIR, f"leads_{tier.lower()}_tier.csv")

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['email', 'first_name', 'last_name', 'company', 'tier', 'service_software', 'review_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(leads)

        print(f"✅ {tier}-Tier: {len(leads)} leads → {output_file}")

    # Summary
    total_leads = sum(len(leads) for leads in leads_by_tier.values())
    print(f"\n📊 Total: {total_leads} verified leads")
    print(f"   A-Tier (20-30 pts): {len(leads_by_tier['A'])} leads")
    print(f"   B-Tier (10-19 pts): {len(leads_by_tier['B'])} leads")
    print(f"   C-Tier (0-9 pts): {len(leads_by_tier['C'])} leads")

    return leads_by_tier

if __name__ == "__main__":
    print("🧹 Cleaning Clay export for Smartlead...")
    print(f"📄 Input: {INPUT_FILE}\n")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found")
        print("   Place the Clay export CSV in this directory first.")
        exit(1)

    leads = clean_csv()
    print("\n✅ Done! Import CSVs are ready in ./data/processed/")
