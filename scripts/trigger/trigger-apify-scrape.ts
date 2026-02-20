/**
 * Example script showing how to trigger the Apify lead scraping task
 *
 * Usage:
 *   npx ts-node scripts/trigger/trigger-apify-scrape.ts
 *
 * Or from a Next.js API route, Node.js server, etc.
 */

import { tasks, runs } from "@trigger.dev/sdk/v3";
// Type-only import to avoid bundling task dependencies
import type { scrapeHVACLeads } from "../../src/trigger/apify-lead-scrape";

async function main() {
  console.log("Triggering HVAC lead scrape...");

  // Example 1: Scrape specific cities
  const handle = await tasks.trigger<typeof scrapeHVACLeads>("leads.scrape.hvac", {
    locations: [
      { city: "Boston", state: "MA" },
      { city: "Worcester", state: "MA" },
      { city: "Hartford", state: "CT" },
      { city: "Providence", state: "RI" },
    ],
    maxPerQuery: 100,
    enrichEmails: true,
    emailBatchSize: 50,
  });

  console.log(`Task triggered! Run ID: ${handle.id}`);
  console.log(`View at: https://cloud.trigger.dev/runs/${handle.id}`);

  // Optional: Wait for completion and get results
  const run = await runs.poll(handle.id, {
    pollIntervalMs: 10000, // Check every 10 seconds
  });

  if (run.status === "COMPLETED") {
    console.log("Task completed successfully!");
    console.log("Results:", JSON.stringify(run.output, null, 2));
  } else {
    console.error("Task failed:", run.status);
  }
}

// Example 2: Scrape entire states
async function scrapeStates() {
  const handle = await tasks.trigger<typeof scrapeHVACLeads>("leads.scrape.hvac", {
    locations: [
      { state: "Connecticut" },
      { state: "Rhode Island" },
      { state: "Vermont" },
    ],
    maxPerQuery: 200, // More results per query for state-wide searches
    enrichEmails: true,
  });

  return handle;
}

// Example 3: Scrape by zip codes
async function scrapeZipCodes() {
  const handle = await tasks.trigger<typeof scrapeHVACLeads>("leads.scrape.hvac", {
    locations: [
      { zipCode: "02101", state: "MA" }, // Boston
      { zipCode: "02139", state: "MA" }, // Cambridge
      { zipCode: "06103", state: "CT" }, // Hartford
    ],
    maxPerQuery: 50, // Smaller results for specific zip codes
    enrichEmails: true,
  });

  return handle;
}

// Example 4: Quick scrape without email enrichment (faster, cheaper)
async function quickScrape() {
  const handle = await tasks.trigger<typeof scrapeHVACLeads>("leads.scrape.hvac", {
    locations: [
      { city: "Boston", state: "MA" },
    ],
    maxPerQuery: 50,
    enrichEmails: false, // Skip email scraping
  });

  return handle;
}

// Run the main example
main().catch(console.error);
