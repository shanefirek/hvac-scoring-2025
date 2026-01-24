/**
 * Setup Resend domain with automatic DNS configuration via Porkbun
 *
 * Usage:
 *   npx ts-node scripts/setup_resend_domain.ts appletree-tax.com
 *
 * Required in .env:
 *   RESEND_API_KEY - Your Resend API key (re_xxxxxxxxx)
 *   PORKBUN_API_KEY - Your Porkbun API key
 *   PORKBUN_SECRET_KEY - Your Porkbun secret key
 */

import * as dotenv from "dotenv";
dotenv.config();

const RESEND_API_KEY = process.env.RESEND_API_KEY;
const PORKBUN_API_KEY = process.env.PORKBUN_API_KEY;
const PORKBUN_SECRET_KEY = process.env.PORKBUN_SECRET_KEY;

interface ResendDNSRecord {
  record: string;
  name: string;
  type: string;
  ttl: string;
  status: string;
  value: string;
  priority?: number;
}

interface ResendDomainResponse {
  id: string;
  name: string;
  status: string;
  records: ResendDNSRecord[];
}

async function createResendDomain(domain: string): Promise<ResendDomainResponse> {
  console.log(`\n[Resend] Adding domain: ${domain}`);

  const res = await fetch("https://api.resend.com/domains", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: domain }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Resend API error: ${res.status} - ${error}`);
  }

  return res.json() as Promise<ResendDomainResponse>;
}

async function getResendDomain(domainId: string): Promise<ResendDomainResponse> {
  const res = await fetch(`https://api.resend.com/domains/${domainId}`, {
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
    },
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Resend API error: ${res.status} - ${error}`);
  }

  return res.json() as Promise<ResendDomainResponse>;
}

async function verifyResendDomain(domainId: string): Promise<any> {
  console.log(`\n[Resend] Verifying domain...`);

  const res = await fetch(`https://api.resend.com/domains/${domainId}/verify`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
    },
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Resend verify error: ${res.status} - ${error}`);
  }

  return res.json();
}

async function createPorkbunRecord(
  domain: string,
  type: string,
  name: string,
  content: string,
  ttl: string = "600"
): Promise<any> {
  // Extract subdomain from full record name
  // e.g., "resend._domainkey.appletree-tax.com" -> "resend._domainkey"
  let subdomain = name;
  if (name.endsWith(`.${domain}`)) {
    subdomain = name.replace(`.${domain}`, "");
  } else if (name === domain) {
    subdomain = ""; // root domain
  }

  console.log(`[Porkbun] Creating ${type} record: ${subdomain || "(root)"} -> ${content.substring(0, 50)}...`);

  const res = await fetch(`https://api.porkbun.com/api/json/v3/dns/create/${domain}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      apikey: PORKBUN_API_KEY,
      secretapikey: PORKBUN_SECRET_KEY,
      type,
      name: subdomain,
      content,
      ttl,
    }),
  });

  const result = await res.json() as { status: string; message?: string; id?: string };

  if (result.status !== "SUCCESS") {
    console.error(`  Failed: ${result.message || JSON.stringify(result)}`);
    return result;
  }

  console.log(`  Success: Record ID ${result.id}`);
  return result;
}

async function listPorkbunRecords(domain: string): Promise<any> {
  const res = await fetch(`https://api.porkbun.com/api/json/v3/dns/retrieve/${domain}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      apikey: PORKBUN_API_KEY,
      secretapikey: PORKBUN_SECRET_KEY,
    }),
  });

  return res.json();
}

async function main() {
  const domain = process.argv[2];

  if (!domain) {
    console.error("Usage: npx ts-node scripts/setup_resend_domain.ts <domain>");
    console.error("Example: npx ts-node scripts/setup_resend_domain.ts appletree-tax.com");
    process.exit(1);
  }

  if (!RESEND_API_KEY) {
    console.error("Missing RESEND_API_KEY environment variable");
    process.exit(1);
  }

  if (!PORKBUN_API_KEY || !PORKBUN_SECRET_KEY) {
    console.error("Missing PORKBUN_API_KEY or PORKBUN_SECRET_KEY environment variables");
    process.exit(1);
  }

  console.log("=".repeat(60));
  console.log("Resend + Porkbun Domain Setup");
  console.log("=".repeat(60));

  // Step 1: Add domain to Resend
  let resendDomain: ResendDomainResponse;
  try {
    resendDomain = await createResendDomain(domain);
    console.log(`Domain added with ID: ${resendDomain.id}`);
  } catch (err: any) {
    // Domain might already exist, try to list domains
    if (err.message.includes("already exists")) {
      console.log("Domain already exists in Resend, fetching records...");
      // We'd need to list domains and find the right one
      // For now, just re-throw
    }
    throw err;
  }

  console.log(`\nDNS Records to create:`);
  console.log("-".repeat(60));

  for (const record of resendDomain.records) {
    console.log(`  ${record.type.padEnd(6)} ${record.name}`);
    console.log(`         -> ${record.value.substring(0, 60)}${record.value.length > 60 ? "..." : ""}`);
  }

  // Step 2: Create DNS records in Porkbun
  console.log("\n" + "=".repeat(60));
  console.log("Creating DNS records in Porkbun...");
  console.log("=".repeat(60));

  for (const record of resendDomain.records) {
    // Skip MX records if you don't need inbound email
    if (record.type === "MX") {
      console.log(`[Porkbun] Skipping MX record (not needed for sending)`);
      continue;
    }

    await createPorkbunRecord(
      domain,
      record.type,
      record.name,
      record.value,
      record.ttl
    );
  }

  // Step 3: Wait and verify
  console.log("\n" + "=".repeat(60));
  console.log("Waiting 10 seconds for DNS propagation...");
  console.log("=".repeat(60));

  await new Promise(resolve => setTimeout(resolve, 10000));

  try {
    await verifyResendDomain(resendDomain.id);
    console.log("Verification triggered! Check Resend dashboard for status.");
  } catch (err) {
    console.log("Verification may take a few minutes. Check Resend dashboard.");
  }

  // Final status
  console.log("\n" + "=".repeat(60));
  console.log("Done! Next steps:");
  console.log("=".repeat(60));
  console.log("1. Check https://resend.com/domains for verification status");
  console.log("2. DNS propagation can take up to 48 hours (usually minutes)");
  console.log("3. Once verified, your edge function will work!");
}

main().catch(err => {
  console.error("\nError:", err.message);
  process.exit(1);
});
