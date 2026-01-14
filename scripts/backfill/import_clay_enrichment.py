#!/usr/bin/env python3
"""
Import Clay enrichment results into Supabase.
Matches by email and updates phone_number, city, state where currently NULL.

Usage:
    python scripts/backfill/import_clay_enrichment.py data/clay_export.csv --dry-run
    python scripts/backfill/import_clay_enrichment.py data/clay_export.csv
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find first matching column name (case-insensitive)."""
    df_cols_lower = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in df_cols_lower:
            return df_cols_lower[candidate.lower()]
    return None


def normalize_phone(phone: str | None) -> str | None:
    """Normalize phone to digits only, with +1 prefix for US numbers."""
    if not phone or pd.isna(phone):
        return None

    # Keep only digits and +
    digits = ''.join(c for c in str(phone) if c.isdigit() or c == '+')

    if not digits:
        return None

    # Remove leading + if present
    if digits.startswith('+'):
        digits = digits[1:]

    # Add +1 for 10-digit US numbers
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    elif len(digits) > 10:
        return f"+{digits}"

    return None  # Invalid phone number


def normalize_state(state: str | None) -> str | None:
    """Normalize state to uppercase 2-letter abbreviation."""
    if not state or pd.isna(state):
        return None

    state = str(state).strip().upper()

    # Common state name to abbreviation mapping
    state_map = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
        "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
        "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
        "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
        "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
        "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
        "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
        "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
        "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
        "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI", "WYOMING": "WY", "DISTRICT OF COLUMBIA": "DC"
    }

    if state in state_map:
        return state_map[state]
    elif len(state) == 2:
        return state

    return None


def load_csv(filepath: str) -> pd.DataFrame:
    """Load CSV and identify relevant columns."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} rows from {filepath}")
    print(f"Columns found: {list(df.columns)}")

    # Find email column (required)
    email_col = find_column(df, ["email", "Email", "EMAIL", "e-mail", "E-Mail"])
    if not email_col:
        print("Error: No email column found in CSV")
        sys.exit(1)

    # Find optional columns
    phone_col = find_column(df, ["phone", "Phone", "phone_number", "Phone Number", "phoneNumber", "telephone"])
    city_col = find_column(df, ["city", "City", "CITY"])
    state_col = find_column(df, ["state", "State", "STATE", "region", "Region"])

    print(f"\nColumn mapping:")
    print(f"  Email: {email_col}")
    print(f"  Phone: {phone_col or '(not found)'}")
    print(f"  City: {city_col or '(not found)'}")
    print(f"  State: {state_col or '(not found)'}")

    return df, email_col, phone_col, city_col, state_col


def get_existing_leads() -> dict:
    """Fetch current lead data from Supabase."""
    print("\nFetching existing leads from Supabase...")

    result = supabase.table("leads").select("email, phone_number, city, state").execute()

    # Build lookup by lowercase email
    leads = {}
    for row in result.data:
        email = row["email"].lower() if row["email"] else None
        if email:
            leads[email] = {
                "phone_number": row.get("phone_number"),
                "city": row.get("city"),
                "state": row.get("state")
            }

    print(f"Found {len(leads)} leads in Supabase")
    return leads


def process_updates(df: pd.DataFrame, email_col: str, phone_col: str | None,
                    city_col: str | None, state_col: str | None,
                    existing_leads: dict, dry_run: bool = False) -> dict:
    """Process CSV rows and update Supabase."""

    stats = {
        "total_rows": len(df),
        "matched": 0,
        "not_found": 0,
        "phone_updated": 0,
        "city_updated": 0,
        "state_updated": 0,
        "skipped_has_data": 0,
        "skipped_no_new_data": 0
    }

    updates_to_make = []

    for _, row in df.iterrows():
        email = str(row[email_col]).lower().strip() if pd.notna(row[email_col]) else None

        if not email or email not in existing_leads:
            stats["not_found"] += 1
            continue

        stats["matched"] += 1
        existing = existing_leads[email]

        # Prepare update payload
        update = {}

        # Phone
        if phone_col and pd.notna(row.get(phone_col)):
            new_phone = normalize_phone(row[phone_col])
            if new_phone and not existing["phone_number"]:
                update["phone_number"] = new_phone
                stats["phone_updated"] += 1
            elif existing["phone_number"]:
                stats["skipped_has_data"] += 1

        # City
        if city_col and pd.notna(row.get(city_col)):
            new_city = str(row[city_col]).strip().title()
            if new_city and not existing["city"]:
                update["city"] = new_city
                stats["city_updated"] += 1

        # State
        if state_col and pd.notna(row.get(state_col)):
            new_state = normalize_state(row[state_col])
            if new_state and not existing["state"]:
                update["state"] = new_state
                stats["state_updated"] += 1

        if update:
            updates_to_make.append((email, update))
        else:
            stats["skipped_no_new_data"] += 1

    # Apply updates
    if not dry_run and updates_to_make:
        print(f"\nApplying {len(updates_to_make)} updates to Supabase...")
        for email, update in updates_to_make:
            try:
                supabase.table("leads").update(update).eq("email", email).execute()
            except Exception as e:
                print(f"  Error updating {email}: {e}")
    elif dry_run:
        print(f"\n[DRY RUN] Would apply {len(updates_to_make)} updates")
        if updates_to_make[:5]:
            print("\nSample updates:")
            for email, update in updates_to_make[:5]:
                print(f"  {email}: {update}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Import Clay enrichment into Supabase")
    parser.add_argument("csv_file", help="Path to Clay export CSV")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)

    # Load CSV
    df, email_col, phone_col, city_col, state_col = load_csv(args.csv_file)

    if not phone_col and not city_col and not state_col:
        print("Error: No phone, city, or state columns found in CSV")
        sys.exit(1)

    # Get existing leads
    existing_leads = get_existing_leads()

    # Process updates
    stats = process_updates(df, email_col, phone_col, city_col, state_col,
                           existing_leads, dry_run=args.dry_run)

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total CSV rows:      {stats['total_rows']}")
    print(f"Matched in Supabase: {stats['matched']}")
    print(f"Not found:           {stats['not_found']}")
    print(f"")
    print(f"Phone updated:       {stats['phone_updated']}")
    print(f"City updated:        {stats['city_updated']}")
    print(f"State updated:       {stats['state_updated']}")
    print(f"")
    print(f"Skipped (had data):  {stats['skipped_has_data']}")
    print(f"Skipped (no new):    {stats['skipped_no_new_data']}")

    if args.dry_run:
        print("\n[DRY RUN] No changes were made. Run without --dry-run to apply.")


if __name__ == "__main__":
    main()
