import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT } from "../config/constants";
import { tr } from "../i18n";
// D3: audio wiring — start the title BGM once the scene builds.
import { AudioManager } from "../systems/Audio";

// 実装済みの遷移先があるものだけ並べる。training/controls/options/quit は
// 実 Scene が無いので追加しない (追加したくなったら先に Scene を実装する)。
const MENU_KEYS = ["menu.single", "menu.autotest"] as const;

type MenuKey = (typeof MENU_KEYS)[number];

const COLOR_CYAN = "#00ffff";
const COLOR_WHITE = "#ffffff";
const COLOR_HINT = "#96c8e6";
const COLOR_VERSION = "#646464";

const VERSION_STRING = "Ver 0.1.0";

/**
 * TitleScene
 *
 * Displays the splash title and a vertical text menu. Up/Down to move
 * selection, Enter or Z to confirm. Confirmation currently only logs
 * the selected key; individual game modes will be wired to their
 * scenes in later passes.
 */
export class TitleScene extends Phaser.Scene {
  private menuTexts: Phaser.GameObjects.Text[] = [];
  private selectedIndex = 0;
  private cursorKeys!: Phaser.Types.Input.Keyboard.CursorKeys;
  private zKey!: Phaser.Input.Keyboard.Key;
  private enterKey!: Phaser.Input.Keyboard.Key;

  constructor() {
    super({ key: "TitleScene" });
  }

  create(): void {
    // Python TitleState が裏で AutoTestState を回していたのを Phaser に移植。
    // TitleBackgroundScene を下層で launch して CPU vs CPU の試合を流し、
    // 100/255 alpha の黒オーバーレイを挟んでからタイトル UI を描く。
    if (!this.scene.isActive("TitleBackgroundScene")) {
      this.scene.launch("TitleBackgroundScene");
    }
    this.scene.sendToBack("TitleBackgroundScene");
    this.add
      .rectangle(
        SCREEN_WIDTH / 2,
        SCREEN_HEIGHT / 2,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        0x000000,
        100 / 255
      )
      .setOrigin(0.5, 0.5);

    this.add
      .text(SCREEN_WIDTH / 2, 150, tr("splash.title"), {
        fontFamily: "MPLUS1p",
        fontSize: "72px",
        color: COLOR_CYAN,
      })
      .setOrigin(0.5, 0.5);

    this.menuTexts = MENU_KEYS.map((key, i) => {
      const txt = this.add
        .text(SCREEN_WIDTH / 2, 300 + i * 50, "", {
          fontFamily: "MPLUS1p",
          fontSize: "36px",
          color: COLOR_WHITE,
        })
        .setOrigin(0.5, 0.5);
      txt.setData("menuKey", key);
      return txt;
    });

    this.refreshMenu();

    this.add
      .text(20, SCREEN_HEIGHT - 30, tr("title.mute_hint_on"), {
        fontFamily: "MPLUS1p",
        fontSize: "20px",
        color: COLOR_HINT,
      })
      .setOrigin(0, 0.5);

    this.add
      .text(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 30, VERSION_STRING, {
        fontFamily: "MPLUS1p",
        fontSize: "20px",
        color: COLOR_VERSION,
      })
      .setOrigin(1, 0.5);

    const keyboard = this.input.keyboard;
    if (!keyboard) {
      // eslint-disable-next-line no-console
      console.warn("[TitleScene] keyboard plugin not available");
      return;
    }

    this.cursorKeys = keyboard.createCursorKeys();
    this.zKey = keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.Z);
    this.enterKey = keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);

    keyboard.on("keydown-UP", () => this.moveSelection(-1));
    keyboard.on("keydown-DOWN", () => this.moveSelection(1));
    keyboard.on("keydown-ENTER", () => this.confirm());
    keyboard.on("keydown-Z", () => this.confirm());

    // D3: audio wiring — play looping title BGM at the per-key volume cap (0.3).
    AudioManager.get().playBgm("rockman_title");
  }

  private moveSelection(delta: number): void {
    const n = MENU_KEYS.length;
    this.selectedIndex = (this.selectedIndex + delta + n) % n;
    this.refreshMenu();
  }

  private refreshMenu(): void {
    this.menuTexts.forEach((txt, i) => {
      const key = txt.getData("menuKey") as MenuKey;
      const label = tr(key);
      if (i === this.selectedIndex) {
        txt.setText(`> ${label} <`);
        txt.setColor(COLOR_CYAN);
      } else {
        txt.setText(label);
        txt.setColor(COLOR_WHITE);
      }
    });
  }

  private confirm(): void {
    const key = MENU_KEYS[this.selectedIndex];
    switch (key) {
      case "menu.single":
        this.scene.stop("TitleBackgroundScene");
        this.scene.start("SingleVersusScene");
        return;
      case "menu.autotest":
        this.scene.stop("TitleBackgroundScene");
        this.scene.start("AutoTestScene");
        return;
    }
  }

  override update(): void {
    // Fallback edge-detection in case the event-based handlers above are
    // interrupted by scene transitions. Kept cheap; no per-frame allocation.
    if (!this.cursorKeys) return;
    // The handlers above drive navigation; this hook is intentionally
    // a no-op beyond the guard so subclasses/tests can attach behavior.
    void this.zKey;
    void this.enterKey;
  }
}
