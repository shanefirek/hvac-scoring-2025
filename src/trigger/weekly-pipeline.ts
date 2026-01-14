import { logger, schedules } from "@trigger.dev/sdk/v3";
import { weeklyScrapeTask } from "./weekly-scrape";
import { enrichLeadsTask } from "./enrich-leads";
import { scoreLeadsTask } from "./score-leads";
import { syncToSmartleadTask } from "./sync-to-smartlead";

/**
 * Weekly lead pipeline orchestrator
 * Runs every Sunday at 2 AM Eastern (7 AM UTC)
 * Chains: scrape → enrich → score → sync
 */
export const weeklyPipeline = schedules.task({
  id: "weekly-pipeline",
  cron: "0 7 * * 0", // Sundays at 7 AM UTC (2 AM ET)
  maxDuration: 3600, // 1 hour max
  run: async (payload) => {
    logger.info("🚀 Starting weekly lead pipeline");

    const startTime = Date.now();
    const results: Record<string, any> = {};

    try {
      // Step 1: Scrape fresh leads from Outscraper
      logger.info("Step 1/4: Scraping leads from Outscraper");

      const scrapeResult = await weeklyScrapeTask.triggerAndWait({
        states: [
          "Connecticut",
          "Maine",
          "Massachusetts",
          "New Hampshire",
          "Rhode Island",
          "Vermont",
          "New York",
          "New Jersey",
          "Pennsylvania",
        ],
        limitPerState: 200, // 200 per state = ~1800 total
      });

      results.scrape = scrapeResult.output;
      logger.info("✅ Scrape completed", results.scrape);

      // Step 2: Enrich leads (detect software)
      logger.info("Step 2/4: Enriching leads with software detection");

      // Process in batches of 50 until no more leads need enrichment
      let enrichmentBatches = 0;
      let totalEnriched = 0;

      while (enrichmentBatches < 60) { // Max 60 batches = 3000 leads
        const enrichResult = await enrichLeadsTask.triggerAndWait({
          batchSize: 50,
        });

        totalEnriched += enrichResult.output?.enriched || 0;
        enrichmentBatches++;

        // Stop if we processed fewer than batch size (no more leads)
        if ((enrichResult.output?.leads_processed || 0) < 50) {
          break;
        }
      }

      results.enrich = {
        batches: enrichmentBatches,
        total_enriched: totalEnriched,
      };
      logger.info("✅ Enrichment completed", results.enrich);

      // Step 3: Score enriched leads
      logger.info("Step 3/4: Scoring leads");

      // Process in batches of 100 until no more leads need scoring
      let scoringBatches = 0;
      let totalScored = 0;

      while (scoringBatches < 30) { // Max 30 batches = 3000 leads
        const scoreResult = await scoreLeadsTask.triggerAndWait({
          batchSize: 100,
        });

        totalScored += scoreResult.output?.scored || 0;
        scoringBatches++;

        // Stop if we processed fewer than batch size
        if ((scoreResult.output?.leads_processed || 0) < 100) {
          break;
        }
      }

      results.score = {
        batches: scoringBatches,
        total_scored: totalScored,
      };
      logger.info("✅ Scoring completed", results.score);

      // Step 4: Sync to Smartlead campaigns
      logger.info("Step 4/4: Syncing to Smartlead");

      const syncResult = await syncToSmartleadTask.triggerAndWait({
        batchSize: 100, // Process up to 100 per tier
      });

      results.sync = syncResult.output;
      logger.info("✅ Sync completed", results.sync);

      // Final summary
      const duration = Math.round((Date.now() - startTime) / 1000);
      const summary = {
        pipeline: "weekly-lead-pipeline",
        duration_seconds: duration,
        duration_minutes: Math.round(duration / 60),
        steps: results,
        timestamp: new Date().toISOString(),
      };

      logger.info("🎉 Weekly pipeline completed successfully", summary);

      return summary;
    } catch (error) {
      logger.error("❌ Weekly pipeline failed", { error, results });
      throw error;
    }
  },
});
