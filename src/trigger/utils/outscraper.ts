import axios from "axios";
import { logger, wait } from "@trigger.dev/sdk/v3";

export interface OutscraperPlace {
  name: string;
  place_id: string;
  site?: string;
  phone?: string;
  full_address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  rating?: number;
  reviews?: number;
  emails?: string[];
}

export interface OutscraperResponse {
  id: string;
  status: "Pending" | "Success" | "Error";
  data?: OutscraperPlace[][];
}

class OutscraperService {
  private apiKey: string;
  private baseUrl = "https://api.app.outscraper.com";

  constructor() {
    const key = process.env.OUTSCRAPER_API_KEY;
    if (!key) {
      throw new Error("Missing OUTSCRAPER_API_KEY");
    }
    this.apiKey = key;
  }

  /**
   * Scrape Google Maps for HVAC contractors in a state
   * Returns request ID for polling
   */
  async scrapeHVAC(state: string, limit: number = 100): Promise<string> {
    const query = `HVAC contractors in ${state}`;

    logger.info(`Starting Outscraper scrape`, { query, limit });

    const response = await axios.post(
      `${this.baseUrl}/maps/search-v3`,
      {
        query: [query],
        limit,
        language: "en",
        region: "us",
        enrichments: ["emails", "contacts"],
      },
      {
        headers: {
          "X-API-KEY": this.apiKey,
          "Content-Type": "application/json",
        },
      }
    );

    const requestId = response.data.id;
    logger.info(`Outscraper request created`, { requestId, query });

    return requestId;
  }

  /**
   * Poll for scrape results (Outscraper is async)
   * Retries every 10 seconds, max 5 minutes
   */
  async pollResults(
    requestId: string,
    maxAttempts: number = 30
  ): Promise<OutscraperPlace[]> {
    logger.info(`Polling Outscraper results`, { requestId });

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const response = await axios.get<OutscraperResponse>(
        `${this.baseUrl}/requests/${requestId}`,
        {
          headers: {
            "X-API-KEY": this.apiKey,
          },
        }
      );

      const { status, data } = response.data;

      logger.info(`Poll attempt ${attempt}/${maxAttempts}`, {
        requestId,
        status,
      });

      if (status === "Success") {
        // Outscraper returns nested arrays [[places]]
        const places = data?.[0] || [];
        logger.info(`Scrape completed`, { requestId, count: places.length });
        return places;
      }

      if (status === "Error") {
        throw new Error(`Outscraper request failed: ${requestId}`);
      }

      // Still pending, wait 10 seconds
      if (attempt < maxAttempts) {
        await wait.for({ seconds: 10 });
      }
    }

    throw new Error(
      `Outscraper polling timeout after ${maxAttempts} attempts`
    );
  }

  /**
   * Full scrape workflow: initiate + poll
   */
  async scrapeAndWait(
    state: string,
    limit: number = 100
  ): Promise<OutscraperPlace[]> {
    const requestId = await this.scrapeHVAC(state, limit);
    const results = await this.pollResults(requestId);
    return results;
  }

  /**
   * Parse Outscraper place into our lead format
   */
  parsePlace(place: OutscraperPlace): {
    email: string;
    place_id: string;
    first_name?: string;
    last_name?: string;
    company: string;
    site?: string;
    phone?: string;
    city?: string;
    state?: string;
    postal_code?: string;
    reviews_count?: number;
  } | null {
    // Must have email to be useful
    const email = place.emails?.[0];
    if (!email) {
      logger.warn(`Skipping place without email`, { place_id: place.place_id });
      return null;
    }

    // Extract name parts (basic heuristic)
    let firstName: string | undefined;
    let lastName: string | undefined;

    // If name has comma, assume "Last, First" format
    if (place.name.includes(",")) {
      const parts = place.name.split(",").map((p) => p.trim());
      lastName = parts[0];
      firstName = parts[1];
    }

    return {
      email,
      place_id: place.place_id,
      first_name: firstName,
      last_name: lastName,
      company: place.name,
      site: place.site,
      phone: place.phone,
      city: place.city,
      state: place.state,
      postal_code: place.postal_code,
      reviews_count: place.reviews,
    };
  }
}

export const outscraperService = new OutscraperService();
