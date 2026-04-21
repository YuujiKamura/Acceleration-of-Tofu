/**
 * One-off DOM-level screenshot to verify the AudioManager mute button
 * overlay. The main snapshot harness uses canvas.toDataURL, which
 * captures *only* the Phaser framebuffer and misses DOM elements like
 * the mute button. This script uses page.screenshot() (full viewport,
 * including DOM) to verify the button renders and reacts to clicks.
 */
import { chromium } from "playwright";
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
const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
await page.goto(BASE, { waitUntil: "load" });
await page.waitForSelector("#mute-indicator", { timeout: 10_000 });
await page.waitForTimeout(800);
await page.screenshot({ path: path.join(OUT, "dom-mute-on.png") });
console.log("[dom] captured ON state");

await page.click("#mute-indicator");
await page.waitForTimeout(300);
await page.screenshot({ path: path.join(OUT, "dom-mute-off.png") });
console.log("[dom] captured OFF state");

await page.click("#mute-indicator");
await page.waitForTimeout(300);
await page.screenshot({ path: path.join(OUT, "dom-mute-on-again.png") });
console.log("[dom] captured ON-again state");

await browser.close();
