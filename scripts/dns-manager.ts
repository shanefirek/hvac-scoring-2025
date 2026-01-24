#!/usr/bin/env npx ts-node
/**
 * DNS Manager CLI - Programmatic domain email setup
 *
 * Commands:
 *   audit <domain>              Check SPF/DKIM/DMARC status
 *   porkbun:list <domain>       List all DNS records
 *   porkbun:add <domain>        Add a DNS record interactively
 *   resend:setup <domain>       Add domain to Resend + create DNS records
 *   resend:verify <domain>      Trigger verification for a domain
 *   resend:list                 List all Resend domains
 *   setup:dmarc <domain>        Add a DMARC policy
 *   setup:smartlead <domain>    Add Smartlead SPF include
 *
 * Requires in .env:
 *   RESEND_API_KEY
 *   PORKBUN_API_KEY
 *   PORKBUN_SECRET_KEY
 */

import * as dotenv from "dotenv";
import { execSync } from "child_process";
import * as readline from "readline";

dotenv.config();

const RESEND_API_KEY = process.env.RESEND_API_KEY;
const PORKBUN_API_KEY = process.env.PORKBUN_API_KEY;
const PORKBUN_SECRET_KEY = process.env.PORKBUN_SECRET_KEY;

// ============================================================================
// Utilities
// ============================================================================

function dig(record: string, type: string = "TXT"): string {
  try {
    return execSync(`dig +short ${type} ${record} 2>/dev/null`, { encoding: "utf-8" }).trim();
  } catch {
    return "";
  }
}

async function prompt(question: string): Promise<string> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function extractRootDomain(domain: string): string {
  const parts = domain.split(".");
  return parts.slice(-2).join(".");
}

// ============================================================================
// Porkbun API
// ============================================================================

async function porkbunRequest(endpoint: string, body: object = {}): Promise<any> {
  const res = await fetch(`https://api.porkbun.com/api/json/v3${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      apikey: PORKBUN_API_KEY,
      secretapikey: PORKBUN_SECRET_KEY,
      ...body,
    }),
  });
  return res.json();
}

async function porkbunListRecords(domain: string): Promise<any> {
  return porkbunRequest(`/dns/retrieve/${domain}`);
}

async function porkbunCreateRecord(
  domain: string,
  type: string,
  name: string,
  content: string,
  ttl: string = "600",
  prio?: number
): Promise<any> {
  const body: any = { type, name, content, ttl };
  if (prio !== undefined) body.prio = prio.toString();
  return porkbunRequest(`/dns/create/${domain}`, body);
}

async function porkbunDeleteRecord(domain: string, recordId: string): Promise<any> {
  return porkbunRequest(`/dns/delete/${domain}/${recordId}`);
}

// ============================================================================
// Resend API
// ============================================================================

async function resendRequest(endpoint: string, method: string = "GET", body?: object): Promise<any> {
  const options: RequestInit = {
    method,
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`https://api.resend.com${endpoint}`, options);
  return res.json();
}

async function resendListDomains(): Promise<any> {
  return resendRequest("/domains");
}

async function resendGetDomain(domainId: string): Promise<any> {
  return resendRequest(`/domains/${domainId}`);
}

async function resendCreateDomain(domain: string): Promise<any> {
  return resendRequest("/domains", "POST", { name: domain });
}

async function resendVerifyDomain(domainId: string): Promise<any> {
  return resendRequest(`/domains/${domainId}/verify`, "POST");
}

// ============================================================================
// Commands
// ============================================================================

async function cmdAudit(domain: string) {
  console.log(`\n🔍 DNS Audit: ${domain}\n${"=".repeat(50)}\n`);

  // SPF
  const spf = dig(domain, "TXT");
  const spfRecord = spf.split("\n").find(r => r.includes("v=spf1"));
  console.log("📧 SPF Record:");
  if (spfRecord) {
    console.log(`   ✅ ${spfRecord}`);
    if (spfRecord.includes("google")) console.log("      → Includes: Google Workspace");
    if (spfRecord.includes("zoho")) console.log("      → Includes: Zoho");
    if (spfRecord.includes("outlook") || spfRecord.includes("protection.outlook")) console.log("      → Includes: Microsoft 365");
    if (spfRecord.includes("smartlead")) console.log("      → Includes: Smartlead");
    if (spfRecord.includes("amazonses")) console.log("      → Includes: Amazon SES (Resend)");
  } else {
    console.log("   ❌ Missing - emails may be marked as spam");
  }

  // DMARC
  console.log("\n🛡️  DMARC Record:");
  const dmarc = dig(`_dmarc.${domain}`, "TXT");
  if (dmarc && dmarc.includes("v=DMARC1")) {
    console.log(`   ✅ ${dmarc}`);
    if (dmarc.includes("p=none")) console.log("      ⚠️  Policy: none (monitoring only)");
    if (dmarc.includes("p=quarantine")) console.log("      📥 Policy: quarantine");
    if (dmarc.includes("p=reject")) console.log("      🚫 Policy: reject (strict)");
  } else if (dmarc.includes("porkbun") || !dmarc) {
    console.log("   ❌ Missing - recommended for deliverability");
  }

  // DKIM - check common selectors
  console.log("\n🔐 DKIM Records:");
  const selectors = ["google", "default", "selector1", "selector2", "resend", "smtp", "mail"];
  let foundDkim = false;
  for (const sel of selectors) {
    const dkim = dig(`${sel}._domainkey.${domain}`, "TXT");
    if (dkim && dkim.includes("DKIM1")) {
      console.log(`   ✅ ${sel}._domainkey → configured`);
      foundDkim = true;
    } else if (dkim && !dkim.includes("porkbun")) {
      console.log(`   ✅ ${sel}._domainkey → ${dkim.substring(0, 50)}...`);
      foundDkim = true;
    }
  }
  if (!foundDkim) {
    console.log("   ❌ No DKIM found (checked: google, default, selector1/2, resend)");
  }

  // MX
  console.log("\n📬 MX Records:");
  const mx = dig(domain, "MX");
  if (mx) {
    mx.split("\n").forEach(r => console.log(`   📨 ${r}`));
  } else {
    console.log("   ❌ No MX records");
  }

  console.log("");
}

async function cmdPorkbunList(domain: string) {
  console.log(`\n📋 DNS Records for ${domain}\n${"=".repeat(50)}\n`);

  const result = await porkbunListRecords(domain);

  if (result.status !== "SUCCESS") {
    console.log(`❌ Error: ${result.message}`);
    console.log("\n💡 Make sure API access is enabled for this domain:");
    console.log("   1. Go to https://porkbun.com/account/domainsSS");
    console.log(`   2. Click on ${domain}`);
    console.log("   3. Enable 'API Access' toggle\n");
    return;
  }

  const records = result.records || [];
  if (records.length === 0) {
    console.log("No records found.");
    return;
  }

  // Group by type
  const byType: Record<string, any[]> = {};
  for (const r of records) {
    if (!byType[r.type]) byType[r.type] = [];
    byType[r.type].push(r);
  }

  for (const type of Object.keys(byType).sort()) {
    console.log(`${type}:`);
    for (const r of byType[type]) {
      const name = r.name || "(root)";
      const content = r.content.length > 60 ? r.content.substring(0, 60) + "..." : r.content;
      console.log(`  ${r.id.padEnd(12)} ${name.padEnd(30)} → ${content}`);
    }
    console.log("");
  }
}

async function cmdResendList() {
  console.log(`\n📧 Resend Domains\n${"=".repeat(50)}\n`);

  const result = await resendListDomains();

  if (result.statusCode) {
    console.log(`❌ Error: ${result.message}`);
    return;
  }

  for (const d of result.data || []) {
    const status = d.status === "verified" ? "✅" : d.status === "not_started" ? "⏳" : "❌";
    console.log(`${status} ${d.name}`);
    console.log(`   ID: ${d.id}`);
    console.log(`   Status: ${d.status}`);
    console.log(`   Region: ${d.region}`);
    console.log("");
  }
}

async function cmdResendSetup(domain: string) {
  console.log(`\n🚀 Setting up Resend for ${domain}\n${"=".repeat(50)}\n`);

  // Check if domain already exists
  const domains = await resendListDomains();
  const existing = domains.data?.find((d: any) => d.name === domain);

  let domainData: any;

  if (existing) {
    console.log(`Domain already exists in Resend (status: ${existing.status})`);
    domainData = await resendGetDomain(existing.id);
  } else {
    console.log("Adding domain to Resend...");
    domainData = await resendCreateDomain(domain);

    if (domainData.statusCode) {
      console.log(`❌ Error: ${domainData.message}`);
      return;
    }
    console.log(`✅ Domain added with ID: ${domainData.id}`);
  }

  // Get DNS records
  const records = domainData.records || [];
  if (records.length === 0) {
    console.log("No DNS records returned from Resend.");
    return;
  }

  console.log(`\n📋 Required DNS Records:\n`);
  for (const r of records) {
    const status = r.status === "verified" ? "✅" : "⏳";
    console.log(`${status} ${r.type.padEnd(5)} ${r.name}`);
    console.log(`         → ${r.value.substring(0, 60)}${r.value.length > 60 ? "..." : ""}`);
  }

  // Try to add via Porkbun
  const rootDomain = extractRootDomain(domain);
  console.log(`\n🔧 Adding records to Porkbun (${rootDomain})...\n`);

  for (const r of records) {
    if (r.status === "verified") {
      console.log(`⏭️  Skipping ${r.type} ${r.name} (already verified)`);
      continue;
    }

    // Convert name to subdomain format for Porkbun
    let subdomain = r.name;
    if (subdomain.endsWith(`.${rootDomain}`)) {
      subdomain = subdomain.replace(`.${rootDomain}`, "");
    } else if (subdomain === rootDomain) {
      subdomain = "";
    }

    const result = await porkbunCreateRecord(
      rootDomain,
      r.type,
      subdomain,
      r.value,
      "600",
      r.priority
    );

    if (result.status === "SUCCESS") {
      console.log(`✅ Added ${r.type} ${subdomain || "(root)"}`);
    } else if (result.message?.includes("already exists")) {
      console.log(`⏭️  ${r.type} ${subdomain || "(root)"} already exists`);
    } else {
      console.log(`❌ Failed ${r.type} ${subdomain}: ${result.message}`);
    }
  }

  // Trigger verification
  console.log(`\n⏳ Waiting 5 seconds for DNS propagation...`);
  await new Promise(r => setTimeout(r, 5000));

  console.log(`🔍 Triggering verification...`);
  await resendVerifyDomain(domainData.id);

  console.log(`\n✅ Done! Check status with: npx ts-node scripts/dns-manager.ts resend:list\n`);
}

async function cmdSetupDmarc(domain: string) {
  console.log(`\n🛡️  Setting up DMARC for ${domain}\n${"=".repeat(50)}\n`);

  const email = await prompt("Report email (e.g., dmarc@yourdomain.com): ");
  const policy = await prompt("Policy (none/quarantine/reject) [none]: ") || "none";

  const dmarcValue = `v=DMARC1; p=${policy}; rua=mailto:${email}; ruf=mailto:${email}; fo=1; pct=100`;

  console.log(`\nAdding DMARC record: _dmarc.${domain}`);
  console.log(`Value: ${dmarcValue}\n`);

  const result = await porkbunCreateRecord(domain, "TXT", "_dmarc", dmarcValue);

  if (result.status === "SUCCESS") {
    console.log(`✅ DMARC record added successfully`);
  } else {
    console.log(`❌ Failed: ${result.message}`);
  }
}

async function cmdSetupSmartlead(domain: string) {
  console.log(`\n📧 Adding Smartlead to SPF for ${domain}\n${"=".repeat(50)}\n`);

  // Get current SPF
  const currentSpf = dig(domain, "TXT").split("\n").find(r => r.includes("v=spf1"));

  if (!currentSpf) {
    console.log("No existing SPF record. Creating new one with Smartlead...");
    const newSpf = "v=spf1 include:_spf.smartlead.ai ~all";
    const result = await porkbunCreateRecord(domain, "TXT", "", newSpf);
    console.log(result.status === "SUCCESS" ? "✅ SPF created" : `❌ Failed: ${result.message}`);
    return;
  }

  if (currentSpf.includes("smartlead")) {
    console.log("✅ Smartlead already in SPF record");
    return;
  }

  // Add smartlead to existing SPF
  const newSpf = currentSpf.replace("~all", "include:_spf.smartlead.ai ~all").replace(/-all/, "include:_spf.smartlead.ai -all");
  console.log(`Current: ${currentSpf}`);
  console.log(`New:     ${newSpf}`);
  console.log("\n⚠️  You'll need to update the existing SPF record manually or delete and recreate.");
  console.log("   Use: npx ts-node scripts/dns-manager.ts porkbun:list " + domain);
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  const [cmd, ...args] = process.argv.slice(2);

  if (!cmd) {
    console.log(`
DNS Manager CLI - Programmatic domain email setup

Commands:
  audit <domain>              Check SPF/DKIM/DMARC status
  porkbun:list <domain>       List all DNS records
  resend:setup <domain>       Add domain to Resend + create DNS records
  resend:verify <domainId>    Trigger verification
  resend:list                 List all Resend domains
  setup:dmarc <domain>        Add a DMARC policy
  setup:smartlead <domain>    Add Smartlead SPF include

Examples:
  npx ts-node scripts/dns-manager.ts audit appletree-tax.com
  npx ts-node scripts/dns-manager.ts resend:setup updates.appletree-tax.com
  npx ts-node scripts/dns-manager.ts porkbun:list appletree-tax.com
`);
    return;
  }

  switch (cmd) {
    case "audit":
      if (!args[0]) { console.log("Usage: audit <domain>"); return; }
      await cmdAudit(args[0]);
      break;

    case "porkbun:list":
      if (!args[0]) { console.log("Usage: porkbun:list <domain>"); return; }
      if (!PORKBUN_API_KEY) { console.log("Missing PORKBUN_API_KEY in .env"); return; }
      await cmdPorkbunList(args[0]);
      break;

    case "resend:list":
      if (!RESEND_API_KEY) { console.log("Missing RESEND_API_KEY in .env"); return; }
      await cmdResendList();
      break;

    case "resend:setup":
      if (!args[0]) { console.log("Usage: resend:setup <domain>"); return; }
      if (!RESEND_API_KEY) { console.log("Missing RESEND_API_KEY in .env"); return; }
      if (!PORKBUN_API_KEY) { console.log("Missing PORKBUN_API_KEY in .env"); return; }
      await cmdResendSetup(args[0]);
      break;

    case "resend:verify":
      if (!args[0]) { console.log("Usage: resend:verify <domainId>"); return; }
      if (!RESEND_API_KEY) { console.log("Missing RESEND_API_KEY in .env"); return; }
      await resendVerifyDomain(args[0]);
      console.log("Verification triggered");
      break;

    case "setup:dmarc":
      if (!args[0]) { console.log("Usage: setup:dmarc <domain>"); return; }
      if (!PORKBUN_API_KEY) { console.log("Missing PORKBUN_API_KEY in .env"); return; }
      await cmdSetupDmarc(args[0]);
      break;

    case "setup:smartlead":
      if (!args[0]) { console.log("Usage: setup:smartlead <domain>"); return; }
      if (!PORKBUN_API_KEY) { console.log("Missing PORKBUN_API_KEY in .env"); return; }
      await cmdSetupSmartlead(args[0]);
      break;

    default:
      console.log(`Unknown command: ${cmd}`);
      console.log("Run without arguments to see usage.");
  }
}

main().catch(err => {
  console.error("Error:", err.message);
  process.exit(1);
});
