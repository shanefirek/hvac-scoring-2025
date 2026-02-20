import { logger, task, idempotencyKeys } from "@trigger.dev/sdk/v3";
import { z } from "zod";
import { apifyService, GoogleMapsPlace, ScrapedBusiness } from "./utils/apify";
import { supabaseService } from "./utils/supabase";

// ============================================================================
// Schemas
// ============================================================================

const LocationSchema = z.object({
  city: z.string().optional(),
  state: z.string(),
  zipCode: z.string().optional(),
});

const ScrapeLeadsPayloadSchema = z.object({
  // Locations to scrape - provide city/state pairs or zip codes
  locations: z.array(LocationSchema).min(1).max(50),
  // Max businesses to scrape per search query (default 100)
  maxPerQuery: z.number().min(10).max(500).default(100),
  // Whether to scrape websites for contact emails (adds time + cost)
  enrichEmails: z.boolean().default(true),
  // Batch size for email scraping (default 50)
  emailBatchSize: z.number().min(10).max(100).default(50),
  // Optional: skip deduplication check (for testing)
  skipDedupe: z.boolean().default(false),
});

export type ScrapeLeadsPayload = z.infer<typeof ScrapeLeadsPayloadSchema>;

// ============================================================================
// Main Orchestrator Task
// ============================================================================

/**
 * Main orchestrator for HVAC lead scraping pipeline
 *
 * Flow:
 * 1. Build search queries from locations
 * 2. Scrape Google Maps for HVAC businesses
 * 3. Extract websites and scrape for contact emails
 * 4. Deduplicate against existing leads in Supabase
 * 5. Insert new leads
 *
 * Usage:
 * ```ts
 * import { tasks } from "@trigger.dev/sdk/v3";
 * import type { scrapeHVACLeads } from "./trigger/apify-lead-scrape";
 *
 * await tasks.trigger<typeof scrapeHVACLeads>("leads.scrape.hvac", {
 *   locations: [
 *     { city: "Boston", state: "MA" },
 *     { city: "Hartford", state: "CT" },
 *     { state: "RI" }, // entire state
 *   ],
 *   maxPerQuery: 100,
 *   enrichEmails: true,
 * });
 * ```
 */
export const scrapeHVACLeads = task({
  id: "leads.scrape.hvac",
  maxDuration: 3600, // 1 hour max
  retry: {
    maxAttempts: 2,
    minTimeoutInMs: 30000,
    maxTimeoutInMs: 120000,
    factor: 2,
  },
  run: async (payload: ScrapeLeadsPayload) => {
    // Validate payload
    const validatedPayload = ScrapeLeadsPayloadSchema.parse(payload);
    const { locations, maxPerQuery, enrichEmails, emailBatchSize, skipDedupe } = validatedPayload;

    logger.info("Starting HVAC lead scraping pipeline", {
      locationCount: locations.length,
      maxPerQuery,
      enrichEmails,
    });

    const startTime = Date.now();
    const results = {
      searchQueries: 0,
      placesScraped: 0,
      websitesScraped: 0,
      emailsFound: 0,
      existingLeads: 0,
      newLeadsInserted: 0,
      errors: [] as string[],
    };

    try {
      // ========================================================================
      // Step 1: Scrape Google Maps
      // ========================================================================
      logger.info("Step 1: Scraping Google Maps for HVAC businesses");

      const idempotencyKeyMaps = await idempotencyKeys.create("google-maps-scrape");
      const mapsResult = await scrapeGoogleMapsTask.triggerAndWait(
        {
          locations,
          maxPerQuery,
        },
        { idempotencyKey: idempotencyKeyMaps }
      );

      if (!mapsResult.ok) {
        throw new Error(`Google Maps scrape failed: ${String(mapsResult.error)}`);
      }

      const places = mapsResult.output.places;
      results.searchQueries = mapsResult.output.queriesExecuted;
      results.placesScraped = places.length;

      logger.info("Google Maps scrape completed", {
        queriesExecuted: results.searchQueries,
        placesFound: results.placesScraped,
      });

      if (places.length === 0) {
        logger.warn("No places found, stopping pipeline");
        return { ...results, duration_seconds: Math.round((Date.now() - startTime) / 1000) };
      }

      // ========================================================================
      // Step 2: Enrich with emails (optional)
      // ========================================================================
      let businesses: ScrapedBusiness[];

      if (enrichEmails) {
        logger.info("Step 2: Scraping websites for contact emails");

        // Extract unique websites
        const websites = [...new Set(
          places
            .map((p) => p.website)
            .filter((w): w is string => !!w)
        )];

        logger.info(`Found ${websites.length} unique websites to scrape`);

        const idempotencyKeyEmails = await idempotencyKeys.create("email-scrape");
        const emailResult = await scrapeEmailsTask.triggerAndWait(
          {
            websites,
            batchSize: emailBatchSize,
          },
          { idempotencyKey: idempotencyKeyEmails }
        );

        if (!emailResult.ok) {
          logger.error("Email scraping failed, continuing with places only", {
            error: String(emailResult.error),
          });
          businesses = places.map(placeToScrapedBusiness);
        } else {
          results.websitesScraped = emailResult.output.websitesProcessed;
          results.emailsFound = emailResult.output.emailsFound;

          // Combine places with email results
          businesses = apifyService.combineResults(places, emailResult.output.contactMap);
        }
      } else {
        logger.info("Step 2: Skipping email enrichment (disabled)");
        businesses = places.map(placeToScrapedBusiness);
      }

      // ========================================================================
      // Step 3: Deduplicate and insert
      // ========================================================================
      logger.info("Step 3: Deduplicating and inserting leads");

      const idempotencyKeyInsert = await idempotencyKeys.create("insert-leads");
      const insertResult = await insertLeadsTask.triggerAndWait(
        {
          businesses,
          skipDedupe,
        },
        { idempotencyKey: idempotencyKeyInsert }
      );

      if (!insertResult.ok) {
        throw new Error(`Lead insertion failed: ${String(insertResult.error)}`);
      }

      results.existingLeads = insertResult.output.duplicatesSkipped;
      results.newLeadsInserted = insertResult.output.inserted;

      // ========================================================================
      // Final Summary
      // ========================================================================
      const durationSeconds = Math.round((Date.now() - startTime) / 1000);

      const summary = {
        ...results,
        duration_seconds: durationSeconds,
        duration_minutes: Math.round(durationSeconds / 60),
        locations_processed: locations.length,
        conversion_rate: results.placesScraped > 0
          ? `${((results.newLeadsInserted / results.placesScraped) * 100).toFixed(1)}%`
          : "0%",
      };

      logger.info("HVAC lead scraping pipeline completed", summary);

      return summary;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      results.errors.push(errorMessage);
      logger.error("Pipeline failed", { error: errorMessage, results });
      throw error;
    }
  },
});

// ============================================================================
// Subtask: Google Maps Scraping
// ============================================================================

// Type for location that matches what we pass to the task
type LocationInput = { city?: string; state: string; zipCode?: string };

const scrapeGoogleMapsTask = task({
  id: "leads.scrape.google-maps",
  maxDuration: 1800, // 30 minutes
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 60000,
    maxTimeoutInMs: 300000,
    factor: 2,
  },
  run: async (payload: { locations: LocationInput[]; maxPerQuery: number }) => {
    const { locations, maxPerQuery } = payload;

    // Build search queries
    const queries = apifyService.buildHVACSearchQueries(locations);
    logger.info(`Built ${queries.length} search queries from ${locations.length} locations`);

    // Execute Google Maps scrape
    const places = await apifyService.scrapeGoogleMaps({
      searchQueries: queries,
      maxResultsPerQuery: maxPerQuery,
      language: "en",
      countryCode: "us",
    });

    // Dedupe by placeId (in case multiple queries return same business)
    const uniquePlaces = deduplicatePlaces(places);

    logger.info("Google Maps scrape completed", {
      queriesExecuted: queries.length,
      rawResults: places.length,
      uniquePlaces: uniquePlaces.length,
    });

    return {
      places: uniquePlaces,
      queriesExecuted: queries.length,
    };
  },
});

// ============================================================================
// Subtask: Email Scraping
// ============================================================================

const scrapeEmailsTask = task({
  id: "leads.scrape.emails",
  maxDuration: 1800, // 30 minutes
  retry: {
    maxAttempts: 2,
    minTimeoutInMs: 30000,
    maxTimeoutInMs: 120000,
    factor: 2,
  },
  run: async (payload: { websites: string[]; batchSize: number }) => {
    const { websites, batchSize } = payload;

    if (websites.length === 0) {
      return {
        websitesProcessed: 0,
        emailsFound: 0,
        contactMap: new Map(),
      };
    }

    logger.info(`Scraping ${websites.length} websites for contacts`, { batchSize });

    // Process in batches
    const contactMap = await apifyService.scrapeContactInfoBatched(websites, batchSize);

    // Count total emails found
    let emailsFound = 0;
    for (const result of contactMap.values()) {
      emailsFound += result.emails?.length || 0;
    }

    logger.info("Email scraping completed", {
      websitesProcessed: websites.length,
      domainsWithResults: contactMap.size,
      emailsFound,
    });

    return {
      websitesProcessed: websites.length,
      emailsFound,
      contactMap,
    };
  },
});

// ============================================================================
// Subtask: Lead Insertion with Deduplication
// ============================================================================

const insertLeadsTask = task({
  id: "leads.insert.batch",
  maxDuration: 600, // 10 minutes
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 5000,
    maxTimeoutInMs: 30000,
    factor: 2,
  },
  run: async (payload: { businesses: ScrapedBusiness[]; skipDedupe: boolean }) => {
    const { businesses, skipDedupe } = payload;

    logger.info(`Processing ${businesses.length} businesses for insertion`);

    let inserted = 0;
    let duplicatesSkipped = 0;
    let noEmailSkipped = 0;
    let errors = 0;

    const supabase = supabaseService.getClient();

    // Get existing place_ids for deduplication
    let existingPlaceIds = new Set<string>();
    let existingEmails = new Set<string>();

    if (!skipDedupe) {
      // Fetch existing place_ids
      const { data: existingByPlaceId } = await supabase
        .from("leads")
        .select("place_id")
        .not("place_id", "is", null);

      existingPlaceIds = new Set(
        (existingByPlaceId || []).map((r) => r.place_id).filter(Boolean)
      );

      // Fetch existing emails
      const { data: existingByEmail } = await supabase
        .from("leads")
        .select("email");

      existingEmails = new Set(
        (existingByEmail || []).map((r) => r.email.toLowerCase())
      );

      logger.info("Deduplication check", {
        existingPlaceIds: existingPlaceIds.size,
        existingEmails: existingEmails.size,
      });
    }

    // Process each business
    for (const business of businesses) {
      try {
        // Skip if no email (required for our lead table)
        const primaryEmail = business.emails[0]?.toLowerCase().trim();
        if (!primaryEmail) {
          noEmailSkipped++;
          continue;
        }

        // Skip if place_id already exists
        if (!skipDedupe && existingPlaceIds.has(business.placeId)) {
          duplicatesSkipped++;
          continue;
        }

        // Skip if email already exists
        if (!skipDedupe && existingEmails.has(primaryEmail)) {
          duplicatesSkipped++;
          continue;
        }

        // Insert the lead
        const { error } = await supabase.from("leads").insert({
          email: primaryEmail,
          place_id: business.placeId,
          company: business.businessName,
          site: business.website,
          phone_number: business.phone,
          city: business.city,
          state: business.state,
          postal_code: business.postalCode,
          reviews_count: business.reviewsCount,
          // LinkedIn from contact scraper (first one if available)
          linkedin_url: business.linkedInUrls?.[0],
          // Mark source for tracking
          data_source_priority: {
            source: "apify_scrape",
            scraped_at: new Date().toISOString(),
          },
        });

        if (error) {
          // Check if it's a unique constraint violation
          if (error.code === "23505") {
            duplicatesSkipped++;
          } else {
            logger.error("Insert error", { error, placeId: business.placeId });
            errors++;
          }
        } else {
          inserted++;
          // Add to tracking sets to avoid duplicates in same batch
          existingPlaceIds.add(business.placeId);
          existingEmails.add(primaryEmail);
        }
      } catch (err) {
        logger.error("Unexpected error inserting business", {
          error: err,
          placeId: business.placeId,
        });
        errors++;
      }
    }

    const summary = {
      total: businesses.length,
      inserted,
      duplicatesSkipped,
      noEmailSkipped,
      errors,
    };

    logger.info("Lead insertion completed", summary);

    return summary;
  },
});

// ============================================================================
// Helper Functions
// ============================================================================

function deduplicatePlaces(places: GoogleMapsPlace[]): GoogleMapsPlace[] {
  const seen = new Set<string>();
  const unique: GoogleMapsPlace[] = [];

  for (const place of places) {
    if (!seen.has(place.placeId)) {
      seen.add(place.placeId);
      unique.push(place);
    }
  }

  return unique;
}

function placeToScrapedBusiness(place: GoogleMapsPlace): ScrapedBusiness {
  return {
    placeId: place.placeId,
    businessName: place.title,
    address: place.address,
    city: place.city,
    state: place.state,
    postalCode: place.postalCode,
    phone: place.phone,
    website: place.website,
    rating: place.totalScore,
    reviewsCount: place.reviewsCount,
    emails: [], // No emails without enrichment
  };
}
