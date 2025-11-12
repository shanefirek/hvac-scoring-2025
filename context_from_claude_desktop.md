# Clay Lead Scoring & Smartlead Routing System

## Overview
Building a lead management flywheel for HVAC businesses that scrapes → enriches → scores → routes to Smartlead for outbound campaigns.

## Current State
- **200 enriched leads** in existing Clay table
- All emails validated (99.9%)
- Catchall emails replaced with decision-maker emails via API
- Mix of independent HVAC businesses and franchises (ARS, Rescue Rooter, etc.)

## Data Schema

### Available Columns
1. Company name
2. Contact name (full + first name)
3. LinkedIn URL (sparse, most not active)
4. Review Count (ranges from 25 to 2,500+)
5. Domain
6. Service Software flag (ServiceTitan, Jobber, Housecall Pro)
7. Validated email (final column)

### Required New Columns
- **Score** (calculated field)
- **Tier** (A/B/C classification)
- **Is Franchise** (boolean flag)
- **Messaging Strategy** (which template to use)

## Scoring Logic

```javascript
let score = 0;

// Service software check (+15 points - HUGE signal)
if (service_software includes "ServiceTitan" OR "Jobber" OR "Housecall Pro") {
  score += 15;
}

// Review count (adjusted for franchise vs independent)
if (is_franchise === "YES") {
  score += 10;  // Franchises always score high (have systems)
} else {
  if (review_count >= 500) score += 10;
  else if (review_count >= 100) score += 7;
  else if (review_count >= 25) score += 4;
  else if (review_count >= 10) score += 2;
}

// LinkedIn presence (+3 points)
if (linkedin_url exists) score += 3;

// Domain (+2 points)
if (domain exists) score += 2;

// Total possible: 30 points
```

## Franchise Detection

```javascript
// Flag franchises by name matching
franchises = ["ARS", "Rescue Rooter", "One Hour", "Benjamin Franklin", 
              "Roto-Rooter", "Mr. Rooter", "Aire Serv", "Goettl"];

is_franchise = franchises.some(f => company_name.includes(f)) ? "YES" : "NO";
```

## Tier Classification

- **A-Tier (20-30 points)**: Franchise OR (ServiceTitan/Jobber/HCP + high reviews)
- **B-Tier (10-19 points)**: Good reviews OR service software (not both)
- **C-Tier (0-9 points)**: Lower reviews, no service software

## Messaging Strategy by Tier

### A-Tier: Software + Scale
- Target franchises and sophisticated independents
- Subject: "Tax planning for [Franchise] owners" or software-specific
- Angle: Understanding their scale/complexity
- **Franchise-specific**: Multi-unit operations, franchise fees, royalty structures
- **Software-specific**: "Most HVAC owners using [software] struggle with unresponsive CPAs..."

### B-Tier: Scale OR Tech
- Has one signal but not both
- Subject: Company-specific, mentions their visible signal
- Angle: "Saw your [X reviews/software setup]... sound familiar?"

### C-Tier: Pure Pain
- No strong sophistication signals
- Subject: Direct pain question
- Angle: "How responsive is your CPA during tax season? $15k surprise tax bills?"

## Smartlead Campaign Structure

### 3 Separate Campaigns
1. **"HVAC A-Tier - Software Users"**
   - 4 touchpoints over 2 weeks (aggressive)
   
2. **"HVAC B-Tier - Scale or Tech"**
   - 3 touchpoints over 3 weeks (normal)
   
3. **"HVAC C-Tier - Pain Focus"**
   - 2 touchpoints over 4 weeks (conservative)

### Fields to Push to Smartlead
- Email
- First Name  
- Company
- Tier (A/B/C)
- Service Software (for merge tags)
- Review Count (for merge tags)
- Messaging Strategy

## Execution Plan

### Week 1: A-Tier (~35 leads)
Launch first, test messaging with highest-value prospects

### Week 2: B-Tier (~75 leads)
Broader reach, still qualified

### Week 3: C-Tier (~90 leads)
Pure pain messaging for everyone else

## Next Steps for Implementation
1. Add franchise detection column
2. Add score calculation column
3. Add tier classification column
4. Add messaging strategy column
5. Create 3 campaigns in Smartlead with appropriate sequences
6. Map Clay columns to Smartlead fields
7. Launch A-Tier first

## Key Insights
- **Don't overthink structure** - these 200 leads are already enriched and ready to send
- **Franchises are high-value** despite review count skew (they have money + systems)
- **Pain-focused messaging > feature-focused** for local businesses
- **Tier differentiation matters** - different sophistication levels need different approaches