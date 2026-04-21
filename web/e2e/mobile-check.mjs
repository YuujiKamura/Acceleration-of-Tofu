/**
 * Mobile viewport smoke test. Captures how the current build looks on
 * a typical phone (iPhone 13 portrait, 390x844) and a tablet (iPad
 * portrait, 810x1080) so we can see what a mobile visitor sees.
 *
 * Usage: node e2e/mobile-check.mjs
 */
import { chromium, devices } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.SNAPSHOT_URL ?? "http://localhost:5173/";
const OUT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "snapshots"
);
const CHROME =
  process.env.CHROME_PATH ??
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const browser = await chromium.launch({ executablePath: CHROME, headless: true });

async function capture(deviceName, outFile) {
  const device = devices[deviceName];
  const ctx = await browser.newContext({ ...device });
  const page = await ctx.newPage();
  await page.goto(BASE, { waitUntil: "load" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(OUT, outFile), fullPage: false });
  await ctx.close();
  console.log(`[mobile] ${deviceName} -> ${outFile}`);
}

await capture("iPhone 13", "mobile-iphone13-portrait.png");
await capture("iPad (gen 7)", "mobile-ipad-portrait.png");
await capture("Galaxy S9+", "mobile-galaxy-landscape.png");

await browser.close();
