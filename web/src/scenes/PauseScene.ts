import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT } from "../config/constants";

/**
 * PauseScene
 *
 * Overlay launched by SingleVersusScene on ESC. The caller MUST pause the
 * gameplay scene via `this.scene.pause("SingleVersusScene")` before
 * launching us, and we resume it on "ゲームに戻る" selection.
 *
 * Ports game/states.py::PauseState. We use the web-localized 3-item
 * menu (resume / instructions / back-to-title); the "Quit" item from
 * Python is dropped because there's no process to quit in a browser.
 */
const MENU_ITEMS = ["ゲームに戻る", "操作説明", "タイトルに戻る"] as const;

const PARENT_SCENE_KEY = "SingleVersusScene";

const COLOR_CYAN = "#00ffff";
const COLOR_WHITE = "#ffffff";
const COLOR_YELLOW = "#ffff00";

export class PauseScene extends Phaser.Scene {
  private selectedIndex = 0;
  private menuTexts: Phaser.GameObjects.Text[] = [];

  constructor() {
    super({ key: "PauseScene" });
  }

  create(): void {
    // Semi-transparent dark overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x000000, 0.5);
    overlay.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    // "PAUSE" title in 72pt cyan MPLUS1p
    this.add
      .text(SCREEN_WIDTH / 2, 180, "PAUSE", {
        fontFamily: "MPLUS1p",
        fontSize: "72px",
        color: COLOR_CYAN,
      })
      .setOrigin(0.5, 0.5);

    this.menuTexts = MENU_ITEMS.map((label, i) =>
      this.add
        .text(SCREEN_WIDTH / 2, 300 + i * 50, label, {
          fontFamily: "MPLUS1p",
          fontSize: "36px",
          color: COLOR_WHITE,
        })
        .setOrigin(0.5, 0.5)
    );

    this.selectedIndex = 0;
    this.refreshMenu();

    const kb = this.input.keyboard;
    if (!kb) return;

    kb.on("keydown-UP", () => this.move(-1));
    kb.on("keydown-DOWN", () => this.move(1));
    kb.on("keydown-ENTER", () => this.confirm());
    kb.on("keydown-Z", () => this.confirm());
    kb.on("keydown-ESC", () => this.resumeGame());
  }

  private move(delta: number): void {
    this.selectedIndex =
      (this.selectedIndex + delta + MENU_ITEMS.length) % MENU_ITEMS.length;
    this.refreshMenu();
  }

  private refreshMenu(): void {
    this.menuTexts.forEach((txt, i) => {
      txt.setColor(i === this.selectedIndex ? COLOR_YELLOW : COLOR_WHITE);
    });
  }

  private confirm(): void {
    switch (this.selectedIndex) {
      case 0:
        this.resumeGame();
        return;
      case 1:
        // TODO: InstructionsScene not yet ported
        // eslint-disable-next-line no-console
        console.log("[PauseScene] TODO: InstructionsScene");
        return;
      case 2:
        this.scene.stop(PARENT_SCENE_KEY);
        this.scene.stop("HUDScene");
        this.scene.stop();
        this.scene.start("TitleScene");
        return;
    }
  }

  private resumeGame(): void {
    this.scene.resume(PARENT_SCENE_KEY);
    this.scene.stop();
  }
}
