import Phaser from "phaser";
import { SCREEN_WIDTH, SCREEN_HEIGHT, FPS } from "./config/constants";
import { BootScene } from "./scenes/BootScene";
import { TitleScene } from "./scenes/TitleScene";
import { AutoTestScene } from "./scenes/AutoTestScene";
import { SingleVersusScene } from "./scenes/SingleVersusScene";

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "game",
  width: SCREEN_WIDTH,
  height: SCREEN_HEIGHT,
  backgroundColor: 0x000000,
  pixelArt: false,
  fps: {
    target: FPS,
    forceSetTimeOut: false,
  },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [BootScene, TitleScene, AutoTestScene, SingleVersusScene],
};

new Phaser.Game(config);
