import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT } from "../config/constants";
// D3: audio wiring — preload the 7 .ogg assets before TitleScene starts.
import { AudioManager } from "../systems/Audio";

/**
 * BootScene
 *
 * Loads the MPLUS1p font via the native FontFace API (not WebFontLoader)
 * and transitions to TitleScene once the font is registered in
 * `document.fonts`. Displays a simple "Loading..." text while pending.
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: "BootScene" });
  }

  create(): void {
    const loadingText = this.add
      .text(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, "Loading...", {
        fontFamily: "sans-serif",
        fontSize: "32px",
        color: "#ffffff",
      })
      .setOrigin(0.5, 0.5);

    void this.loadFontAndContinue(loadingText);
  }

  private async loadFontAndContinue(
    loadingText: Phaser.GameObjects.Text,
  ): Promise<void> {
    try {
      const font = new FontFace(
        "MPLUS1p",
        "url(fonts/MPLUS1p-Regular.ttf)",
      );
      await font.load();
      // Register the loaded font so Phaser/Canvas text can use it.
      (document.fonts as FontFaceSet).add(font);

      // D3: audio wiring — preload every .ogg asset before we leave this scene.
      await AudioManager.get().loadAll(this);

      loadingText.destroy();
      this.scene.start("TitleScene");
    } catch (err) {
      // If the font fails to load we still fall through to TitleScene;
      // the fallback is the browser default.
      // eslint-disable-next-line no-console
      console.error("[BootScene] font load failed:", err);
      loadingText.setText("Font load failed, continuing...");
      this.time.delayedCall(500, () => {
        loadingText.destroy();
        this.scene.start("TitleScene");
      });
    }
  }
}
