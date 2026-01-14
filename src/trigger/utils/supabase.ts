import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { logger } from "@trigger.dev/sdk/v3";

// TypeScript types for our schema
export interface Lead {
  id: string;
  email: string;
  place_id?: string | null;
  smartlead_lead_id?: number | null;
  first_name?: string | null;
  last_name?: string | null;
  company?: string | null;
  domain?: string | null;
  site?: string | null;
  phone?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  reviews_count?: number | null;
  service_software?: string | null;
  score?: number | null;
  tier?: "A" | "B" | "C" | null;
  messaging_strategy?: string | null;
  score_breakdown?: Record<string, any> | null;
  in_smartlead?: boolean | null;
  smartlead_campaign_ids?: number[] | null;
  enriched_at?: string | null;
  last_smartlead_sync?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface OutscraperInsert {
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
}

// Database singleton
class SupabaseService {
  private client: SupabaseClient | null = null;

  getClient(): SupabaseClient {
    if (!this.client) {
      const url = process.env.SUPABASE_URL;
      const key = process.env.SUPABASE_SERVICE_KEY;

      if (!url || !key) {
        throw new Error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY");
      }

      this.client = createClient(url, key);
      logger.info("Supabase client initialized");
    }

    return this.client;
  }

  // Insert leads from Outscraper, skip duplicates by place_id
  async insertLeads(leads: OutscraperInsert[]): Promise<{
    inserted: number;
    skipped: number;
    errors: number;
  }> {
    const supabase = this.getClient();
    let inserted = 0;
    let skipped = 0;
    let errors = 0;

    for (const lead of leads) {
      try {
        // Check if place_id already exists
        const { data: existing } = await supabase
          .from("leads")
          .select("id, place_id")
          .eq("place_id", lead.place_id)
          .single();

        if (existing) {
          logger.info(`Skipping duplicate place_id: ${lead.place_id}`);
          skipped++;
          continue;
        }

        // Insert new lead (email will be auto-lowercased by DB)
        const { error } = await supabase.from("leads").insert({
          email: lead.email.toLowerCase().trim(),
          place_id: lead.place_id,
          first_name: lead.first_name,
          last_name: lead.last_name,
          company: lead.company,
          site: lead.site,
          phone: lead.phone,
          city: lead.city,
          state: lead.state,
          postal_code: lead.postal_code,
          reviews_count: lead.reviews_count,
        });

        if (error) {
          logger.error("Insert error", { error, place_id: lead.place_id });
          errors++;
        } else {
          inserted++;
        }
      } catch (err) {
        logger.error("Unexpected error inserting lead", {
          error: err,
          place_id: lead.place_id,
        });
        errors++;
      }
    }

    return { inserted, skipped, errors };
  }

  // Get leads that need enrichment (no service_software, has website)
  async getLeadsForEnrichment(limit: number = 50): Promise<Lead[]> {
    const supabase = this.getClient();

    const { data, error } = await supabase
      .from("leads")
      .select("*")
      .is("enriched_at", null)
      .not("site", "is", null)
      .limit(limit);

    if (error) {
      throw new Error(`Failed to fetch leads for enrichment: ${error.message}`);
    }

    return data || [];
  }

  // Update lead with enrichment result
  async updateEnrichment(
    leadId: string,
    serviceSoftware: string | null
  ): Promise<void> {
    const supabase = this.getClient();

    const { error } = await supabase
      .from("leads")
      .update({
        service_software: serviceSoftware,
        enriched_at: new Date().toISOString(),
      })
      .eq("id", leadId);

    if (error) {
      throw new Error(`Failed to update enrichment: ${error.message}`);
    }
  }

  // Get leads that need scoring (enriched but not scored)
  async getLeadsForScoring(limit: number = 100): Promise<Lead[]> {
    const supabase = this.getClient();

    const { data, error } = await supabase
      .from("leads")
      .select("*")
      .not("enriched_at", "is", null)
      .is("tier", null)
      .limit(limit);

    if (error) {
      throw new Error(`Failed to fetch leads for scoring: ${error.message}`);
    }

    return data || [];
  }

  // Update lead with score and tier
  async updateScore(
    leadId: string,
    score: number,
    tier: "A" | "B" | "C",
    breakdown: Record<string, any>
  ): Promise<void> {
    const supabase = this.getClient();

    const { error } = await supabase
      .from("leads")
      .update({
        score,
        tier,
        score_breakdown: breakdown,
      })
      .eq("id", leadId);

    if (error) {
      throw new Error(`Failed to update score: ${error.message}`);
    }
  }

  // Get leads ready for Smartlead sync (scored but not synced)
  async getLeadsForSmartlead(tier: "A" | "B" | "C", limit: number = 100): Promise<Lead[]> {
    const supabase = this.getClient();

    const { data, error } = await supabase
      .from("leads")
      .select("*")
      .eq("tier", tier)
      .eq("in_smartlead", false)
      .limit(limit);

    if (error) {
      throw new Error(`Failed to fetch leads for Smartlead: ${error.message}`);
    }

    return data || [];
  }

  // Update lead after Smartlead sync
  async updateSmartleadSync(
    leadId: string,
    smartleadLeadId: number,
    campaignId: number
  ): Promise<void> {
    const supabase = this.getClient();

    const { error } = await supabase
      .from("leads")
      .update({
        smartlead_lead_id: smartleadLeadId,
        in_smartlead: true,
        smartlead_campaign_ids: [campaignId],
        last_smartlead_sync: new Date().toISOString(),
      })
      .eq("id", leadId);

    if (error) {
      throw new Error(`Failed to update Smartlead sync: ${error.message}`);
    }
  }
}

// Export singleton instance
export const supabaseService = new SupabaseService();
