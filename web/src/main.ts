import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT, FPS } from "./config/constants";
import { BootScene } from "./scenes/BootScene";
import { TitleScene } from "./scenes/TitleScene";
import { AutoTestScene } from "./scenes/AutoTestScene";
import { SingleVersusScene } from "./scenes/SingleVersusScene";
import { HUDScene } from "./scenes/HUDScene";
import { PauseScene } from "./scenes/PauseScene";
import { TitleBackgroundScene } from "./scenes/TitleBackgroundScene";
// D3: audio wiring — bring in the AudioManager singleton.
import { AudioManager } from "./systems/Audio";

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "game",
  width: SCREEN_WIDTH,
  height: SCREEN_HEIGHT,
  backgroundColor: 0x000000,
  pixelArt: false,
  render: {
    // WebGL のバックバッファを保持する。未設定だと canvas.toDataURL や
    // renderer.snapshot が黒画像しか返さず e2e ハーネスで何も見えない。
    preserveDrawingBuffer: true,
  },
  fps: {
    target: FPS,
    forceSetTimeOut: false,
  },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  // TitleBackgroundScene は TitleScene より前に登録することで
  // render 順が下層になり、TitleScene の UI が上に乗る。
  scene: [BootScene, TitleBackgroundScene, TitleScene, AutoTestScene, SingleVersusScene, HUDScene, PauseScene],
};

// D3: audio wiring — initialize AudioManager and install the global M-key mute listener.
const game = new Phaser.Game(config);
AudioManager.init(game);

// e2e スナップショットハーネス (web/e2e/snapshot.mjs) から
// page.evaluate(() => window.game.renderer.snapshot(...)) で呼べるように公開。
// production でも露出しておく (秘匿情報なし)。
(window as unknown as { game: Phaser.Game }).game = game;
