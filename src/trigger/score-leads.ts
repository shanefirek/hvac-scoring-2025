import { logger, task } from "@trigger.dev/sdk/v3";
import { supabaseService, Lead } from "./utils/supabase";

export interface ScoreLeadsPayload {
  batchSize?: number; // Default 100
}

interface ScoreBreakdown {
  service_software?: number;
  reviews_500_plus?: number;
  reviews_100_499?: number;
  reviews_25_99?: number;
  reviews_10_24?: number;
  domain?: number;
  total: number;
}

/**
 * Calculate score based on schema scoring system:
 * - Service Software: +15
 * - Reviews 500+: +10
 * - Reviews 100-499: +7
 * - Reviews 25-99: +4
 * - Reviews 10-24: +2
 * - Domain exists: +2
 */
function calculateScore(lead: Lead): {
  score: number;
  tier: "A" | "B" | "C";
  breakdown: ScoreBreakdown;
} {
  const breakdown: ScoreBreakdown = { total: 0 };

  // Service software (+15) - most important signal
  if (lead.service_software) {
    breakdown.service_software = 15;
    breakdown.total += 15;
  }

  // Reviews scoring (tiered)
  const reviews = lead.reviews_count || 0;
  if (reviews >= 500) {
    breakdown.reviews_500_plus = 10;
    breakdown.total += 10;
  } else if (reviews >= 100) {
    breakdown.reviews_100_499 = 7;
    breakdown.total += 7;
  } else if (reviews >= 25) {
    breakdown.reviews_25_99 = 4;
    breakdown.total += 4;
  } else if (reviews >= 10) {
    breakdown.reviews_10_24 = 2;
    breakdown.total += 2;
  }

  // Domain exists (+2)
  if (lead.domain || lead.site) {
    breakdown.domain = 2;
    breakdown.total += 2;
  }

  // Determine tier based on total score
  let tier: "A" | "B" | "C";
  if (breakdown.total >= 20) {
    tier = "A"; // 20-30 points
  } else if (breakdown.total >= 10) {
    tier = "B"; // 10-19 points
  } else {
    tier = "C"; // 0-9 points
  }

  return {
    score: breakdown.total,
    tier,
    breakdown,
  };
}

export const scoreLeadsTask = task({
  id: "score-leads",
  maxDuration: 300, // 5 minutes
  retry: {
    maxAttempts: 2,
  },
  run: async (payload: ScoreLeadsPayload = {}) => {
    const { batchSize = 100 } = payload;

    logger.info("Starting lead scoring", { batchSize });

    // Fetch enriched leads that haven't been scored yet
    const leads = await supabaseService.getLeadsForScoring(batchSize);

    logger.info(`Found ${leads.length} leads to score`);

    let scored = 0;
    let tierCounts = { A: 0, B: 0, C: 0 };
    let failures = 0;

    for (const lead of leads) {
      try {
        const { score, tier, breakdown } = calculateScore(lead);

        await supabaseService.updateScore(lead.id, score, tier, breakdown);

        scored++;
        tierCounts[tier]++;

        logger.info(`Scored lead`, {
          lead_id: lead.id,
          company: lead.company,
          score,
          tier,
        });
      } catch (error) {
        logger.error(`Failed to score lead ${lead.id}`, { error });
        failures++;
      }
    }

    const summary = {
      leads_processed: leads.length,
      scored,
      failures,
      tier_distribution: tierCounts,
      avg_score:
        scored > 0
          ? (
              leads.slice(0, scored).reduce((sum, l) => sum + (l.score || 0), 0) /
              scored
            ).toFixed(1)
          : 0,
    };

    logger.info("Lead scoring completed", summary);

    return summary;
  },
});
