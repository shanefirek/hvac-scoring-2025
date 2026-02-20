import { logger, wait } from "@trigger.dev/sdk/v3";

// ============================================================================
// Types
// ============================================================================

export interface ApifyRunResponse {
  id: string;
  status: "READY" | "RUNNING" | "SUCCEEDED" | "FAILED" | "ABORTING" | "ABORTED" | "TIMED-OUT";
  defaultDatasetId: string;
}

export interface GoogleMapsPlace {
  placeId: string;
  title: string;
  address: string;
  street?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  countryCode?: string;
  phone?: string;
  website?: string;
  categoryName?: string;
  totalScore?: number;
  reviewsCount?: number;
  imageUrl?: string;
  url?: string;
}

export interface ApifyEmailResult {
  domain: string;
  emails: string[];
  phones?: string[];
  linkedIns?: string[];
  twitters?: string[];
  facebooks?: string[];
  instagrams?: string[];
}

export interface ScrapedBusiness {
  placeId: string;
  businessName: string;
  address: string;
  city?: string;
  state?: string;
  postalCode?: string;
  phone?: string;
  website?: string;
  rating?: number;
  reviewsCount?: number;
  emails: string[];
  linkedInUrls?: string[];
}

// ============================================================================
// Apify Client Service
// ============================================================================

class ApifyService {
  private apiToken: string;
  private baseUrl = "https://api.apify.com/v2";

  // Actor IDs for the scrapers we use
  private readonly GOOGLE_MAPS_SCRAPER = "nwua9Gu5YrADL7ZDj"; // compass/crawler-google-places
  private readonly EMAIL_SCRAPER = "xMc5Ga1oCONPmeWKs"; // apify/contact-info-scraper

  constructor() {
    const token = process.env.APIFY_API_TOKEN;
    if (!token) {
      throw new Error("Missing APIFY_API_TOKEN environment variable");
    }
    this.apiToken = token;
  }

  // ============================================================================
  // Core API Methods
  // ============================================================================

  /**
   * Start an Apify actor run
   */
  async startActor(actorId: string, input: Record<string, unknown>): Promise<ApifyRunResponse> {
    const url = `${this.baseUrl}/acts/${actorId}/runs?token=${this.apiToken}`;

    logger.info("Starting Apify actor", { actorId, inputKeys: Object.keys(input) });

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Apify actor start failed: ${response.status} - ${errorText}`);
    }

    const data = (await response.json()) as { data: ApifyRunResponse };
    logger.info("Apify actor started", { runId: data.data.id, status: data.data.status });

    return data.data;
  }

  /**
   * Poll for actor run completion
   */
  async waitForRun(
    runId: string,
    maxWaitSeconds: number = 600,
    pollIntervalSeconds: number = 15
  ): Promise<ApifyRunResponse> {
    const maxAttempts = Math.ceil(maxWaitSeconds / pollIntervalSeconds);

    logger.info("Waiting for Apify run to complete", { runId, maxWaitSeconds });

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const url = `${this.baseUrl}/actor-runs/${runId}?token=${this.apiToken}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to check run status: ${response.status}`);
      }

      const data = (await response.json()) as { data: ApifyRunResponse };
      const { status } = data.data;

      logger.info(`Poll attempt ${attempt}/${maxAttempts}`, { runId, status });

      if (status === "SUCCEEDED") {
        return data.data;
      }

      if (status === "FAILED" || status === "ABORTED" || status === "TIMED-OUT") {
        throw new Error(`Apify run failed with status: ${status}`);
      }

      // Still running, wait before next poll
      if (attempt < maxAttempts) {
        await wait.for({ seconds: pollIntervalSeconds });
      }
    }

    throw new Error(`Apify run timed out after ${maxWaitSeconds} seconds`);
  }

  /**
   * Fetch results from a dataset
   */
  async getDatasetItems<T>(datasetId: string, limit: number = 1000): Promise<T[]> {
    const url = `${this.baseUrl}/datasets/${datasetId}/items?token=${this.apiToken}&limit=${limit}`;

    logger.info("Fetching dataset items", { datasetId, limit });

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch dataset: ${response.status}`);
    }

    const items = (await response.json()) as T[];
    logger.info("Dataset items fetched", { datasetId, count: items.length });

    return items;
  }

  // ============================================================================
  // Google Maps Scraper
  // ============================================================================

  /**
   * Scrape Google Maps for businesses
   * Uses compass/crawler-google-places actor
   */
  async scrapeGoogleMaps(options: {
    searchQueries: string[];
    maxResultsPerQuery?: number;
    language?: string;
    countryCode?: string;
  }): Promise<GoogleMapsPlace[]> {
    const {
      searchQueries,
      maxResultsPerQuery = 100,
      language = "en",
      countryCode = "us",
    } = options;

    // Build search URLs for the actor
    const searchStringsArray = searchQueries.map(
      (query) => `https://www.google.com/maps/search/${encodeURIComponent(query)}`
    );

    const input = {
      searchStringsArray,
      maxCrawledPlacesPerSearch: maxResultsPerQuery,
      language,
      countryCode,
      // Get detailed info including website
      scrapeWebsite: true,
      // Performance settings
      maxConcurrency: 10,
      maxPageRetries: 3,
    };

    const run = await this.startActor(this.GOOGLE_MAPS_SCRAPER, input);
    const completedRun = await this.waitForRun(run.id, 900); // 15 min max
    const results = await this.getDatasetItems<GoogleMapsPlace>(completedRun.defaultDatasetId);

    return results;
  }

  // ============================================================================
  // Email/Contact Scraper
  // ============================================================================

  /**
   * Scrape websites for contact information (emails, phones, social links)
   * Uses apify/contact-info-scraper actor
   */
  async scrapeContactInfo(websites: string[]): Promise<ApifyEmailResult[]> {
    if (websites.length === 0) {
      return [];
    }

    // Filter out invalid URLs
    const validUrls = websites.filter((url) => {
      try {
        new URL(url.startsWith("http") ? url : `https://${url}`);
        return true;
      } catch {
        return false;
      }
    });

    if (validUrls.length === 0) {
      logger.warn("No valid URLs to scrape for contacts");
      return [];
    }

    const input = {
      startUrls: validUrls.map((url) => ({
        url: url.startsWith("http") ? url : `https://${url}`,
      })),
      maxRequestsPerStartUrl: 10, // Crawl up to 10 pages per domain
      maxDepth: 2, // Follow links 2 levels deep
      sameDomain: true, // Stay on same domain
    };

    const run = await this.startActor(this.EMAIL_SCRAPER, input);
    const completedRun = await this.waitForRun(run.id, 600); // 10 min max
    const results = await this.getDatasetItems<ApifyEmailResult>(completedRun.defaultDatasetId);

    return results;
  }

  // ============================================================================
  // Batch Processing Helpers
  // ============================================================================

  /**
   * Process websites in batches for email scraping
   * Helps avoid rate limits and manage costs
   */
  async scrapeContactInfoBatched(
    websites: string[],
    batchSize: number = 50
  ): Promise<Map<string, ApifyEmailResult>> {
    const results = new Map<string, ApifyEmailResult>();
    const batches = this.chunkArray(websites, batchSize);

    logger.info(`Processing ${websites.length} websites in ${batches.length} batches`);

    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      logger.info(`Processing batch ${i + 1}/${batches.length}`, { size: batch.length });

      try {
        const batchResults = await this.scrapeContactInfo(batch);

        // Map results by domain for easy lookup
        for (const result of batchResults) {
          if (result.domain) {
            results.set(result.domain.toLowerCase(), result);
          }
        }

        // Small delay between batches to be nice to Apify
        if (i < batches.length - 1) {
          await wait.for({ seconds: 5 });
        }
      } catch (error) {
        logger.error(`Batch ${i + 1} failed`, { error });
        // Continue with remaining batches
      }
    }

    return results;
  }

  /**
   * Build search queries for HVAC businesses
   */
  buildHVACSearchQueries(locations: Array<{ city?: string; state: string; zipCode?: string }>): string[] {
    const queries: string[] = [];

    for (const loc of locations) {
      let locationStr: string;

      if (loc.zipCode) {
        locationStr = loc.zipCode;
      } else if (loc.city && loc.state) {
        locationStr = `${loc.city}, ${loc.state}`;
      } else {
        locationStr = loc.state;
      }

      // Primary search terms for HVAC businesses
      queries.push(`HVAC contractors in ${locationStr}`);
      queries.push(`heating and cooling companies in ${locationStr}`);
      queries.push(`air conditioning repair ${locationStr}`);
    }

    return queries;
  }

  /**
   * Combine Google Maps results with email scraping results
   */
  combineResults(
    places: GoogleMapsPlace[],
    contactResults: Map<string, ApifyEmailResult>
  ): ScrapedBusiness[] {
    const businesses: ScrapedBusiness[] = [];

    for (const place of places) {
      // Extract domain from website
      let domain: string | undefined;
      if (place.website) {
        try {
          const url = new URL(
            place.website.startsWith("http") ? place.website : `https://${place.website}`
          );
          domain = url.hostname.replace(/^www\./, "").toLowerCase();
        } catch {
          // Invalid URL, skip domain extraction
        }
      }

      // Look up contact info by domain
      const contactInfo = domain ? contactResults.get(domain) : undefined;

      businesses.push({
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
        emails: contactInfo?.emails || [],
        linkedInUrls: contactInfo?.linkedIns,
      });
    }

    return businesses;
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}

// Export singleton instance
export const apifyService = new ApifyService();
