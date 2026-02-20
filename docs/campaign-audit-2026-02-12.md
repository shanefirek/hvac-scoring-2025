# Full Campaign Audit - February 12, 2026

---

## All Campaigns At a Glance

| Campaign | ID | Status | Leads | Sent | Open Rate | Click Rate | Reply Rate | Bounce Rate | Verdict |
|----------|-----|--------|-------|------|-----------|------------|------------|-------------|---------|
| HVAC A-Tier | 2677089 | PAUSED | 341 | 348 | **53.2%** | **14.7%** | 0.9% | 1.7% | HEALTHY |
| HVAC B-Tier | 2677090 | PAUSED | 271 | 771 | **49.9%** | **10.9%** | 0.1% | 1.8% | HEALTHY |
| HVAC C-Tier | 2677091 | ACTIVE | 3,040 | 10,778 | 35.2% | 1.3% | 0.16% | 6.8% | DEGRADED |
| MA v1 | 2843683 | PAUSED | 1,066 | 2,048 | 36.9% | 0% | 0.2% | **12.4%** | DEAD |
| MA v2 | 2885428 | ACTIVE | 1,466 | 1,081 | 18.7% | **6.2%** | 0% | 1.5% | PROMISING |
| A/B Tests (x4) | 2757801-05 | PAUSED | ~663 | 663 | 35-44% | 0% | 0% | 2-4% | DEAD |
| HVAC Re-engage | 2885427 | DRAFTED | 0 | 0 | - | - | - | - | NEVER LAUNCHED |

---

## Campaign 1: HVAC C-Tier (2677091) — ACTIVE

### Performance
- **10,778 sent** over 91 days to 3,040 leads
- 75.3% of leads completed full 4-email sequence
- 1,078 unique opens (25.6%), 108 clicks (1.3%), 17 replies (0.16%)
- **0 meetings booked**

### Sequence Performance
| Step | Subject | Sent | Open Rate | Click Rate | Bounce Rate |
|------|---------|------|-----------|------------|-------------|
| 1 | Where is {{company_name}}'s CPA? | 2,807 | 24.8% | 0% | 8.2% |
| 2 | Re: Quick Question | 2,733 | 21.3% | **2.5% (67 clicks)** | 6.3% |
| 3 | What most HVAC owners miss | 2,208 | 25.4% | 0.05% | 3.5% |
| 4 | Should I close your file? | 1,814 | 25.9% | 0% | **12.3%** |

**Key finding:** Sequence 2 drives almost all clicks (67 of 108 total). The "Re:" thread continuation tactic works. Sequence 4 has a 12.3% bounce rate — by email 4, servers are blocking the sender.

**Major drop-off:** 525 leads (19.2%) didn't make it from Seq 2 → Seq 3. Likely autopause from bounce threshold.

### Mailbox Performance (C-Tier)
| Mailbox | Sent | Open Rate | Bounce Rate | Sender Bounces |
|---------|------|-----------|-------------|----------------|
| team@appletree-tax.com | 1,916 | 34.0% | 0.73% | 0 |
| sales@appletree-tax.com | 1,823 | 30.8% | 0.27% | 0 |
| patrick@appletree-tax.com | 1,692 | 28.8% | 0.47% | 2 |
| team@appletree-taxes.com | 2,059 | **22.8%** | 1.21% | **13** |

**team@appletree-taxes.com is weakest** — lowest open rate, highest sender bounces, 19 unsubscribes (vs 1-4 on others). Zoho SMTP underperforming Gmail accounts.

### Bounce Analysis (from earlier deep dive)
- **629 bounced leads** — all "Sender Originated Bounce" (server rejecting sender, not invalid addresses)
- 35% generic role emails (info@, contact@), 48% business personal, 16% freemail
- Bounces increase at later sequence steps (164 → 164 → 78 → 223)
- 84% of bounced leads never opened a single email
- 29% of bounced leads have first_name="there" (data quality bug)

### Verdict
Campaign is operationally running but strategically dead. Good subject lines (25%+ opens) but copy/CTA doesn't convert. 24% all-time bounce rate is destroying sender reputation. **Should be paused.**

---

## Campaign 2: Marketing Agencies v2 (2885428) — ACTIVE

### Performance
- **1,081 sent** over 14 days to 1,466 leads (476 unique contacts reached)
- 989 leads (67.5%) not yet started — large pipeline remaining
- 151 opens, **67 clicks (6.2%)**, 0 replies
- **0 meetings booked** but highest click rate of any campaign

### Sequence Performance
| Step | Subject | Sent | Open Rate | Click Rate | Notes |
|------|---------|------|-----------|------------|-------|
| 1 | {{company_name}} - quick finance question | 476 | 18.3% | **10.5% (50 clicks)** | Excellent opener |
| 2 | Re: quick finance question | 333 | 8.7% | 0% | Bump underperformed |
| 3 | Quick tax math for {{company_name}} | 185 | 10.8% | **9.2% (17 clicks)** | Strong re-engagement |
| 4 | Closing the loop | 87 | 17.2% | 0% | Breakup, expected |

**Key findings:**
- Seq 1 and Seq 3 both drive clicks (~10% CTR each) — the "$20-50K overpaying" hook and "free estimate" offer resonate
- Seq 2 (bump) gets 0 clicks — "reply and I'll send my calendar" CTA is weaker than direct Calendly link
- Click-to-open ratio of **44.4%** is excellent — when people open, they click

### Mailbox Performance (MA v2)
| Mailbox | Sent | Open Rate | Click Rate | Bounce Rate |
|---------|------|-----------|------------|-------------|
| sales@appletree-tax.com | 360 | 13.9% | **7.2%** | 1.39% |
| patrick@appletree-tax.com | 367 | 12.0% | 5.7% | 1.09% |
| team@appletree-taxes.com | 180 | 16.1% | 5.6% | 2.78% |
| team@appletree-tax.com | 174 | 16.1% | 5.7% | 1.15% |

All mailboxes healthy on this campaign. sales@ is top performer.

### Critical Issues Found
1. **NO WEBHOOKS CONFIGURED** — Reply notifications are NOT being sent to the Edge Function. If someone replies, you won't know.
2. **Weekend sending disabled** — Mon-Fri only, should be 7 days per original design
3. **End hour is 17:00** — should be 17:30 per standard config

### Verdict
Best-performing campaign by click rate. 67 Calendly clicks in 14 days with 0 replies suggests people are interested but the Calendly page or meeting ask isn't closing. **Keep running but fix webhooks immediately.** 989 untouched leads remaining.

---

## Campaign 3: HVAC A-Tier (2677089) — PAUSED

### Performance
- **348 sent** to 132 unique leads (of 341 total)
- 218 leads (64%) not yet started
- 53.2% open rate, **14.7% click rate**, 3 replies (0.9%)
- Bounce rate: 1.7% — healthy

### Mailbox Performance
| Mailbox | Sent | Open Rate | Bounce |
|---------|------|-----------|--------|
| team@appletree-tax.com | 81 | **77.8%** | 1.2% |
| team@appletree-taxes.com | 119 | 49.6% | 1.7% |

### Verdict
**Best campaign in the account.** 53% open rate and 14.7% click rate — these are ServiceTitan/Jobber users who actually resonate with the pitch. 218 untouched leads. **Should be unpaused on fresh infrastructure.**

---

## Campaign 4: HVAC B-Tier (2677090) — PAUSED

### Performance
- **771 sent** to 302 unique leads (of 271 total — some leads got all 4 emails)
- 0 leads not started — everyone has been contacted
- 49.9% open rate, 10.9% click rate, 1 reply
- Bounce rate: 1.8% — healthy

### Mailbox Performance
| Mailbox | Sent | Open Rate | Bounce |
|---------|------|-----------|--------|
| team@appletree-tax.com | 191 | **68.6%** | 0.5% |
| team@appletree-taxes.com | 183 | 42.6% | 2.7% |
| patrick@appletree-tax.com | 54 | 53.7% | 0% |
| sales@appletree-tax.com | 53 | 45.3% | 0% |

### Verdict
Solid engagement but list is fully exhausted — 0 not-started leads. Would need new leads or a re-engagement sequence to reactivate. **No action needed unless adding fresh leads.**

---

## Campaign 5: Marketing Agencies v1 (2843683) — PAUSED

### Performance
- **2,048 sent** to 834 unique leads (of 1,066 total)
- 36.9% open rate, **0% click rate**, 4 replies
- **Bounce rate: 12.4%** — well above 10% autopause threshold
- **Sender bounce rate: 23.4%** (479 sender bounces out of 2,048 sent)

### Sequence Degradation
| Step | Sent | Open Rate | Sender Bounce Rate | Stopped |
|------|------|-----------|-------------------|---------|
| 1 | 836 | 32.7% | **27.3%** | - |
| 2 | 566 | 44.0% | **29.0%** | 74 |
| 3 | 399 | 48.6% | **21.8%** | 153 |
| 4 | 247 | 15.8% | 0% | **244 (98.8%)** |

Campaign hit autopause threshold by Seq 4 — 98.8% of leads were stopped.

### Mailbox Performance
| Mailbox | Sent | Open Rate | Bounce Rate | Sender Bounce |
|---------|------|-----------|-------------|---------------|
| team@appletree-tax.com | 216 | 60.2% | **10.6%** | 10.6% |
| team@appletree-taxes.com | 226 | 50.9% | 1.8% | 0% |
| patrick@appletree-tax.com | 433 | 44.1% | 6.7% | 6.5% |
| sales@appletree-tax.com | 415 | 41.4% | 7.2% | 6.5% |

**team@appletree-tax.com had 10.6% sender bounce on this campaign** — the marketing agency list hammered this mailbox.

### Verdict
**Dead campaign. Do not unpause.** 23.4% sender bounce rate destroyed deliverability. The marketing agency email list from v1 had severe quality issues. v2 was created to fix this (and is performing much better at 1.5% bounce).

---

## Cross-Campaign Insights

### What Works
1. **A-Tier leads are the best audience** — 53% open, 14.7% click, 1.7% bounce
2. **"Re:" thread continuation** drives clicks across all campaigns
3. **Direct Calendly links** outperform "reply for my calendar" CTAs
4. **appletree-tax.com Gmail accounts** consistently outperform Zoho (appletree-taxes.com)
5. **Shorter, value-first emails** (Seq 1 and Seq 3 on MA v2) get the most clicks

### What Doesn't Work
1. **C-Tier HVAC at volume** — 10,778 sends, 0 meetings. List quality + generic copy = waste
2. **Marketing agency lists without validation** — MA v1 had 23% sender bounce
3. **"Reply fit" / "Reply yes" CTAs** — lower conversion than Calendly links
4. **30-min meeting asks** — C-Tier uses 30min Calendly, MA v2 uses 15min. 15min is better.
5. **Weekend sending on degraded domains** — accelerates reputation damage

### Mailbox Rankings (Combined Performance)
| Rank | Mailbox | Avg Open Rate | Avg Bounce | Notes |
|------|---------|---------------|------------|-------|
| 1 | team@appletree-tax.com | ~55% | ~2% | Best opener, but took a hit on MA v1 |
| 2 | sales@appletree-tax.com | ~33% | ~1.5% | Most consistent, lowest bounce |
| 3 | patrick@appletree-tax.com | ~35% | ~1.5% | Solid, no issues |
| 4 | team@appletree-taxes.com | ~35% | ~2% | Zoho, weakest sender reputation |

---

## Immediate Actions

### Critical
- [ ] **Add webhook to MA v2 (2885428)** — replies are not being captured
- [ ] **Pause C-Tier (2677091)** — 24% bounce, actively damaging sender reputation

### Before Relaunch
- [ ] Buy 2-3 fresh domains (no "tax" in name)
- [ ] Buy 3-4 prewarmed inboxes
- [ ] SPF + DKIM + DMARC on new domains day one
- [ ] New 3-email sequence with "7 Ways to Save" lead magnet
- [ ] Marketing Agencies only on new infrastructure
- [ ] 50-80/day max, weekdays only

### Infrastructure
- [ ] Set Trigger.dev env vars and deploy sync-from-smartlead
- [ ] Update CLAUDE.md with current state
- [ ] Clean bounced leads from Supabase

---

*Generated February 12, 2026 from Smartlead API data across all 9 campaigns.*
