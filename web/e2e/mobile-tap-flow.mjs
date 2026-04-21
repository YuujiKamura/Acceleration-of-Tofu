/**
 * Mobile tap-flow smoke test.
 *
 * Emulates an iPhone 13 portrait viewport, then exercises the new
 * tap-driven UI wiring end-to-end:
 *   1. Tap the "自動テスト" menu item on TitleScene -> AutoTestScene
 *   2. Tap the floating PAUSE button -> PauseScene overlay appears
 *   3. Tap "タイトルに戻る" on PauseScene -> back to TitleScene
 *
 * A screenshot is saved before and after each tap under
 * e2e/snapshots/ so the caller can visually verify each transition.
 *
 * Usage: node e2e/mobile-tap-flow.mjs
 */
import { chromium, devices } from "playwright";
import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";

const BASE = process.env.SNAPSHOT_URL ?? "http://localhost:5173/";
const OUT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "snapshots"
);
const CHROME =
  process.env.CHROME_PATH ??
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

async function shot(page, label) {
  await fs.mkdir(OUT, { recursive: true });
  const file = path.join(OUT, `mobile-tap-${label}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log(`[mobile-tap] ${label} -> ${path.relative(process.cwd(), file)}`);
}

/**
 * Returns the canvas-relative tap point for a game-coordinate (gx, gy).
 * Because scale.mode = FIT, the canvas is letterboxed inside its on-screen
 * rectangle. We map (gx,gy) in 1280x720 game space into the letterboxed
 * rectangle based on the aspect-preserving fit.
 */
async function tapGameCoord(page, gx, gy) {
  const point = await page.evaluate(
    ({ gx, gy }) => {
      const c = document.querySelector("canvas");
      if (!c) return null;
      const r = c.getBoundingClientRect();
      // Phaser FIT keeps canvas aspect at 1280/720; the DOM canvas width/height
      // already reflect the fit result, so a direct ratio works.
      const sx = r.width / c.width;
      const sy = r.height / c.height;
      return {
        x: r.left + gx * sx,
        y: r.top + gy * sy,
      };
    },
    { gx, gy }
  );
  if (!point) throw new Error("no canvas");
  await page.mouse.click(point.x, point.y);
}

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const device = devices["iPhone 13"];
const ctx = await browser.newContext({ ...device });
const page = await ctx.newPage();
page.on("pageerror", (e) => console.error(`[pageerror] ${e.message}`));

let failed = false;
try {
  await page.goto(BASE, { waitUntil: "load" });
  await page.waitForSelector("canvas", { timeout: 15_000 });
  await page.waitForTimeout(1500);
  await shot(page, "01-title");

  // Step 1: tap "自動テスト" (second menu item, y = 350 in game coords).
  await tapGameCoord(page, 640, 350);
  await page.waitForTimeout(900);
  await shot(page, "02-autotest");

  const sceneAfterTap1 = await page.evaluate(() => {
    const keys = [];
    for (const s of window.game.scene.getScenes(true)) keys.push(s.scene.key);
    return keys;
  });
  console.log(`[mobile-tap] active scenes after tap1: ${sceneAfterTap1.join(", ")}`);
  if (!sceneAfterTap1.includes("AutoTestScene")) {
    console.error("[mobile-tap] FAIL: AutoTestScene not active after title tap");
    failed = true;
  }

  // Step 2: tap the floating PAUSE button (top-right ~ SCREEN_WIDTH-48, 48).
  await tapGameCoord(page, 1280 - 48, 48);
  await page.waitForTimeout(600);
  await shot(page, "03-pause");

  const sceneAfterTap2 = await page.evaluate(() => {
    const keys = [];
    for (const s of window.game.scene.getScenes(true)) keys.push(s.scene.key);
    return keys;
  });
  console.log(`[mobile-tap] active scenes after tap2: ${sceneAfterTap2.join(", ")}`);
  if (!sceneAfterTap2.includes("PauseScene")) {
    console.error("[mobile-tap] FAIL: PauseScene not active after PAUSE tap");
    failed = true;
  }

  // Step 3: tap "タイトルに戻る" (second menu item in PauseScene, y = 350).
  await tapGameCoord(page, 640, 350);
  await page.waitForTimeout(900);
  await shot(page, "04-back-to-title");

  const sceneAfterTap3 = await page.evaluate(() => {
    const keys = [];
    for (const s of window.game.scene.getScenes(true)) keys.push(s.scene.key);
    return keys;
  });
  console.log(`[mobile-tap] active scenes after tap3: ${sceneAfterTap3.join(", ")}`);
  if (!sceneAfterTap3.includes("TitleScene")) {
    console.error("[mobile-tap] FAIL: TitleScene not active after return-to-title");
    failed = true;
  }
} finally {
  await browser.close();
}

if (failed) {
  console.error("[mobile-tap] FAILED");
  process.exit(1);
}
console.log("[mobile-tap] OK");
