# DNS & Email Authentication Setup

**Last Updated:** January 24, 2026

---

## Domain Status

| Domain | SPF | DMARC | DKIM | Provider |
|--------|-----|-------|------|----------|
| appletree-tax.com | ✅ Google + Smartlead | ✅ `p=none` | ✅ Google | Porkbun |
| appletree-advisors.com | ✅ Smartlead | ✅ `p=none` | ✅ Outlook | Porkbun |
| appletree-taxes.com | ✅ Zoho + Smartlead | ✅ `p=none` | ❌ Missing | Porkbun |
| macrohub.co | ✅ Outlook | ✅ `p=reject` | ✅ Outlook | Porkbun |
| updates.appletree-tax.com | ✅ Amazon SES | - | ✅ Resend | Porkbun |

**DMARC reports** sent to: `shanefirek@gmail.com`

---

## DNS Manager CLI

Location: `scripts/dns-manager.ts`

```bash
# Audit any domain
npx ts-node scripts/dns-manager.ts audit <domain>

# List DNS records via Porkbun API
npx ts-node scripts/dns-manager.ts porkbun:list <domain>

# Setup Resend domain + auto-create DNS records
npx ts-node scripts/dns-manager.ts resend:setup <domain>

# List Resend domains and status
npx ts-node scripts/dns-manager.ts resend:list

# Add DMARC policy
npx ts-node scripts/dns-manager.ts setup:dmarc <domain>

# Add Smartlead to SPF
npx ts-node scripts/dns-manager.ts setup:smartlead <domain>
```

### Required .env Variables

```
RESEND_API_KEY=re_xxxxxxxxx
PORKBUN_API_KEY=pk1_xxxxxxxxx
PORKBUN_SECRET_KEY=sk1_xxxxxxxxx
```

### Porkbun API Access

API access must be enabled per-domain in Porkbun:
1. Go to https://porkbun.com/account/domainsSS
2. Click the domain
3. Toggle "API Access" ON

---

## Resend Setup

**Domain:** `updates.appletree-tax.com`
**Status:** Pending verification (DNS records live)
**From address:** `leads@updates.appletree-tax.com`

### DNS Records (in Porkbun)

| Type | Name | Value |
|------|------|-------|
| TXT | `resend._domainkey.updates` | DKIM public key |
| TXT | `send.updates` | `v=spf1 include:amazonses.com ~all` |
| MX | `send.updates` | `feedback-smtp.us-east-1.amazonses.com` (priority 10) |

---

## Lead Reply Notifications

**Edge Function:** `notify-lead-reply`
**URL:** `https://rlmuovkdvbxzyylbiunj.supabase.co/functions/v1/notify-lead-reply`

### How It Works

1. Lead replies to campaign email
2. Smartlead webhook fires `EMAIL_REPLY` event
3. Edge Function receives webhook payload
4. Enriches lead data from Supabase (phone, tier, location)
5. Sends formatted email via Resend

### Current Recipient

- `shanefirek@gmail.com` (testing)
- Patrick's email commented out - uncomment when ready for production

### Webhooks Configured

All 4 campaigns have `EMAIL_REPLY` webhook pointing to Edge Function:

| Campaign | Webhook ID |
|----------|------------|
| C-Tier (2677091) | 408580 |
| Marketing Agencies (2843683) | 408581 |
| A-Tier (2677089) | 408582 |
| B-Tier (2677090) | 408583 |

---

## DMARC Rollout Plan

Current: `p=none` (monitoring)

### Timeline

1. **Now - Feb 2026:** Monitor reports at `shanefirek@gmail.com`
2. **After clean reports:** Upgrade to `p=quarantine`
3. **Final:** Move to `p=reject` for full protection

### Upgrade Command

```bash
# Delete old record first via Porkbun dashboard or API
# Then add new policy:
npx ts-node scripts/dns-manager.ts setup:dmarc <domain>
# Choose "quarantine" or "reject" when prompted
```

---

## TODO

- [ ] Verify Resend domain (check dashboard or wait for auto-verify)
- [ ] Add DKIM for appletree-taxes.com (get from Zoho admin)
- [ ] Monitor DMARC reports for 2-4 weeks
- [ ] Upgrade DMARC to `p=quarantine` then `p=reject`
- [ ] Switch notification recipient to Patrick when ready
