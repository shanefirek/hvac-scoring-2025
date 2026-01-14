import axios from "axios";
import { logger } from "@trigger.dev/sdk/v3";

export interface SmartleadLead {
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  website?: string;
  phone_number?: string;
  location?: string;
  custom_fields?: Record<string, any>;
}

export interface SmartleadAddLeadResponse {
  lead_id: number;
  email: string;
  status: string;
}

class SmartleadService {
  private apiKey: string;
  private baseUrl = "https://server.smartlead.ai/api/v1";

  constructor() {
    const key = process.env.SMARTLEAD_API_KEY;
    if (!key) {
      throw new Error("Missing SMARTLEAD_API_KEY");
    }
    this.apiKey = key;
  }

  /**
   * Add a single lead to a Smartlead campaign
   */
  async addLead(
    campaignId: number,
    lead: SmartleadLead
  ): Promise<SmartleadAddLeadResponse> {
    logger.info(`Adding lead to Smartlead campaign ${campaignId}`, {
      email: lead.email,
    });

    try {
      const response = await axios.post(
        `${this.baseUrl}/campaigns/${campaignId}/leads`,
        {
          lead_list: [lead],
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
          params: {
            api_key: this.apiKey,
          },
        }
      );

      // Smartlead returns array of results
      const result = response.data[0];

      logger.info(`Lead added to Smartlead`, {
        lead_id: result.lead_id,
        email: result.email,
        campaign_id: campaignId,
      });

      return result;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        logger.error(`Smartlead API error`, {
          status: error.response?.status,
          data: error.response?.data,
          email: lead.email,
        });
      }
      throw error;
    }
  }

  /**
   * Add multiple leads to a campaign (batch operation)
   */
  async addLeadsBatch(
    campaignId: number,
    leads: SmartleadLead[]
  ): Promise<SmartleadAddLeadResponse[]> {
    logger.info(`Adding ${leads.length} leads to campaign ${campaignId}`);

    try {
      const response = await axios.post(
        `${this.baseUrl}/campaigns/${campaignId}/leads`,
        {
          lead_list: leads,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
          params: {
            api_key: this.apiKey,
          },
        }
      );

      logger.info(`Batch add completed`, {
        count: response.data.length,
        campaign_id: campaignId,
      });

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        logger.error(`Smartlead batch API error`, {
          status: error.response?.status,
          data: error.response?.data,
          lead_count: leads.length,
        });
      }
      throw error;
    }
  }

  /**
   * Get campaign ID for a tier
   */
  getCampaignIdForTier(tier: "A" | "B" | "C"): number {
    const envKey = `SMARTLEAD_CAMPAIGN_${tier}`;
    const campaignId = process.env[envKey];

    if (!campaignId) {
      throw new Error(`Missing env var: ${envKey}`);
    }

    return parseInt(campaignId, 10);
  }
}

export const smartleadService = new SmartleadService();
