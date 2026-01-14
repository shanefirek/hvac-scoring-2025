#!/usr/bin/env python3
"""
Clean Outscraper export: 94 columns → 15 essential columns

Keeps only the columns needed for Clay enrichment and Smartlead campaigns.
Filters out invalid emails and normalizes data.
"""

import pandas as pd
from pathlib import Path

# Paths
INPUT_FILE = Path(__file__).parent.parent.parent / "data/outscraper/Outscraper-20251126132711xxl8d_hvac_contractor (1).xlsx"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data/processed/outscraper_cleaned_2000.csv"

# Columns to keep
KEEP_COLUMNS = [
    # Contact info
    'name',
    'email',
    'email.emails_validator.status',
    'first_name',
    'last_name',
    'phone',
    'domain',

    # Scoring signals
    'rating',
    'reviews',
    'company_linkedin',
    'verified',

    # Location
    'city',
    'state',
    'postal_code',

    # Dedupe key
    'place_id',
]

def clean_outscraper_data(
    input_file: Path,
    output_file: Path,
    filter_invalid_emails: bool = False
):
    """
    Clean Outscraper export file

    Args:
        input_file: Path to input XLSX file
        output_file: Path to output CSV file
        filter_invalid_emails: If True, remove rows where email status != 'valid'
    """
    print(f"Reading {input_file}...")
    df = pd.read_excel(input_file)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Keep only essential columns
    print(f"\nKeeping {len(KEEP_COLUMNS)} columns...")
    df_clean = df[KEEP_COLUMNS].copy()

    # Normalize emails to lowercase
    print("Normalizing emails to lowercase...")
    df_clean['email'] = df_clean['email'].str.lower().str.strip()

    # Filter invalid emails if requested
    if filter_invalid_emails:
        before_count = len(df_clean)
        df_clean = df_clean[df_clean['email.emails_validator.status'] == 'valid']
        after_count = len(df_clean)
        print(f"Filtered invalid emails: {before_count} → {after_count} ({before_count - after_count} removed)")

    # Show data quality stats
    print("\n=== Data Quality ===")
    for col in KEEP_COLUMNS:
        filled = df_clean[col].notna().sum()
        pct = (filled / len(df_clean) * 100)
        print(f"{col}: {filled}/{len(df_clean)} ({pct:.1f}%)")

    # Show email validation breakdown
    if 'email.emails_validator.status' in df_clean.columns:
        print("\n=== Email Validation Status ===")
        print(df_clean['email.emails_validator.status'].value_counts())

    # Save cleaned data
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    print(f"\n✅ Saved cleaned data to {output_file}")
    print(f"   {len(df_clean)} rows, {len(df_clean.columns)} columns")

    return df_clean

if __name__ == "__main__":
    import sys

    # Optional: pass --filter-invalid to remove invalid emails
    filter_invalid = '--filter-invalid' in sys.argv

    if filter_invalid:
        print("⚠️  Filtering out invalid emails\n")

    df_clean = clean_outscraper_data(
        INPUT_FILE,
        OUTPUT_FILE,
        filter_invalid_emails=filter_invalid
    )

    print("\n📊 Sample of cleaned data:")
    print(df_clean.head())

    print("\n✅ Done! Ready to import into Clay.")
