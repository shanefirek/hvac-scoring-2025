import { logger, task } from "@trigger.dev/sdk/v3";
import { supabaseService } from "./utils/supabase";
import { smartleadService, SmartleadCampaignLead } from "./utils/smartlead";

// All active campaign IDs
const CAMPAIGN_IDS: Record<string, number> = {
  "A-Tier": 2677089,
  "B-Tier": 2677090,
  "C-Tier": 2677091,
  "Marketing Agencies": 2843683,
  "Marketing Agencies v2": 2885428,
};

export interface SyncFromSmartleadPayload {
  campaignIds?: number[]; // Specific campaigns, or all if omitted
}

interface CampaignSyncResult {
  campaignId: number;
  campaignName: string;
  totalLeads: number;
  updated: number;
  bounced: number;
  errors: number;
}

/**
 * Sync lead statuses FROM Smartlead back TO Supabase.
 * Pulls lead data, updates statuses, flags bounces.
 */
export const syncFromSmartleadTask = task({
  id: "sync-from-smartlead",
  maxDuration: 900, // 15 minutes
  retry: {
    maxAttempts: 2,
  },
  run: async (payload: SyncFromSmartleadPayload = {}) => {
    const campaignsToSync = payload.campaignIds
      ? Object.entries(CAMPAIGN_IDS).filter(([, id]) =>
          payload.campaignIds!.includes(id)
        )
      : Object.entries(CAMPAIGN_IDS);

    logger.info("Starting Smartlead → Supabase sync", {
      campaigns: campaignsToSync.map(([name, id]) => ({ name, id })),
    });

    const supabase = supabaseService.getClient();
    const results: CampaignSyncResult[] = [];

    for (const [campaignName, campaignId] of campaignsToSync) {
      logger.info(`Processing campaign: ${campaignName} (${campaignId})`);

      let updated = 0;
      let bounced = 0;
      let errors = 0;

      try {
        const leads = await smartleadService.getCampaignLeads(campaignId);

        for (const lead of leads) {
          if (!lead.email || !lead.id) continue;

          try {
            const email = lead.email.toLowerCase().trim();

            // Upsert lead status back to Supabase
            const { error } = await supabase
              .from("leads")
              .update({
                smartlead_lead_id: lead.id,
                in_smartlead: true,
                last_smartlead_sync: new Date().toISOString(),
              })
              .eq("email", email);

            if (error) {
              logger.warn(`Failed to update lead ${email}`, { error });
              errors++;
              continue;
            }

            // Update campaign_tracking status
            const isBounced =
              lead.lead_category === "Sender Originated Bounce" ||
              lead.lead_category === "Recipient Originated Bounce";

            if (isBounced) {
              bounced++;

              // Update campaign_tracking to BOUNCED
              await supabase
                .from("campaign_tracking")
                .update({
                  status: "BOUNCED",
                  updated_at: new Date().toISOString(),
                })
                .eq("smartlead_campaign_id", campaignId)
                .eq(
                  "lead_id",
                  (
                    await supabase
                      .from("leads")
                      .select("id")
                      .eq("email", email)
                      .single()
                  ).data?.id
                );
            }

            updated++;
          } catch (err) {
            logger.error(`Error processing lead`, {
              email: lead.email,
              error: err,
            });
            errors++;
          }
        }

        results.push({
          campaignId,
          campaignName,
          totalLeads: leads.length,
          updated,
          bounced,
          errors,
        });

        logger.info(`Campaign ${campaignName} done`, {
          totalLeads: leads.length,
          updated,
          bounced,
          errors,
        });
      } catch (err) {
        logger.error(`Failed to process campaign ${campaignName}`, {
          error: err,
        });
        results.push({
          campaignId,
          campaignName,
          totalLeads: 0,
          updated: 0,
          bounced: 0,
          errors: 1,
        });
      }
    }

    const summary = {
      campaigns_processed: results.length,
      total_leads: results.reduce((s, r) => s + r.totalLeads, 0),
      total_updated: results.reduce((s, r) => s + r.updated, 0),
      total_bounced: results.reduce((s, r) => s + r.bounced, 0),
      total_errors: results.reduce((s, r) => s + r.errors, 0),
      campaign_results: results,
    };

    logger.info("Smartlead → Supabase sync completed", summary);
    return summary;
  },
});
