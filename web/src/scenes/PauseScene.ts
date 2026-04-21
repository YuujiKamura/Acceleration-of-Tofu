import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT } from "../config/constants";

/**
 * PauseScene
 *
 * Overlay launched by SingleVersusScene on ESC. The caller MUST pause the
 * gameplay scene via `this.scene.pause("SingleVersusScene")` before
 * launching us, and we resume it on "ゲームに戻る" selection.
 *
 * Ports game/states.py::PauseState. Menu is trimmed to what actually
 * works: resume + back-to-title. The Python "Quit" item has no process
 * to quit in a browser, and "操作説明" (InstructionsScene) is not
 * implemented — we do not ship dead menu items.
 */
const MENU_ITEMS = ["ゲームに戻る", "タイトルに戻る"] as const;

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
    // Ensure PauseScene renders above gameplay + HUD, regardless of
    // the scene-list registration order in main.ts. Phaser's "scene
    // launch" appends the scene to the display list, but subsequent
    // scene starts/restarts can reorder; bringing ourselves to top
    // here is idempotent and cheap.
    this.scene.bringToTop();

    // Semi-transparent dark overlay. Python PauseState used
    // pygame.SRCALPHA with fill((0, 0, 0, 128)) which is alpha 128/255
    // (~0.502). In WebGL the composited result over bright HUD text and
    // arena circles reads weaker than on pygame's software blit, so we
    // bump to 0.7 to keep the visual distinction the snapshot pass was
    // looking for (bug #8). The PAUSE / menu text color is unchanged.
    const overlay = this.add.graphics();
    overlay.fillStyle(0x000000, 0.7);
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
        this.returnToTitle();
        return;
    }
  }

  /**
   * Python PauseState (legacy/pygbag/game/states.py:744-745) does
   * `self.game.change_state(TitleState(self.game))` which tears down
   * the current gameplay state and installs Title. Phaser's scene
   * system is different: SingleVersusScene is paused (not stopped) and
   * HUDScene is launched as an overlay, so we have to stop both
   * siblings explicitly before handing control to TitleScene.
   *
   * Phaser quirk the old implementation tripped over: calling
   * `scene.stop("SingleVersusScene")` on a *paused* scene does work,
   * but the paused scene still has its input plugin paused, which
   * occasionally swallowed the subsequent keyboard events on
   * TitleScene when transitioning directly. Resuming the parent first
   * normalizes the plugin state, and then the stop cleanly shuts it
   * down (the SHUTDOWN handler in SingleVersusScene.cleanup disposes
   * projectiles / result text). We also stop HUDScene (launched as an
   * overlay, not auto-stopped by the parent) and finally start
   * TitleScene. We stop ourselves last so the start() call above is
   * still dispatched by a live scene.
   */
  private returnToTitle(): void {
    this.scene.resume(PARENT_SCENE_KEY);
    this.scene.stop(PARENT_SCENE_KEY);
    this.scene.stop("HUDScene");
    this.scene.start("TitleScene");
    this.scene.stop();
  }

  private resumeGame(): void {
    this.scene.resume(PARENT_SCENE_KEY);
    this.scene.stop();
  }
}
