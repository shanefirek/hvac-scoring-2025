import { logger, task } from "@trigger.dev/sdk/v3";
import { outscraperService } from "./utils/outscraper";
import { supabaseService, OutscraperInsert } from "./utils/supabase";

export interface WeeklyScrapePayload {
  states: string[];
  limitPerState: number;
}

export const weeklyScrapeTask = task({
  id: "weekly-scrape",
  maxDuration: 1800, // 30 minutes
  retry: {
    maxAttempts: 2,
  },
  run: async (payload: WeeklyScrapePayload) => {
    const { states, limitPerState } = payload;

    logger.info("Starting weekly scrape", { states, limitPerState });

    let totalScraped = 0;
    let totalInserted = 0;
    let totalSkipped = 0;
    let totalErrors = 0;

    // Process each state sequentially
    for (const state of states) {
      logger.info(`Scraping state: ${state}`);

      try {
        // Step 1: Scrape Outscraper (async, will poll for results)
        const places = await outscraperService.scrapeAndWait(
          state,
          limitPerState
        );

        totalScraped += places.length;
        logger.info(`Scraped ${places.length} places from ${state}`);

        // Step 2: Parse and filter places (must have email)
        const leads: OutscraperInsert[] = [];
        for (const place of places) {
          const parsed = outscraperService.parsePlace(place);
          if (parsed) {
            leads.push(parsed);
          }
        }

        logger.info(`Parsed ${leads.length} leads with emails from ${state}`);

        // Step 3: Insert into Supabase (dedupes by place_id)
        if (leads.length > 0) {
          const result = await supabaseService.insertLeads(leads);

          totalInserted += result.inserted;
          totalSkipped += result.skipped;
          totalErrors += result.errors;

          logger.info(`State ${state} results`, {
            inserted: result.inserted,
            skipped: result.skipped,
            errors: result.errors,
          });
        }
      } catch (error) {
        logger.error(`Failed to scrape state: ${state}`, { error });
        // Continue to next state even if one fails
      }
    }

    const summary = {
      states_processed: states.length,
      total_scraped: totalScraped,
      total_inserted: totalInserted,
      total_skipped: totalSkipped,
      total_errors: totalErrors,
    };

    logger.info("Weekly scrape completed", summary);

    return summary;
  },
});
