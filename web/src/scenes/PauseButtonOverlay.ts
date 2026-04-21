import Phaser from "phaser";
import { SCREEN_WIDTH } from "../config/constants";

/**
 * PauseButtonOverlay
 *
 * Floating touch-friendly PAUSE button rendered in the top-right of the
 * screen. Launched as a sibling overlay scene by gameplay scenes
 * (SingleVersusScene / AutoTestScene) so it can receive pointer events
 * without having to steal them from the parent scene's input plugin.
 *
 * On pointerdown it pauses the parent scene (by key, stored from init
 * data) and launches PauseScene. Because PauseScene calls
 * `this.scene.bringToTop()` in its create(), this overlay naturally
 * ends up under the PauseScene's dim rectangle while the menu is up;
 * once PauseScene resolves (resume or return-to-title), this overlay
 * remains visible for the resumed parent or is stopped by PauseScene's
 * returnToTitle() flow.
 */
const BUTTON_WIDTH = 56;
const BUTTON_HEIGHT = 56;
const BUTTON_MARGIN_X = 20;
const BUTTON_MARGIN_Y = 20;
const BAR_WIDTH = 8;
const BAR_HEIGHT = 24;
const BAR_GAP = 6;

export class PauseButtonOverlay extends Phaser.Scene {
  private parentKey = "SingleVersusScene";

  constructor() {
    super({ key: "PauseButtonOverlay" });
  }

  init(data: { parentKey?: string }): void {
    if (data && typeof data.parentKey === "string" && data.parentKey.length > 0) {
      this.parentKey = data.parentKey;
    } else {
      this.parentKey = "SingleVersusScene";
    }
  }

  create(): void {
    // Position: top-right corner with small inset.
    const cx = SCREEN_WIDTH - BUTTON_MARGIN_X - BUTTON_WIDTH / 2;
    const cy = BUTTON_MARGIN_Y + BUTTON_HEIGHT / 2;

    // Rounded-rectangle background (semi-opaque dark with cyan border).
    const bg = this.add.graphics();
    bg.fillStyle(0x000000, 0.55);
    bg.fillRoundedRect(
      cx - BUTTON_WIDTH / 2,
      cy - BUTTON_HEIGHT / 2,
      BUTTON_WIDTH,
      BUTTON_HEIGHT,
      8
    );
    bg.lineStyle(2, 0x00ffff, 1.0);
    bg.strokeRoundedRect(
      cx - BUTTON_WIDTH / 2,
      cy - BUTTON_HEIGHT / 2,
      BUTTON_WIDTH,
      BUTTON_HEIGHT,
      8
    );

    // Pause icon: two vertical white bars. Emoji is intentionally avoided
    // per project policy (font fallback on Windows / Android is unreliable).
    bg.fillStyle(0xffffff, 1.0);
    const leftBarX = cx - BAR_GAP / 2 - BAR_WIDTH;
    const rightBarX = cx + BAR_GAP / 2;
    const barTopY = cy - BAR_HEIGHT / 2;
    bg.fillRect(leftBarX, barTopY, BAR_WIDTH, BAR_HEIGHT);
    bg.fillRect(rightBarX, barTopY, BAR_WIDTH, BAR_HEIGHT);

    // Transparent hit zone so the entire button (including padding)
    // accepts taps. Graphics fillRoundedRect is not natively interactive,
    // so we layer a Zone on top.
    const hitZone = this.add
      .zone(cx, cy, BUTTON_WIDTH, BUTTON_HEIGHT)
      .setOrigin(0.5, 0.5)
      .setInteractive({ useHandCursor: true });

    hitZone.on("pointerdown", () => {
      // Guard: don't re-pause if PauseScene is already active (double-tap).
      if (this.scene.isActive("PauseScene")) return;
      if (!this.scene.isActive(this.parentKey)) return;
      this.scene.pause(this.parentKey);
      this.scene.launch("PauseScene");
    });
  }
}
