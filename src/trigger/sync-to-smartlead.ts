import { logger, task } from "@trigger.dev/sdk/v3";
import { supabaseService, Lead } from "./utils/supabase";
import { smartleadService, SmartleadLead } from "./utils/smartlead";

export interface SyncToSmartleadPayload {
  tier?: "A" | "B" | "C"; // If provided, sync only this tier
  batchSize?: number; // Default 100
}

/**
 * Convert Supabase lead to Smartlead format
 */
function formatLeadForSmartlead(lead: Lead): SmartleadLead {
  return {
    email: lead.email,
    first_name: lead.first_name || "",
    last_name: lead.last_name || "",
    company_name: lead.company || "",
    website: lead.site || lead.domain || "",
    phone_number: lead.phone || "",
    location: [lead.city, lead.state].filter(Boolean).join(", "),
    custom_fields: {
      reviews_count: lead.reviews_count || 0,
      service_software: lead.service_software || "",
      score: lead.score || 0,
      tier: lead.tier || "",
    },
  };
}

export const syncToSmartleadTask = task({
  id: "sync-to-smartlead",
  maxDuration: 900, // 15 minutes
  retry: {
    maxAttempts: 2,
  },
  run: async (payload: SyncToSmartleadPayload = {}) => {
    const { tier, batchSize = 100 } = payload;

    const tiersToSync = tier ? [tier] : (["A", "B", "C"] as const);

    logger.info("Starting Smartlead sync", {
      tiers: tiersToSync,
      batchSize,
    });

    let totalSynced = 0;
    let totalFailed = 0;
    const tierResults: Record<string, { synced: number; failed: number }> = {};

    for (const currentTier of tiersToSync) {
      logger.info(`Syncing ${currentTier}-tier leads`);

      try {
        // Get campaign ID for this tier
        const campaignId = smartleadService.getCampaignIdForTier(currentTier);

        // Fetch leads ready for sync
        const leads = await supabaseService.getLeadsForSmartlead(
          currentTier,
          batchSize
        );

        logger.info(`Found ${leads.length} ${currentTier}-tier leads to sync`);

        if (leads.length === 0) {
          tierResults[currentTier] = { synced: 0, failed: 0 };
          continue;
        }

        let synced = 0;
        let failed = 0;

        // Process leads one by one (safer than batch for tracking)
        for (const lead of leads) {
          try {
            const smartleadLead = formatLeadForSmartlead(lead);
            const result = await smartleadService.addLead(
              campaignId,
              smartleadLead
            );

            // Update Supabase with Smartlead lead ID
            await supabaseService.updateSmartleadSync(
              lead.id,
              result.lead_id,
              campaignId
            );

            synced++;
            totalSynced++;

            logger.info(`Synced lead to ${currentTier}-tier campaign`, {
              lead_id: lead.id,
              smartlead_lead_id: result.lead_id,
              email: lead.email,
              company: lead.company,
            });
          } catch (error) {
            logger.error(`Failed to sync lead`, {
              lead_id: lead.id,
              email: lead.email,
              error,
            });
            failed++;
            totalFailed++;
          }
        }

        tierResults[currentTier] = { synced, failed };
      } catch (error) {
        logger.error(`Failed to sync ${currentTier}-tier`, { error });
        tierResults[currentTier] = { synced: 0, failed: 0 };
      }
    }

    const summary = {
      tiers_processed: tiersToSync.length,
      total_synced: totalSynced,
      total_failed: totalFailed,
      tier_results: tierResults,
    };

    logger.info("Smartlead sync completed", summary);

    return summary;
  },
});
