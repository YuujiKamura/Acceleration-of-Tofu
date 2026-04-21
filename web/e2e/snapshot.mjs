/**
 * Canvas framebuffer capture harness.
 *
 * Launches headless Chrome against the running Vite dev server, navigates
 * through the game's scene flow, and dumps the raw Phaser canvas
 * framebuffer (via canvas.toDataURL) as PNG files under e2e/snapshots/.
 *
 * This is NOT a window screenshot — it's the actual pixel data the
 * renderer has produced, independent of whether any window is visible.
 *
 * Usage:
 *   cd web
 *   npm run dev &             # start vite on :5173
 *   node e2e/snapshot.mjs     # capture
 *
 * Output:
 *   e2e/snapshots/NN-label.png
 */
import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BASE_URL = process.env.SNAPSHOT_URL ?? "http://localhost:5173/";
const OUT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "snapshots");
const CHROME_PATH =
  process.env.CHROME_PATH ??
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

/** Wait until the Phaser canvas has rendered non-trivial content. */
async function waitForFrames(page, minFrames = 60) {
  await page.waitForSelector("canvas", { timeout: 15_000 });
  await page.waitForFunction(
    (min) => {
      const c = document.querySelector("canvas");
      if (!c) return false;
      // We rely on canvas width being finite — Phaser sets it at boot.
      return c.width > 0 && c.height > 0 && performance.now() > min * 16;
    },
    minFrames,
    { timeout: 15_000 }
  );
}

/** Read the canvas framebuffer as PNG base64, save to disk. */
async function capture(page, label, index) {
  const dataUrl = await page.evaluate(() => {
    const c = document.querySelector("canvas");
    if (!c) return null;
    // toDataURL reads whatever is currently in the canvas backbuffer.
    // For WebGL Phaser needs `preserveDrawingBuffer: true` OR we must
    // snapshot right after a render. Phaser 3 by default does NOT
    // preserveDrawingBuffer, so canvas.toDataURL from the wrong tick
    // can return a blank frame. We use Phaser's own renderer.snapshot
    // when available, which hooks the next post-render tick.
    return new Promise((resolve) => {
      const g = window.game;
      if (g && g.renderer && typeof g.renderer.snapshot === "function") {
        g.renderer.snapshot((img) => {
          if (img instanceof HTMLImageElement) resolve(img.src);
          else if (img instanceof HTMLCanvasElement) resolve(img.toDataURL("image/png"));
          else resolve(null);
        });
      } else {
        // Fallback: direct toDataURL.
        resolve(c.toDataURL("image/png"));
      }
    });
  });

  if (!dataUrl || !dataUrl.startsWith("data:image/png;base64,")) {
    console.error(`[capture] ${label}: snapshot returned empty or malformed data`);
    return;
  }

  const b64 = dataUrl.slice("data:image/png;base64,".length);
  const file = path.join(OUT_DIR, `${String(index).padStart(2, "0")}-${label}.png`);
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.writeFile(file, Buffer.from(b64, "base64"));
  const stat = await fs.stat(file);
  console.log(`[capture] ${label} -> ${path.relative(process.cwd(), file)} (${stat.size} bytes)`);
}

async function main() {
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
  });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();

  // Surface Phaser's Game instance as window.game for snapshot access.
  // Our main.ts currently does `new Phaser.Game(config)` without assigning.
  // The snapshot harness works around this by also falling back to direct
  // canvas.toDataURL — less reliable, but sufficient for smoke capture.
  page.on("pageerror", (e) => console.error(`[pageerror] ${e.message}`));
  page.on("console", (msg) => {
    const type = msg.type();
    if (type === "error" || type === "warning") {
      console.log(`[console.${type}] ${msg.text()}`);
    }
  });

  console.log(`[harness] navigating to ${BASE_URL}`);
  await page.goto(BASE_URL, { waitUntil: "load" });
  await waitForFrames(page);

  // Title scene (with background demo behind).
  // Give Phaser a full second after boot to let BGScene spawn players.
  await page.waitForTimeout(1500);
  await capture(page, "title", 1);

  // Step into SingleVersus (first menu item = menu.single).
  await page.keyboard.press("Enter");
  await page.waitForTimeout(500);
  await capture(page, "single-versus-entry", 2);

  // Let a few seconds of gameplay elapse so HUD, players, projectiles
  // all have visible state.
  await page.waitForTimeout(2500);
  await capture(page, "single-versus-midgame", 3);

  // Press Escape — should pause + launch PauseScene overlay.
  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);
  await capture(page, "pause", 4);

  // Resume (menu item 0 = ゲームに戻る) then wait a bit.
  await page.keyboard.press("Enter");
  await page.waitForTimeout(800);
  await capture(page, "resumed", 5);

  // --- Jump directly to AutoTestScene via Phaser scene manager. ---
  // UI-driven navigation is flaky (pause scene menu handling seems to
  // drop input) — bypass it for reliable capture.
  await page.evaluate(() => {
    const g = window.game;
    for (const s of g.scene.getScenes(true)) g.scene.stop(s.scene.key);
    g.scene.start("AutoTestScene");
  });
  await page.waitForTimeout(800);
  await capture(page, "autotest-entry", 6);

  // Let AI play a few seconds — should produce dash, shots, possibly
  // weapon_b / hyper / shield per the new AI.
  await page.waitForTimeout(3000);
  await capture(page, "autotest-3s", 7);
  await page.waitForTimeout(3000);
  await capture(page, "autotest-6s", 8);

  await browser.close();
  console.log("[harness] done");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
