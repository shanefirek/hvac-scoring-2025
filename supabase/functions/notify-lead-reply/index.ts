import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
const PATRICK_EMAIL = "patrick@appletreebusiness.com";
const SHANE_EMAIL = "shanefirek@gmail.com";

interface SmartleadWebhook {
  event_type: string;
  lead_email: string;
  lead_name?: string;
  lead_first_name?: string;
  lead_last_name?: string;
  company_name?: string;
  campaign_name?: string;
  campaign_id?: number;
  reply_text?: string;
  reply_message?: string;
  email_body?: string;
  subject?: string;
  timestamp?: string;
  [key: string]: unknown;
}

async function sendEmail(to: string, subject: string, html: string) {
  if (!RESEND_API_KEY) {
    console.error("RESEND_API_KEY not configured");
    return { error: "Email not configured" };
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${RESEND_API_KEY}`,
    },
    body: JSON.stringify({
      from: "Appletree Leads <leads@updates.appletree-tax.com>",
      to: [to],
      subject: subject,
      html: html,
    }),
  });

  return res.json();
}

async function getLeadFromSupabase(email: string) {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) return null;

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

  const { data, error } = await supabase
    .from("leads")
    .select("*")
    .eq("email", email.toLowerCase())
    .single();

  if (error) {
    console.log("Lead not found in Supabase:", email);
    return null;
  }

  return data;
}

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  }

  try {
    const payload: SmartleadWebhook = await req.json();
    console.log("Received webhook:", JSON.stringify(payload, null, 2));

    // Extract reply content from various possible fields
    const replyContent = payload.reply_text || payload.reply_message || payload.email_body || "(No message content)";
    const leadEmail = payload.lead_email || "unknown";
    const leadName = payload.lead_name || payload.lead_first_name || "Unknown";
    const companyName = payload.company_name || "Unknown Company";
    const campaignName = payload.campaign_name || "Unknown Campaign";

    // Try to get more lead data from Supabase
    const supabaseLead = await getLeadFromSupabase(leadEmail);

    // Build enriched info
    const company = supabaseLead?.company || companyName;
    const phone = supabaseLead?.phone || "Not available";
    const city = supabaseLead?.city || "";
    const state = supabaseLead?.state || "";
    const location = city && state ? `${city}, ${state}` : (supabaseLead?.location || "Not available");
    const tier = supabaseLead?.tier || "Unknown";
    const domain = supabaseLead?.domain || "";

    // Format the email
    const emailHtml = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2563eb;">New Lead Reply</h2>

        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
          <h3 style="margin-top: 0;">Lead Info</h3>
          <p><strong>Name:</strong> ${leadName}</p>
          <p><strong>Email:</strong> <a href="mailto:${leadEmail}">${leadEmail}</a></p>
          <p><strong>Company:</strong> ${company}</p>
          <p><strong>Phone:</strong> ${phone}</p>
          <p><strong>Location:</strong> ${location}</p>
          <p><strong>Tier:</strong> ${tier}</p>
          ${domain ? `<p><strong>Website:</strong> <a href="https://${domain}">${domain}</a></p>` : ""}
        </div>

        <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
          <h3 style="margin-top: 0;">Their Message</h3>
          <p style="white-space: pre-wrap;">${replyContent}</p>
        </div>

        <div style="background: #e0e7ff; padding: 16px; border-radius: 8px;">
          <p style="margin: 0;"><strong>Campaign:</strong> ${campaignName}</p>
          <p style="margin: 8px 0 0 0;"><strong>Reply to:</strong> <a href="mailto:${leadEmail}">${leadEmail}</a></p>
        </div>

        <p style="color: #6b7280; font-size: 12px; margin-top: 24px;">
          This notification was sent automatically by the Appletree lead system.
        </p>
      </div>
    `;

    const emailSubject = `Lead Reply: ${leadName} from ${company}`;

    // Send email to Shane only (Patrick disabled for testing)
    // const emailResult = await sendEmail(PATRICK_EMAIL, emailSubject, emailHtml);
    const emailResult = await sendEmail(SHANE_EMAIL, emailSubject, emailHtml);
    console.log("Email result:", emailResult);

    return new Response(
      JSON.stringify({
        success: true,
        message: "Notification sent",
        lead: leadEmail,
        emailResult
      }),
      {
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Error processing webhook:", error);
    return new Response(
      JSON.stringify({ success: false, error: String(error) }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
});
