import axios from "axios";
import { logger } from "@trigger.dev/sdk/v3";

export type ServiceSoftware = "ServiceTitan" | "Jobber" | "Housecall Pro";

/**
 * Detects field service management software from a website
 * Returns the detected software or null if none found
 */
export async function detectSoftware(
  url: string,
  timeoutMs: number = 10000
): Promise<ServiceSoftware | null> {
  try {
    logger.info(`Detecting software for URL: ${url}`);

    // Fetch website HTML with timeout
    const response = await axios.get(url, {
      timeout: timeoutMs,
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
      maxRedirects: 3,
    });

    const html = response.data.toLowerCase();

    // Detection patterns (order matters - check most specific first)
    const patterns: { software: ServiceSoftware; keywords: string[] }[] = [
      {
        software: "ServiceTitan",
        keywords: [
          "servicetitan.com",
          "servicetitan",
          "service titan",
          "st-widget",
          "stwidget",
        ],
      },
      {
        software: "Jobber",
        keywords: [
          "getjobber.com",
          "jobber.com",
          "jobber software",
          "jobber-widget",
          "powered by jobber",
        ],
      },
      {
        software: "Housecall Pro",
        keywords: [
          "housecallpro.com",
          "housecall pro",
          "housecallpro",
          "hcp-widget",
          "powered by housecall",
        ],
      },
    ];

    // Check each pattern
    for (const pattern of patterns) {
      for (const keyword of pattern.keywords) {
        if (html.includes(keyword)) {
          logger.info(`Detected ${pattern.software}`, { url, keyword });
          return pattern.software;
        }
      }
    }

    logger.info(`No software detected`, { url });
    return null;
  } catch (error) {
    // Log but don't throw - we want to continue processing other leads
    if (axios.isAxiosError(error)) {
      logger.warn(`Failed to fetch URL`, {
        url,
        status: error.response?.status,
        message: error.message,
      });
    } else {
      logger.warn(`Unexpected error detecting software`, { url, error });
    }

    return null;
  }
}

/**
 * Normalize URL to ensure it's fetchable
 */
export function normalizeUrl(url: string): string {
  let normalized = url.trim();

  // Add protocol if missing
  if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
    normalized = `https://${normalized}`;
  }

  // Remove trailing slash
  normalized = normalized.replace(/\/$/, "");

  return normalized;
}
