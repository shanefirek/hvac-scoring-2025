#!/usr/bin/env python3
"""
Supabase Data Quality Audit Script
Checks for discrepancies and data quality issues in the leads table.
"""

import os
import sys
import json
import csv
from datetime import datetime
from collections import defaultdict
import re
import requests

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Valid campaign IDs
VALID_CAMPAIGN_IDS = [2677089, 2677090, 2677091]

class SupabaseAuditor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")

        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }

        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def fetch_all_leads(self):
        """Fetch all leads from Supabase"""
        print(f"{BLUE}Fetching all leads from Supabase...{RESET}")

        url = f"{self.supabase_url}/rest/v1/leads?select=*"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch leads: {response.status_code} - {response.text}")

        leads = response.json()
        print(f"{GREEN}✅ Fetched {len(leads)} leads{RESET}\n")
        return leads

    def check_duplicate_emails(self, leads):
        """Check for duplicate emails (should be none due to unique constraint)"""
        print(f"{BOLD}1. Checking for duplicate emails...{RESET}")

        email_counts = defaultdict(int)
        for lead in leads:
            if lead.get('email'):
                email_counts[lead['email']] += 1

        duplicates = {email: count for email, count in email_counts.items() if count > 1}

        if duplicates:
            print(f"{RED}❌ Found {len(duplicates)} duplicate emails:{RESET}")
            for email, count in duplicates.items():
                print(f"   {email}: {count} occurrences")
                self.issues['duplicate_emails'].append({'email': email, 'count': count})
            self.stats['duplicate_emails'] = len(duplicates)
        else:
            print(f"{GREEN}✅ No duplicate emails found{RESET}")
            self.stats['duplicate_emails'] = 0
        print()

    def check_missing_required_fields(self, leads):
        """Check for missing required fields"""
        print(f"{BOLD}2. Checking for missing required fields...{RESET}")

        missing_email = [lead for lead in leads if not lead.get('email')]

        if missing_email:
            print(f"{RED}❌ Found {len(missing_email)} leads with missing email:{RESET}")
            for lead in missing_email:
                print(f"   ID: {lead.get('id')}, Company: {lead.get('company_name')}")
                self.issues['missing_email'].append(lead)
            self.stats['missing_email'] = len(missing_email)
        else:
            print(f"{GREEN}✅ All leads have email addresses{RESET}")
            self.stats['missing_email'] = 0
        print()

    def check_inconsistent_names(self, leads):
        """Check for inconsistent name data"""
        print(f"{BOLD}3. Checking for inconsistent name data...{RESET}")

        has_first_no_last = []
        has_last_no_first = []

        for lead in leads:
            first = lead.get('first_name')
            last = lead.get('last_name')

            if first and not last:
                has_first_no_last.append(lead)
            elif last and not first:
                has_last_no_first.append(lead)

        if has_first_no_last:
            print(f"{YELLOW}⚠️  Found {len(has_first_no_last)} leads with first_name but no last_name{RESET}")
            self.stats['first_no_last'] = len(has_first_no_last)
            self.issues['first_no_last'] = has_first_no_last

        if has_last_no_first:
            print(f"{YELLOW}⚠️  Found {len(has_last_no_first)} leads with last_name but no first_name{RESET}")
            self.stats['last_no_first'] = len(has_last_no_first)
            self.issues['last_no_first'] = has_last_no_first

        if not has_first_no_last and not has_last_no_first:
            print(f"{GREEN}✅ All leads with names have both first and last{RESET}")
        print()

    def check_invalid_company_names(self, leads):
        """Check for invalid company names"""
        print(f"{BOLD}4. Checking for invalid company names...{RESET}")

        invalid_companies = []

        for lead in leads:
            company = lead.get('company_name', '').strip()

            if not company:
                invalid_companies.append({'lead': lead, 'issue': 'empty'})
            elif len(company) == 1:
                invalid_companies.append({'lead': lead, 'issue': 'single_char'})
            elif company.lower() in ['test', 'n/a', 'na', 'none', 'unknown']:
                invalid_companies.append({'lead': lead, 'issue': 'placeholder'})

        if invalid_companies:
            print(f"{YELLOW}⚠️  Found {len(invalid_companies)} leads with invalid company names:{RESET}")
            for item in invalid_companies[:10]:  # Show first 10
                print(f"   {item['issue']}: {item['lead'].get('email')} - '{item['lead'].get('company_name')}'")
            if len(invalid_companies) > 10:
                print(f"   ... and {len(invalid_companies) - 10} more")
            self.stats['invalid_companies'] = len(invalid_companies)
            self.issues['invalid_companies'] = invalid_companies
        else:
            print(f"{GREEN}✅ All company names are valid{RESET}")
            self.stats['invalid_companies'] = 0
        print()

    def check_smartlead_tracking(self, leads):
        """Check for Smartlead tracking issues"""
        print(f"{BOLD}5. Checking Smartlead tracking consistency...{RESET}")

        # in_smartlead=true but empty campaign_ids array
        has_flag_no_campaigns = []
        # has campaign IDs but in_smartlead=false
        has_campaigns_no_flag = []
        # invalid campaign IDs
        invalid_campaign_ids = []

        for lead in leads:
            in_smartlead = lead.get('in_smartlead', False)
            campaign_ids = lead.get('smartlead_campaign_ids', [])

            # Handle null/None campaign_ids
            if campaign_ids is None:
                campaign_ids = []

            if in_smartlead and not campaign_ids:
                has_flag_no_campaigns.append(lead)

            if campaign_ids and not in_smartlead:
                has_campaigns_no_flag.append(lead)

            # Check for invalid campaign IDs
            if campaign_ids:
                invalid_ids = [cid for cid in campaign_ids if cid not in VALID_CAMPAIGN_IDS]
                if invalid_ids:
                    invalid_campaign_ids.append({
                        'lead': lead,
                        'invalid_ids': invalid_ids
                    })

        if has_flag_no_campaigns:
            print(f"{RED}❌ Found {len(has_flag_no_campaigns)} leads with in_smartlead=true but empty campaign_ids{RESET}")
            self.stats['flag_no_campaigns'] = len(has_flag_no_campaigns)
            self.issues['flag_no_campaigns'] = has_flag_no_campaigns

        if has_campaigns_no_flag:
            print(f"{RED}❌ Found {len(has_campaigns_no_flag)} leads with campaign_ids but in_smartlead=false{RESET}")
            self.stats['campaigns_no_flag'] = len(has_campaigns_no_flag)
            self.issues['campaigns_no_flag'] = has_campaigns_no_flag

        if invalid_campaign_ids:
            print(f"{RED}❌ Found {len(invalid_campaign_ids)} leads with invalid campaign IDs:{RESET}")
            for item in invalid_campaign_ids[:5]:
                print(f"   {item['lead'].get('email')}: {item['invalid_ids']}")
            if len(invalid_campaign_ids) > 5:
                print(f"   ... and {len(invalid_campaign_ids) - 5} more")
            self.stats['invalid_campaign_ids'] = len(invalid_campaign_ids)
            self.issues['invalid_campaign_ids'] = invalid_campaign_ids

        if not has_flag_no_campaigns and not has_campaigns_no_flag and not invalid_campaign_ids:
            print(f"{GREEN}✅ All Smartlead tracking is consistent{RESET}")
        print()

    def check_email_format(self, leads):
        """Check for invalid email formats"""
        print(f"{BOLD}6. Checking email format validation...{RESET}")

        invalid_emails = []
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        for lead in leads:
            email = lead.get('email', '')
            if email and not re.match(email_regex, email):
                invalid_emails.append(lead)

        if invalid_emails:
            print(f"{RED}❌ Found {len(invalid_emails)} leads with invalid email format:{RESET}")
            for lead in invalid_emails[:10]:
                print(f"   {lead.get('email')}")
            if len(invalid_emails) > 10:
                print(f"   ... and {len(invalid_emails) - 10} more")
            self.stats['invalid_emails'] = len(invalid_emails)
            self.issues['invalid_emails'] = invalid_emails
        else:
            print(f"{GREEN}✅ All emails have valid format{RESET}")
            self.stats['invalid_emails'] = 0
        print()

    def check_data_completeness(self, leads):
        """Check data completeness"""
        print(f"{BOLD}7. Checking data completeness...{RESET}")

        fields_to_check = ['first_name', 'last_name', 'company_name', 'phone_number',
                          'location', 'linkedin_url', 'website']

        completeness = {
            'all_fields': 0,
            'missing_name': 0,
            'missing_company': 0,
            'missing_phone': 0,
            'missing_location': 0,
            'missing_linkedin': 0,
            'missing_website': 0,
        }

        for lead in leads:
            has_all = all(lead.get(field) for field in fields_to_check)

            if has_all:
                completeness['all_fields'] += 1

            if not lead.get('first_name') or not lead.get('last_name'):
                completeness['missing_name'] += 1
            if not lead.get('company_name'):
                completeness['missing_company'] += 1
            if not lead.get('phone_number'):
                completeness['missing_phone'] += 1
            if not lead.get('location'):
                completeness['missing_location'] += 1
            if not lead.get('linkedin_url'):
                completeness['missing_linkedin'] += 1
            if not lead.get('website'):
                completeness['missing_website'] += 1

        total = len(leads)
        print(f"   All fields populated: {completeness['all_fields']} ({completeness['all_fields']/total*100:.1f}%)")
        print(f"   Missing name: {completeness['missing_name']} ({completeness['missing_name']/total*100:.1f}%)")
        print(f"   Missing company: {completeness['missing_company']} ({completeness['missing_company']/total*100:.1f}%)")
        print(f"   Missing phone: {completeness['missing_phone']} ({completeness['missing_phone']/total*100:.1f}%)")
        print(f"   Missing location: {completeness['missing_location']} ({completeness['missing_location']/total*100:.1f}%)")
        print(f"   Missing LinkedIn: {completeness['missing_linkedin']} ({completeness['missing_linkedin']/total*100:.1f}%)")
        print(f"   Missing website: {completeness['missing_website']} ({completeness['missing_website']/total*100:.1f}%)")

        self.stats['completeness'] = completeness
        print()

    def check_field_consistency(self, leads):
        """Check field consistency (LinkedIn URLs, websites, phone numbers)"""
        print(f"{BOLD}8. Checking field consistency...{RESET}")

        invalid_linkedin = []
        invalid_website = []

        for lead in leads:
            linkedin = lead.get('linkedin_url', '')
            website = lead.get('website', '')

            if linkedin and 'linkedin.com' not in linkedin.lower():
                invalid_linkedin.append(lead)

            if website and not ('.' in website and len(website) > 3):
                invalid_website.append(lead)

        if invalid_linkedin:
            print(f"{YELLOW}⚠️  Found {len(invalid_linkedin)} leads with invalid LinkedIn URLs{RESET}")
            self.stats['invalid_linkedin'] = len(invalid_linkedin)
            self.issues['invalid_linkedin'] = invalid_linkedin
        else:
            print(f"{GREEN}✅ All LinkedIn URLs are valid{RESET}")

        if invalid_website:
            print(f"{YELLOW}⚠️  Found {len(invalid_website)} leads with invalid website URLs{RESET}")
            self.stats['invalid_website'] = len(invalid_website)
            self.issues['invalid_website'] = invalid_website
        else:
            print(f"{GREEN}✅ All website URLs are valid{RESET}")
        print()

    def generate_statistics(self, leads):
        """Generate overall statistics"""
        print(f"{BOLD}9. Overall Statistics{RESET}")

        total_leads = len(leads)
        in_smartlead = len([l for l in leads if l.get('in_smartlead')])
        not_in_smartlead = total_leads - in_smartlead

        # Campaign distribution
        campaign_dist = defaultdict(int)
        for lead in leads:
            campaign_ids = lead.get('smartlead_campaign_ids', [])
            if campaign_ids:
                for cid in campaign_ids:
                    campaign_dist[cid] += 1

        print(f"   Total leads: {total_leads}")
        print(f"   In Smartlead: {in_smartlead} ({in_smartlead/total_leads*100:.1f}%)")
        print(f"   Not in Smartlead: {not_in_smartlead} ({not_in_smartlead/total_leads*100:.1f}%)")
        print(f"\n   Campaign distribution:")
        print(f"     Campaign 2677089 (A-Tier): {campaign_dist.get(2677089, 0)} leads")
        print(f"     Campaign 2677090 (B-Tier): {campaign_dist.get(2677090, 0)} leads")
        print(f"     Campaign 2677091 (C-Tier): {campaign_dist.get(2677091, 0)} leads")

        self.stats['total_leads'] = total_leads
        self.stats['in_smartlead'] = in_smartlead
        self.stats['not_in_smartlead'] = not_in_smartlead
        self.stats['campaign_distribution'] = dict(campaign_dist)
        print()

    def save_report(self):
        """Save detailed findings to CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"/Users/shanefirek/projects/appletree-outbound-2025/appletree-data-pipeline/data/supabase_audit_report_{timestamp}.csv"

        print(f"{BLUE}Saving detailed report to {report_path}...{RESET}")

        # Flatten issues for CSV
        rows = []
        for issue_type, items in self.issues.items():
            for item in items:
                if isinstance(item, dict) and 'lead' in item:
                    lead = item['lead']
                    rows.append({
                        'issue_type': issue_type,
                        'email': lead.get('email'),
                        'company': lead.get('company_name'),
                        'first_name': lead.get('first_name'),
                        'last_name': lead.get('last_name'),
                        'in_smartlead': lead.get('in_smartlead'),
                        'campaign_ids': lead.get('smartlead_campaign_ids'),
                        'details': item.get('issue', item.get('invalid_ids', ''))
                    })
                elif isinstance(item, dict):
                    rows.append({
                        'issue_type': issue_type,
                        'email': item.get('email'),
                        'details': item.get('count', '')
                    })
                else:
                    rows.append({
                        'issue_type': issue_type,
                        'email': item.get('email'),
                        'company': item.get('company_name'),
                        'first_name': item.get('first_name'),
                        'last_name': item.get('last_name'),
                        'in_smartlead': item.get('in_smartlead'),
                        'campaign_ids': item.get('smartlead_campaign_ids'),
                    })

        if rows:
            with open(report_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['issue_type', 'email', 'company',
                                                       'first_name', 'last_name', 'in_smartlead',
                                                       'campaign_ids', 'details'])
                writer.writeheader()
                writer.writerows(rows)
            print(f"{GREEN}✅ Report saved: {len(rows)} issues documented{RESET}\n")
        else:
            print(f"{GREEN}✅ No issues to report!{RESET}\n")

        return report_path if rows else None

    def print_summary(self):
        """Print summary of critical issues"""
        print(f"{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}AUDIT SUMMARY{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        critical_issues = []
        warnings = []

        if self.stats.get('duplicate_emails', 0) > 0:
            critical_issues.append(f"❌ {self.stats['duplicate_emails']} duplicate emails (database constraint violated)")

        if self.stats.get('missing_email', 0) > 0:
            critical_issues.append(f"❌ {self.stats['missing_email']} leads missing email addresses")

        if self.stats.get('flag_no_campaigns', 0) > 0:
            critical_issues.append(f"❌ {self.stats['flag_no_campaigns']} leads marked in_smartlead but no campaign IDs")

        if self.stats.get('campaigns_no_flag', 0) > 0:
            critical_issues.append(f"❌ {self.stats['campaigns_no_flag']} leads with campaign IDs but in_smartlead=false")

        if self.stats.get('invalid_campaign_ids', 0) > 0:
            critical_issues.append(f"❌ {self.stats['invalid_campaign_ids']} leads with invalid campaign IDs")

        if self.stats.get('invalid_emails', 0) > 0:
            warnings.append(f"⚠️  {self.stats['invalid_emails']} leads with invalid email format")

        if self.stats.get('invalid_companies', 0) > 0:
            warnings.append(f"⚠️  {self.stats['invalid_companies']} leads with invalid company names")

        if self.stats.get('first_no_last', 0) > 0:
            warnings.append(f"⚠️  {self.stats['first_no_last']} leads with first name but no last name")

        if self.stats.get('last_no_first', 0) > 0:
            warnings.append(f"⚠️  {self.stats['last_no_first']} leads with last name but no first name")

        if critical_issues:
            print(f"{RED}{BOLD}CRITICAL ISSUES:{RESET}")
            for issue in critical_issues:
                print(f"  {issue}")
            print()

        if warnings:
            print(f"{YELLOW}{BOLD}WARNINGS:{RESET}")
            for warning in warnings:
                print(f"  {warning}")
            print()

        if not critical_issues and not warnings:
            print(f"{GREEN}{BOLD}✅ NO ISSUES FOUND - Data quality looks good!{RESET}\n")

        print(f"{BOLD}Overall Health:{RESET}")
        print(f"  Total leads: {self.stats.get('total_leads', 0)}")
        print(f"  In Smartlead: {self.stats.get('in_smartlead', 0)}")
        print(f"  Data completeness: {self.stats.get('completeness', {}).get('all_fields', 0)} leads with all fields ({self.stats.get('completeness', {}).get('all_fields', 0)/self.stats.get('total_leads', 1)*100:.1f}%)")
        print()

        return critical_issues, warnings

    def run_audit(self):
        """Run full audit"""
        print(f"{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}SUPABASE DATA QUALITY AUDIT{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

        # Fetch all leads
        leads = self.fetch_all_leads()

        # Run all checks
        self.check_duplicate_emails(leads)
        self.check_missing_required_fields(leads)
        self.check_inconsistent_names(leads)
        self.check_invalid_company_names(leads)
        self.check_smartlead_tracking(leads)
        self.check_email_format(leads)
        self.check_data_completeness(leads)
        self.check_field_consistency(leads)
        self.generate_statistics(leads)

        # Save report
        report_path = self.save_report()

        # Print summary
        critical_issues, warnings = self.print_summary()

        return {
            'total_leads': len(leads),
            'critical_issues': critical_issues,
            'warnings': warnings,
            'report_path': report_path,
            'stats': dict(self.stats)
        }

def main():
    try:
        auditor = SupabaseAuditor()
        results = auditor.run_audit()

        # Exit code based on issues found
        if results['critical_issues']:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"{RED}❌ Error running audit: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()
