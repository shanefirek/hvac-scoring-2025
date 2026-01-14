import { logger, task } from "@trigger.dev/sdk/v3";
import { supabaseService } from "./utils/supabase";
import { detectSoftware, normalizeUrl } from "./utils/software-detect";

export interface EnrichLeadsPayload {
  batchSize?: number; // Default 50
}

export const enrichLeadsTask = task({
  id: "enrich-leads",
  maxDuration: 900, // 15 minutes
  retry: {
    maxAttempts: 2,
  },
  run: async (payload: EnrichLeadsPayload = {}) => {
    const { batchSize = 50 } = payload;

    logger.info("Starting lead enrichment", { batchSize });

    // Fetch leads that need enrichment (no enriched_at, has website)
    const leads = await supabaseService.getLeadsForEnrichment(batchSize);

    logger.info(`Found ${leads.length} leads to enrich`);

    let enriched = 0;
    let softwareDetected = 0;
    let failures = 0;

    // Process each lead with 10s timeout per site
    for (const lead of leads) {
      try {
        if (!lead.site) {
          logger.warn(`Lead ${lead.id} has no site, skipping`);
          // Still mark as enriched to avoid re-processing
          await supabaseService.updateEnrichment(lead.id, null);
          enriched++;
          continue;
        }

        const normalizedUrl = normalizeUrl(lead.site);
        const software = await detectSoftware(normalizedUrl, 10000);

        await supabaseService.updateEnrichment(lead.id, software);

        enriched++;
        if (software) {
          softwareDetected++;
          logger.info(`Detected ${software}`, {
            lead_id: lead.id,
            company: lead.company,
          });
        }
      } catch (error) {
        logger.error(`Failed to enrich lead ${lead.id}`, { error });
        failures++;
        // Continue to next lead
      }
    }

    const summary = {
      leads_processed: leads.length,
      enriched,
      software_detected: softwareDetected,
      failures,
      detection_rate:
        enriched > 0
          ? `${((softwareDetected / enriched) * 100).toFixed(1)}%`
          : "0%",
    };

    logger.info("Lead enrichment completed", summary);

    return summary;
  },
});
