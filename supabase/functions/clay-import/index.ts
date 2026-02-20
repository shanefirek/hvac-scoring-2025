import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

interface ClayLead {
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  domain?: string;
  phone_number?: string;
  city?: string;
  state?: string;
  location?: string;
  linkedin_url?: string;
  business_type?: string;
  // Clay can send any additional fields
  [key: string]: unknown;
}

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const payload = await req.json();
    console.log("Received Clay payload:", JSON.stringify(payload, null, 2));

    // Handle both single lead and array of leads
    const leads: ClayLead[] = Array.isArray(payload) ? payload : [payload];

    if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
      throw new Error("Supabase credentials not configured");
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

    const results = {
      inserted: 0,
      updated: 0,
      skipped: 0,
      errors: [] as string[],
    };

    for (const lead of leads) {
      // Skip if no email
      if (!lead.email) {
        results.skipped++;
        results.errors.push("Missing email");
        continue;
      }

      const email = lead.email.toLowerCase().trim();

      // Build the lead record
      const leadRecord = {
        email,
        first_name: lead.first_name || null,
        last_name: lead.last_name || null,
        company: lead.company || null,
        domain: lead.domain || null,
        phone_number: lead.phone_number || null,
        city: lead.city || null,
        state: lead.state || null,
        location: lead.location || null,
        linkedin_url: lead.linkedin_url || null,
        business_type: lead.business_type || "marketing_agency",
        clay_data: lead, // Store full Clay payload
        updated_at: new Date().toISOString(),
        last_enriched_at: new Date().toISOString(),
      };

      // Upsert - insert or update on email conflict
      const { data, error } = await supabase
        .from("leads")
        .upsert(leadRecord, {
          onConflict: "email",
          ignoreDuplicates: false,
        })
        .select();

      if (error) {
        console.error("Error upserting lead:", email, error);
        results.errors.push(`${email}: ${error.message}`);
      } else {
        // Check if it was insert or update based on created_at
        results.inserted++;
      }
    }

    console.log("Import results:", results);

    return new Response(
      JSON.stringify({
        success: true,
        message: `Processed ${leads.length} leads`,
        results,
      }),
      {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  } catch (error) {
    console.error("Error processing Clay import:", error);
    return new Response(
      JSON.stringify({ success: false, error: String(error) }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  }
});
