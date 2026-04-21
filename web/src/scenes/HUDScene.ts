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
 * P1 (isLeft=true) is left-anchored at (20, 20) — bars extend rightward,
 * numeric labels sit to the right of each bar.
 *
 * P2 (isLeft=false) is right-anchored. The Python port positioned P2 at
 * SCREEN_WIDTH - 220 = 1060 and reused the P1 left-anchored layout, which
 * pushes numeric labels past the 1280-wide canvas ("ヒ…", "水分: 1…",
 * "豆: 10…" are clipped). We mirror the layout around the P2 right edge
 * (= x + HEALTH_W = 1260) so every gauge and label lives inside the
 * canvas: bars are right-aligned to that edge and numeric labels sit to
 * the LEFT of their bar, right-anchored at bar_left - 10.
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
  isLeft: boolean;
  // Right edge anchor (only meaningful when isLeft=false). Equals
  // x + HEALTH_W so the widest bar still lives inside the canvas.
  rightEdge: number;
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

  /**
   * Compute the left-pixel of a gauge for the given slot/width.
   * P1: always `x` (Python behavior).
   * P2: right-align against rightEdge, so `rightEdge - width`.
   */
  private barLeft(slot: PlayerHudSlot, width: number): number {
    return slot.isLeft ? slot.x : slot.rightEdge - width;
  }

  private buildSlot(
    player: Player,
    x: number,
    y: number,
    isLeft: boolean
  ): PlayerHudSlot {
    const nameLabel = isLeft ? "プレイヤー1" : "プレイヤー2";
    const rightEdge = x + HEALTH_W;

    // Name: P1 left-anchored at (x, y); P2 right-anchored at rightEdge.
    const nameText = this.add.text(
      isLeft ? x : rightEdge,
      y + NAME_DY,
      nameLabel,
      FONT
    );
    if (!isLeft) nameText.setOrigin(1, 0);

    // Numeric labels.
    // P1 (Python): positioned at `bar_x + bar_width + 10`, i.e. right of bar.
    // P2 (mirror): right-anchored at `bar_left - 10`, i.e. left of bar.
    //   bar_left for P2 = rightEdge - W.
    //
    // For P1, BEAN/AGING use `y + DY - 5` per Python (smaller bars,
    // nudged up 5px to vertically center with the 20px font). We mirror
    // that offset on P2 so labels align with their bars.
    const p1NumericX = (w: number) => x + w + 10; // P1
    const p2NumericX = (w: number) => rightEdge - w - 10; // P2

    const heatText = this.add.text(
      isLeft ? p1NumericX(HEAT_W) : p2NumericX(HEAT_W),
      y + HEAT_DY,
      "",
      FONT
    );
    if (!isLeft) heatText.setOrigin(1, 0);

    const hyperText = this.add.text(
      isLeft ? p1NumericX(HYPER_W) : p2NumericX(HYPER_W),
      y + HYPER_DY,
      "",
      FONT
    );
    if (!isLeft) hyperText.setOrigin(1, 0);

    const waterText = this.add.text(
      isLeft ? p1NumericX(WATER_W) : p2NumericX(WATER_W),
      y + WATER_DY,
      "",
      FONT
    );
    if (!isLeft) waterText.setOrigin(1, 0);

    const beanText = this.add.text(
      isLeft ? p1NumericX(BEAN_W) : p2NumericX(BEAN_W),
      y + BEAN_DY - 5,
      "",
      FONT
    );
    if (!isLeft) beanText.setOrigin(1, 0);

    const agingText = this.add.text(
      isLeft ? p1NumericX(AGING_W) : p2NumericX(AGING_W),
      y + AGING_DY - 5,
      "",
      FONT
    );
    if (!isLeft) agingText.setOrigin(1, 0);

    // "OVERHEAT" blinker, centered over the heat bar.
    // Heat bar center = barLeft + HEAT_W/2. For P1 that's x + HEAT_W/2;
    // for P2 that's (rightEdge - HEAT_W) + HEAT_W/2 = rightEdge - HEAT_W/2.
    const heatBarLeft = isLeft ? x : rightEdge - HEAT_W;
    const overheatText = this.add
      .text(heatBarLeft + HEAT_W / 2, y + HEAT_DY - 30, tr("hud.overheat"), FONT_LARGE)
      .setOrigin(0.5, 0);
    overheatText.setVisible(false);

    // Hyper active status text, shown below all bars.
    // P1: left-anchored at x. P2: right-anchored at rightEdge.
    const hyperActiveText = this.add.text(
      isLeft ? x : rightEdge,
      y + HYPER_STATUS_DY,
      tr("hud.hyper_active"),
      FONT_HYPER_STATUS
    );
    if (!isLeft) hyperActiveText.setOrigin(1, 0);
    hyperActiveText.setVisible(false);

    const graphics = this.add.graphics();

    return {
      player,
      x,
      y,
      isLeft,
      rightEdge,
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
    const y = slot.y;
    const g = slot.graphics;
    g.clear();

    // --- Health bar ---
    const hp = Math.max(0, p.health);
    const hpPct = Math.max(0, Math.min(1, hp / MAX_HEALTH));
    const healthX = this.barLeft(slot, HEALTH_W);
    g.fillStyle(C_GRAY, 1).fillRect(healthX, y + HEALTH_DY, HEALTH_W, HEALTH_H);
    g.fillStyle(C_GREEN, 1).fillRect(
      healthX,
      y + HEALTH_DY,
      HEALTH_W * hpPct,
      HEALTH_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(
      healthX,
      y + HEALTH_DY,
      HEALTH_W,
      HEALTH_H
    );

    // --- Heat bar (blink at >=200) ---
    const heat = p.heat;
    const heatPct = Math.max(0, Math.min(1, heat / MAX_HEAT));
    const isOverheat = heat >= 200;
    const heatX = this.barLeft(slot, HEAT_W);
    g.fillStyle(C_GRAY, 1).fillRect(heatX, y + HEAT_DY, HEAT_W, HEAT_H);
    let heatColor = C_RED;
    if (isOverheat) {
      heatColor = this.frameCount % 30 < 15 ? C_ORANGE : C_RED;
    }
    g.fillStyle(heatColor, 1).fillRect(
      heatX,
      y + HEAT_DY,
      HEAT_W * heatPct,
      HEAT_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(heatX, y + HEAT_DY, HEAT_W, HEAT_H);
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
    const hyperX = this.barLeft(slot, HYPER_W);
    g.fillStyle(C_GRAY, 1).fillRect(hyperX, y + HYPER_DY, HYPER_W, HYPER_H);
    let hyperColor = C_CYAN;
    if (isHyperReady) {
      hyperColor = this.frameCount % 30 < 15 ? C_YELLOW : C_CYAN;
    }
    g.fillStyle(hyperColor, 1).fillRect(
      hyperX,
      y + HYPER_DY,
      HYPER_W * hyperPct,
      HYPER_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(hyperX, y + HYPER_DY, HYPER_W, HYPER_H);
    slot.hyperText.setText(tr("hud.hyper", { value: Math.floor(hyper) }));

    // --- Water bar ---
    const water = p.waterLevel;
    const waterPct = Math.max(0, Math.min(1, water / 100));
    const waterX = this.barLeft(slot, WATER_W);
    g.fillStyle(C_GRAY, 1).fillRect(waterX, y + WATER_DY, WATER_W, WATER_H);
    g.fillStyle(C_WATER, 1).fillRect(
      waterX,
      y + WATER_DY,
      WATER_W * waterPct,
      WATER_H
    );
    g.lineStyle(2, C_WHITE, 1).strokeRect(waterX, y + WATER_DY, WATER_W, WATER_H);
    slot.waterText.setText(tr("hud.water", { value: Math.floor(water) }));

    // --- Bean bar (thin) ---
    const beans = p.beans;
    const beanPct = Math.max(0, Math.min(1, beans / 100));
    const beanX = this.barLeft(slot, BEAN_W);
    g.fillStyle(C_GRAY, 1).fillRect(beanX, y + BEAN_DY, BEAN_W, BEAN_H);
    g.fillStyle(C_BEAN, 1).fillRect(beanX, y + BEAN_DY, BEAN_W * beanPct, BEAN_H);
    g.lineStyle(1, C_WHITE, 1).strokeRect(beanX, y + BEAN_DY, BEAN_W, BEAN_H);
    slot.beanText.setText(tr("hud.bean", { value: Math.floor(beans) }));

    // --- Aging bar (thin) ---
    const aging = p.aging;
    const agingPct = Math.max(0, Math.min(1, aging / 100));
    const agingX = this.barLeft(slot, AGING_W);
    g.fillStyle(C_GRAY, 1).fillRect(agingX, y + AGING_DY, AGING_W, AGING_H);
    g.fillStyle(C_AGING, 1).fillRect(
      agingX,
      y + AGING_DY,
      AGING_W * agingPct,
      AGING_H
    );
    g.lineStyle(1, C_WHITE, 1).strokeRect(agingX, y + AGING_DY, AGING_W, AGING_H);
    slot.agingText.setText(tr("hud.aging", { value: Math.floor(aging) }));

    // --- Hyper-active status ---
    // Uses D1's optional isHyperActive field when present.
    const isHyperActive =
      (p as unknown as { isHyperActive?: boolean }).isHyperActive === true;
    slot.hyperActiveText.setVisible(isHyperActive);
  }
}
