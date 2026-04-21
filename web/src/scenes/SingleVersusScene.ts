import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT } from "../config/constants";

/**
 * SingleVersusScene
 *
 * Placeholder for the player-vs-CPU mode. Renders a centered TODO
 * message in MPLUS1p 36pt white and returns to TitleScene on ESC.
 * The real implementation (key-mapped P1 vs SimpleAI P2) lands in a
 * later pass after AutoTestScene proves the shared Player + Projectile
 * pipeline is stable.
 */
export class SingleVersusScene extends Phaser.Scene {
  constructor() {
    super({ key: "SingleVersusScene" });
  }

  create(): void {
    this.add
      .text(
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2,
        "TODO: 実装中 (press ESC to return)",
        {
          fontFamily: "MPLUS1p",
          fontSize: "36px",
          color: "#ffffff",
        }
      )
      .setOrigin(0.5, 0.5);

    const kb = this.input.keyboard;
    if (kb) {
      kb.on("keydown-ESC", () => {
        this.scene.start("TitleScene");
      });
    }
  }
}
