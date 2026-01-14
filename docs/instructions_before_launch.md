Smartlead Campaign Configuration - Final Setup Instructions
Campaign Launch Date: Monday, November 18, 2025
Total Leads: 151 (16 A-Tier, 29 B-Tier, 106 C-Tier)
Email Accounts: 3 (SMTP/Zoho, Outlook, Gmail)
Objective: Configure all settings for clean Monday morning launch

CAMPAIGN OVERVIEW
A-TIER: Software & Scale (Campaign ID: 2677089)

Leads: 16 total
Email Sequence: 4 emails over 14 days
Cadence: Day 0 → Day 4 → Day 9 → Day 14
Daily Send Limit: 10 leads/day
Lead Distribution: ~5-6 leads per email account

B-TIER: Growth Signal (Campaign ID: 2677090)

Leads: 29 total
Email Sequence: 3 emails over 12 days
Cadence: Day 0 → Day 5 → Day 12
Daily Send Limit: 8 leads/day
Lead Distribution: ~10 leads per email account

C-TIER: Pain Focus (Campaign ID: 2677091)

Leads: 106 total
Email Sequence: 2 emails over 10 days
Cadence: Day 0 → Day 10
Daily Send Limit: 10 leads/day
Lead Distribution: ~35 leads per email account


CRITICAL CONFIGURATION TASKS
TASK 1: Update Send Schedule (All 3 Campaigns)
Navigate to: Campaign Settings → Sending Schedule
Configure:
Send Days: Monday, Tuesday, Wednesday, Thursday, Friday
Send Times: 
  - 9:00 AM - 11:30 AM ET
  - 1:00 PM - 3:00 PM ET
Timezone: America/New_York (Eastern Time)
Minimum Gap Between Emails: 120 seconds (2 minutes)
Randomize Send Times: ENABLED
Apply to: Campaigns 2677089, 2677090, 2677091

TASK 2: Configure Sequence Stop Conditions (All 3 Campaigns)
Navigate to: Campaign Settings → Automation Rules
Enable the following stops:
✅ Stop sequence on reply
✅ Stop sequence on auto-reply  
✅ Stop sequence on hard bounce
✅ Stop sequence on soft bounce (after 2 attempts)
✅ Stop sequence on unsubscribe
❌ Do NOT stop on link click
Apply to: Campaigns 2677089, 2677090, 2677091

TASK 3: Verify Lead Distribution Across Email Accounts
Navigate to: Campaign → Leads → View Lead List
Check that leads are distributed evenly:

Each campaign should have leads roughly balanced across all 3 email accounts
No single account should have >40% of leads from any campaign

If distribution is unbalanced:

Go to Campaign Settings → Email Accounts
Enable "Distribute leads evenly across accounts"
Or manually reassign leads for better balance


TASK 4: Email Account - Auto-Reply Detection
Navigate to: Settings → Email Accounts → [Each Account]
For ALL 3 email accounts (SMTP/Zoho, Outlook, Gmail):
Auto-Reply Detection: ENABLED
Actions on auto-reply detected:
  ✅ Stop sequence for this lead
  ✅ Tag lead as "Auto-reply"
  ✅ Move to "Auto-reply" category
Test auto-reply detection:

Send test email from each account to a personal email
Reply with an out-of-office/auto-reply message
Verify Smartlead detects it and stops the sequence


TASK 5: Email Account - Reply Forwarding
Navigate to: Settings → Email Accounts → [Each Account]
For ALL 3 email accounts:
Option A - Forward to Primary Email (Recommended):
Reply Forwarding: ENABLED
Forward replies to: [AWAITING EMAIL ADDRESS FROM USER]
Keep copy in Smartlead: YES
Subject prefix: "[Campaign Reply] "
Option B - Use Smartlead Unified Inbox Only:
Navigate to: Settings → Notifications
✅ Email notification on new reply
✅ Browser notification enabled
Notification email: [AWAITING EMAIL ADDRESS FROM USER]
Test forwarding:

Send test email from each campaign
Reply to the test email
Verify reply appears in designated inbox within 2-3 minutes


TASK 6: Verify Email Account Health
Navigate to: Settings → Email Accounts
For each of the 3 accounts, verify:
SPF Status: ✅ Verified (GREEN)
DKIM Status: ✅ Verified (GREEN)  
DMARC Status: ✅ Verified (GREEN)
Warm-up Status: [Record current status]
Daily Warm-up Volume: [Record current volume]
Account Reputation: [Should be GREEN]
If any DNS records show RED or YELLOW:

STOP and report issue immediately
Do not proceed with launch until resolved


TASK 7: Tracking Configuration
Navigate to: Settings → Tracking
Current Configuration Check:
Open Tracking: [Check if ON/OFF]
Click Tracking: [Check if ON/OFF]
Custom Tracking Domain: [Check if configured]
Required Action:
IF custom tracking domain is NOT set up:

Disable click tracking entirely (better deliverability)
Keep open tracking enabled

IF custom tracking domain IS set up:

Keep both open and click tracking enabled
Verify domain is properly configured and verified


TASK 8: Unsubscribe Compliance Check
Navigate to: Settings → Unsubscribe
Verify:
✅ One-click unsubscribe: ENABLED
✅ Unsubscribe link auto-added to emails: YES
✅ Auto-stop sequence on unsubscribe: YES
Check each campaign's email templates:

Open each email in the sequence
Scroll to footer
Verify unsubscribe link is present and visible
Test unsubscribe link (click and verify it works)


TASK 9: Content Validation (All Email Templates)
For EACH email in ALL 3 campaigns:
Navigate to: Campaign → Email Sequence → [Each Email]
Check:
✅ Personalization tokens working ({{firstName}}, {{companyName}}, etc.)
✅ No spam trigger words (free, guarantee, limited time, click here, act now)
✅ Unsubscribe link in footer
✅ Links use custom tracking domain (if applicable)
✅ Plain text version exists and is readable
✅ No broken formatting or code visible
Send test emails:

From A-Tier Email 1: Send to test@email.com
From B-Tier Email 1: Send to test@email.com
From C-Tier Email 1: Send to test@email.com
Review formatting, personalization, deliverability in inbox


TASK 10: Pre-Launch Status Configuration
Navigate to: Campaign Settings → Status
Set ALL 3 campaigns to:
Campaign Status: SCHEDULED (not ACTIVE)
Scheduled Start Date: Monday, November 18, 2025
Scheduled Start Time: 8:30 AM ET
Do NOT activate campaigns yet - they will be manually activated Monday morning.

VALIDATION CHECKLIST
Before completing this configuration, verify all items are complete:
Campaign Settings

 Send schedule: Mon-Fri, 9-11:30 AM & 1-3 PM ET (all 3 campaigns)
 Minimum gap between emails: 120 seconds (all 3 campaigns)
 Randomize send times: ENABLED (all 3 campaigns)
 Daily send limits: A-Tier=10, B-Tier=8, C-Tier=10
 Sequence stops configured: reply, auto-reply, bounce, unsubscribe

Email Account Configuration

 Auto-reply detection: ENABLED (all 3 accounts)
 Reply forwarding: CONFIGURED and TESTED (all 3 accounts)
 SPF/DKIM/DMARC: All GREEN (all 3 accounts)
 Warm-up status: VERIFIED and LOGGED
 Lead distribution: BALANCED across accounts

Tracking & Compliance

 Tracking settings: VERIFIED (custom domain or click tracking disabled)
 Unsubscribe: ENABLED and TESTED
 Unsubscribe links: PRESENT in all email footers

Content & Testing

 Personalization tokens: WORKING in all emails
 Spam words: REMOVED from all emails
 Test emails: SENT and REVIEWED from all campaigns
 Plain text versions: VERIFIED readable

Launch Preparation

 All campaigns: Set to SCHEDULED status
 Launch date/time: Monday 11/18/2025, 8:30 AM ET
 Auto-reply test: COMPLETED successfully
 Reply forwarding test: COMPLETED successfully


REPORTING REQUIREMENTS
After completing all tasks above, provide the following information:
Email Account Status Report
Account 1 (SMTP/Zoho):
  - SPF/DKIM/DMARC Status: 
  - Warm-up Status: 
  - Daily Warm-up Volume:
  - Current Reputation:

Account 2 (Outlook):
  - SPF/DKIM/DMARC Status:
  - Warm-up Status:
  - Daily Warm-up Volume:
  - Current Reputation:

Account 3 (Gmail):
  - SPF/DKIM/DMARC Status:
  - Warm-up Status:
  - Daily Warm-up Volume:
  - Current Reputation:
Lead Distribution Report
A-Tier Campaign (2677089) - 16 leads total:
  - Account 1: ___ leads
  - Account 2: ___ leads
  - Account 3: ___ leads

B-Tier Campaign (2677090) - 29 leads total:
  - Account 1: ___ leads
  - Account 2: ___ leads
  - Account 3: ___ leads

C-Tier Campaign (2677091) - 106 leads total:
  - Account 1: ___ leads
  - Account 2: ___ leads
  - Account 3: ___ leads
Tracking Configuration Report
Open Tracking: ENABLED / DISABLED
Click Tracking: ENABLED / DISABLED
Custom Tracking Domain: CONFIGURED / NOT CONFIGURED
If configured, domain name: _______________
Reply Forwarding Configuration
Forwarding Method: PRIMARY EMAIL / SMARTLEAD INBOX ONLY
If primary email, address: _______________
Test Status: SUCCESSFUL / FAILED

ISSUES & BLOCKERS
If you encounter any of the following, STOP and report immediately:

DNS Records Not Green: Any SPF/DKIM/DMARC showing yellow or red
Warm-up Issues: Accounts showing poor reputation or high bounce rates
Lead Import Errors: Leads not uploading or missing required fields
Test Email Failures: Test emails bouncing or not delivering
Reply Forwarding Failures: Test replies not arriving in designated inbox
Auto-reply Detection Failures: Auto-replies not being detected/stopped

