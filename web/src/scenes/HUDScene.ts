import Phaser from "phaser";
import {
  SCREEN_WIDTH,
  MAX_HEALTH,
  MAX_HEAT,
  MAX_HYPER,
} from "../config/constants";
import { tr } from "../i18n";
import type { Player } from "../entities/Player";

/**
 * HUDScene
 *
 * Overlay scene drawn on top of a gameplay scene. Launched via:
 *   this.scene.launch("HUDScene", { player1, player2 });
 *
 * Ports game/hud.py. Per-player column lays out name -> health ->
 * heat -> hyper -> water -> beans -> aging. Blinks the heat and hyper
 * bars on 60-frame boundaries when threshold is crossed.
 *
 * We cache Phaser GameObjects (text + Graphics) and only call
 * setText / .clear()+fillRect() each frame — never allocate per-tick.
 */

// --- layout constants (mirror Python hud.py) ---
const P1_X = 20;
const P1_Y = 20;
const P2_X = SCREEN_WIDTH - 220;
const P2_Y = 20;

const HEALTH_W = 200;
const HEALTH_H = 20;
const HEAT_W = 150;
const HEAT_H = 15;
const HYPER_W = 150;
const HYPER_H = 15;
const WATER_W = 150;
const WATER_H = 15;
const BEAN_W = 150;
const BEAN_H = 10;
const AGING_W = 150;
const AGING_H = 10;

const NAME_DY = 0;
const HEALTH_DY = 30;
const HEAT_DY = 60;
const HYPER_DY = 85;
const WATER_DY = 110;
const BEAN_DY = 135;
const AGING_DY = 155;
const HYPER_STATUS_DY = 180;

// Colors (0xRRGGBB). Mirrors Python RGB tuples.
const C_WHITE = 0xffffff;
const C_GRAY = 0x808080;
const C_GREEN = 0x00ff00;
const C_RED = 0xff0000;
const C_ORANGE = 0xffa500;
const C_CYAN = 0x00ffff;
const C_YELLOW = 0xffff00;
const C_WATER = 0x3296ff; //  50,150,255
const C_BEAN = 0x8b4513; // 139, 69, 19
const C_AGING = 0xffd700; // 255,215,  0

const FONT = { fontFamily: "MPLUS1p", fontSize: "20px", color: "#ffffff" };
const FONT_LARGE = { fontFamily: "MPLUS1p", fontSize: "24px", color: "#ffa500" };
const FONT_HYPER_STATUS = {
  fontFamily: "MPLUS1p",
  fontSize: "24px",
  color: "#ffff00",
};

interface PlayerHudSlot {
  player: Player;
  x: number;
  y: number;
  nameText: Phaser.GameObjects.Text;
  heatText: Phaser.GameObjects.Text;
  hyperText: Phaser.GameObjects.Text;
  waterText: Phaser.GameObjects.Text;
  beanText: Phaser.GameObjects.Text;
  agingText: Phaser.GameObjects.Text;
  overheatText: Phaser.GameObjects.Text;
  hyperActiveText: Phaser.GameObjects.Text;
  graphics: Phaser.GameObjects.Graphics;
}

interface HUDSceneData {
  player1: Player;
  player2: Player;
}

export class HUDScene extends Phaser.Scene {
  private slots: PlayerHudSlot[] = [];
  private frameCount = 0;
  private player1!: Player;
  private player2!: Player;

  constructor() {
    super({ key: "HUDScene" });
  }

  init(data: HUDSceneData): void {
    this.player1 = data.player1;
    this.player2 = data.player2;
  }

  create(): void {
    this.slots = [];
    this.slots.push(this.buildSlot(this.player1, P1_X, P1_Y, true));
    this.slots.push(this.buildSlot(this.player2, P2_X, P2_Y, false));
    this.frameCount = 0;
  }

  private buildSlot(
    player: Player,
    x: number,
    y: number,
    isLeft: boolean
  ): PlayerHudSlot {
    const nameLabel = isLeft ? "プレイヤー1" : "プレイヤー2";

    const nameText = this.add.text(x, y + NAME_DY, nameLabel, FONT);

    // numeric labels — positioned to the right of each bar
    const heatText = this.add.text(x + HEAT_W + 10, y + HEAT_DY, "", FONT);
    const hyperText = this.add.text(x + HYPER_W + 10, y + HYPER_DY, "", FONT);
    const waterText = this.add.text(x + WATER_W + 10, y + WATER_DY, "", FONT);
    const beanText = this.add.text(x + BEAN_W + 10, y + BEAN_DY - 5, "", FONT);
    const agingText = this.add.text(
      x + AGING_W + 10,
      y + AGING_DY - 5,
      "",
      FONT
    );

    // "OVERHEAT" blinker, centered over the heat bar
    const overheatText = this.add
      .text(x + HEAT_W / 2, y + HEAT_DY - 30, tr("hud.overheat"), FONT_LARGE)
      .setOrigin(0.5, 0);
    overheatText.setVisible(false);

    // Hyper active status text, shown below all bars
    const hyperActiveText = this.add.text(
      x,
      y + HYPER_STATUS_DY,
      tr("hud.hyper_active"),
      FONT_HYPER_STATUS
    );
    hyperActiveText.setVisible(false);

    const graphics = this.add.graphics();

    return {
      player,
      x,
      y,
      nameText,
      heatText,
      hyperText,
      waterText,
      beanText,
      agingText,
      overheatText,
      hyperActiveText,
      graphics,
    };
  }

  override update(): void {
    this.frameCount = (this.frameCount + 1) % 60;
    for (const slot of this.slots) {
      this.drawSlot(slot);
    }
  }

  private drawSlot(slot: PlayerHudSlot): void {
    const p = slot.player;
    const x = slot.x;
    const y = slot.y;
    const g = slot.graphics;
    g.clear();

    // --- Health bar ---
    const hp = Math.max(0, p.health);
    const hpPct = Math.max(0, Math.min(1, hp / MAX_HEALTH));
    g.fillStyle(C_GRAY, 1).fillRect(x, y + HEALTH_DY, HEALTH_W, HEALTH_H);
    g.fillStyle(C_GREEN, 1).fillRect(
      x,
      y + HEALTH_DY,
      HEALTH_W * hpPct,
      HEALTH_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(
      x,
      y + HEALTH_DY,
      HEALTH_W,
      HEALTH_H
    );

    // --- Heat bar (blink at >=200) ---
    const heat = p.heat;
    const heatPct = Math.max(0, Math.min(1, heat / MAX_HEAT));
    const isOverheat = heat >= 200;
    g.fillStyle(C_GRAY, 1).fillRect(x, y + HEAT_DY, HEAT_W, HEAT_H);
    let heatColor = C_RED;
    if (isOverheat) {
      heatColor = this.frameCount % 30 < 15 ? C_ORANGE : C_RED;
    }
    g.fillStyle(heatColor, 1).fillRect(
      x,
      y + HEAT_DY,
      HEAT_W * heatPct,
      HEAT_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(x, y + HEAT_DY, HEAT_W, HEAT_H);
    slot.heatText.setText(tr("hud.heat", { value: Math.floor(heat) }));

    // Overheat blinker text
    if (isOverheat) {
      slot.overheatText.setVisible(this.frameCount % 30 < 15);
    } else {
      slot.overheatText.setVisible(false);
    }

    // --- Hyper gauge (blink cyan/yellow at >=100) ---
    const hyper = p.hyperGauge;
    const hyperPct = Math.max(0, Math.min(1, hyper / MAX_HYPER));
    const isHyperReady = hyper >= 100;
    g.fillStyle(C_GRAY, 1).fillRect(x, y + HYPER_DY, HYPER_W, HYPER_H);
    let hyperColor = C_CYAN;
    if (isHyperReady) {
      hyperColor = this.frameCount % 30 < 15 ? C_YELLOW : C_CYAN;
    }
    g.fillStyle(hyperColor, 1).fillRect(
      x,
      y + HYPER_DY,
      HYPER_W * hyperPct,
      HYPER_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(x, y + HYPER_DY, HYPER_W, HYPER_H);
    slot.hyperText.setText(tr("hud.hyper", { value: Math.floor(hyper) }));

    // --- Water bar ---
    const water = p.waterLevel;
    const waterPct = Math.max(0, Math.min(1, water / 100));
    g.fillStyle(C_GRAY, 1).fillRect(x, y + WATER_DY, WATER_W, WATER_H);
    g.fillStyle(C_WATER, 1).fillRect(
      x,
      y + WATER_DY,
      WATER_W * waterPct,
      WATER_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(x, y + WATER_DY, WATER_W, WATER_H);
    slot.waterText.setText(tr("hud.water", { value: Math.floor(water) }));

    // --- Bean bar (thin) ---
    const beans = p.beans;
    const beanPct = Math.max(0, Math.min(1, beans / 100));
    g.fillStyle(C_GRAY, 1).fillRect(x, y + BEAN_DY, BEAN_W, BEAN_H);
    g.fillStyle(C_BEAN, 1).fillRect(x, y + BEAN_DY, BEAN_W * beanPct, BEAN_H);
    g.lineStyle(1, C_WHITE, 1).strokeRect(x, y + BEAN_DY, BEAN_W, BEAN_H);
    slot.beanText.setText(tr("hud.bean", { value: Math.floor(beans) }));

    // --- Aging bar (thin) ---
    const aging = p.aging;
    const agingPct = Math.max(0, Math.min(1, aging / 100));
    g.fillStyle(C_GRAY, 1).fillRect(x, y + AGING_DY, AGING_W, AGING_H);
    g.fillStyle(C_AGING, 1).fillRect(
      x,
      y + AGING_DY,
      AGING_W * agingPct,
      AGING_H
    );
    g.lineStyle(1, C_WHITE, 1).strokeRect(x, y + AGING_DY, AGING_W, AGING_H);
    slot.agingText.setText(tr("hud.aging", { value: Math.floor(aging) }));

    // --- Hyper-active status ---
    // Uses D1's optional isHyperActive field when present.
    const isHyperActive =
      (p as unknown as { isHyperActive?: boolean }).isHyperActive === true;
    slot.hyperActiveText.setVisible(isHyperActive);
  }
}
