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

export interface SmartleadCampaignLead {
  id: number; // smartlead_lead_id
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  phone_number?: string;
  website?: string;
  location?: string;
  linkedin_profile?: string;
  status?: string; // COMPLETED, IN_PROGRESS, NOT_STARTED, BLOCKED
  lead_category?: string; // "Sender Originated Bounce", "Clicked", etc.
  open_count?: number;
  click_count?: number;
  reply_count?: number;
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
   * Fetch all leads from a Smartlead campaign with pagination
   */
  async getCampaignLeads(campaignId: number): Promise<SmartleadCampaignLead[]> {
    logger.info(`Fetching leads from Smartlead campaign ${campaignId}`);

    const allLeads: SmartleadCampaignLead[] = [];
    let offset = 0;
    const limit = 100;

    while (true) {
      try {
        const response = await axios.get(
          `${this.baseUrl}/campaigns/${campaignId}/leads`,
          {
            params: {
              api_key: this.apiKey,
              limit,
              offset,
            },
          }
        );

        const campaignLeads = response.data?.data || [];
        if (campaignLeads.length === 0) break;

        for (const item of campaignLeads) {
          const lead = item.lead;
          if (!lead) continue;

          allLeads.push({
            id: lead.id,
            email: lead.email,
            first_name: lead.first_name,
            last_name: lead.last_name,
            company_name: lead.company_name,
            phone_number: lead.phone_number,
            website: lead.website,
            location: lead.location,
            linkedin_profile: lead.linkedin_profile,
            status: item.status,
            lead_category: item.lead_category,
            open_count: item.open_count,
            click_count: item.click_count,
            reply_count: item.reply_count,
          });
        }

        logger.info(`Fetched ${campaignLeads.length} leads (total: ${allLeads.length})`);

        if (campaignLeads.length < limit) break;
        offset += limit;
      } catch (error) {
        if (axios.isAxiosError(error)) {
          logger.error(`Smartlead fetch error`, {
            status: error.response?.status,
            campaignId,
            offset,
          });
        }
        throw error;
      }
    }

    logger.info(`Total leads fetched from campaign ${campaignId}: ${allLeads.length}`);
    return allLeads;
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
