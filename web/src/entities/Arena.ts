import Phaser from "phaser";
import { ORANGE, RED } from "../config/colors";

/**
 * Arena
 *
 * Literal 1:1 port of legacy/pygbag/game/arena.py::Arena.draw() and
 * Arena.update(). Every color, every radius, every pulsing-alpha value
 * below matches the Python source byte-for-byte.
 *
 * Python reference (legacy/pygbag/game/arena.py):
 *   - update()  : lines 18-27  (border_alpha oscillation 100..255)
 *   - draw()    : lines 29-52  (4 primitives: bg fill, water overlay,
 *                               warning ring with RGB-scaled color,
 *                               red rounded-rect border)
 *   - is_inside : lines 54-57
 *   - is_near_border : lines 59-62
 *   - constrain_position : lines 64-75
 */
export class Arena {
  public readonly centerX: number;
  public readonly centerY: number;
  public readonly radius: number;
  public readonly warningRadius: number;

  // Oscillating border alpha counter (Python: self.border_alpha).
  public borderAlpha: number;
  public borderAlphaDirection: number;
  public borderAlphaSpeed: number;

  private readonly scene: Phaser.Scene;
  private readonly g: Phaser.GameObjects.Graphics;

  constructor(
    scene: Phaser.Scene,
    centerX: number,
    centerY: number,
    radius: number,
    warningRadius: number
  ) {
    this.scene = scene;
    this.centerX = centerX;
    this.centerY = centerY;
    this.radius = radius;
    this.warningRadius = warningRadius;

    // Python __init__ lines 14-16.
    this.borderAlpha = 255;
    this.borderAlphaDirection = -1;
    this.borderAlphaSpeed = 5;

    this.g = this.scene.add.graphics();
  }

  /**
   * Backwards-compat entry point preserved so existing scenes
   * (AutoTestScene) keep compiling. Performs an initial render so the
   * arena is visible from frame 0; subsequent per-frame redraws are
   * driven by render(), invoked by the scene.
   */
  create(): void {
    this.render();
  }

  /**
   * Pure counter oscillation. Mirrors Python Arena.update()
   * (lines 18-27) with no drawing side-effects.
   */
  update(): void {
    this.borderAlpha += this.borderAlphaDirection * this.borderAlphaSpeed;
    if (this.borderAlpha <= 100) {
      this.borderAlpha = 100;
      this.borderAlphaDirection = 1;
    } else if (this.borderAlpha >= 255) {
      this.borderAlpha = 255;
      this.borderAlphaDirection = -1;
    }
  }

  /**
   * Literal port of Python Arena.draw() (lines 29-52). Clears and
   * repaints the four primitives in source order.
   */
  render(): void {
    const g = this.g;
    g.clear();

    // Step 1 (Python line 32): solid fill dark blue-gray circle
    //   (20, 20, 40) = 0x141428 at center, radius=ARENA_RADIUS.
    g.fillStyle(0x141428, 1);
    g.fillCircle(this.centerX, this.centerY, this.radius);

    // Step 2 (Python lines 35-39): semi-transparent blue water-zone
    //   circle (50, 100, 200, 100) = 0x3264C8 @ alpha 100/255,
    //   radius=100 at the arena center.
    g.fillStyle(0x3264c8, 100 / 255);
    g.fillCircle(this.centerX, this.centerY, 100);

    // Step 3 (Python lines 42-49): orange warning ring at
    //   ARENA_WARNING_RADIUS. The alpha modulation is done via RGB
    //   darkening (NOT true alpha), exactly as the Python source does.
    //   warning_color = (int(ORANGE[0]*ratio), int(ORANGE[1]*ratio),
    //                    int(ORANGE[2]*ratio))
    const alphaRatio = this.borderAlpha / 255.0;
    const orR = (ORANGE >> 16) & 0xff;
    const orG = (ORANGE >> 8) & 0xff;
    const orB = ORANGE & 0xff;
    const scaled =
      (Math.floor(orR * alphaRatio) << 16) |
      (Math.floor(orG * alphaRatio) << 8) |
      Math.floor(orB * alphaRatio);
    g.lineStyle(2, scaled, 1);
    g.strokeCircle(this.centerX, this.centerY, this.warningRadius);

    // Step 4 (Python line 52): red rounded-rectangle border, width=3,
    //   border_radius=self.radius (== half the side length, producing
    //   an inscribed-circle-wrapping rectangle visual).
    const x = this.centerX - this.radius;
    const y = this.centerY - this.radius;
    const side = this.radius * 2;
    g.lineStyle(3, RED, 1);
    g.strokeRoundedRect(x, y, side, side, this.radius);
  }

  /**
   * Python Arena.is_inside() (lines 54-57). Strictly inside
   * (distance < radius), matching the Python `<` comparison.
   */
  isInside(x: number, y: number): boolean {
    const dx = x - this.centerX;
    const dy = y - this.centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    return distance < this.radius;
  }

  /**
   * Python Arena.is_near_border() (lines 59-62). True when the point
   * lies in the annulus [warning_radius, radius).
   */
  isNearBorder(x: number, y: number): boolean {
    const dx = x - this.centerX;
    const dy = y - this.centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    return this.warningRadius <= distance && distance < this.radius;
  }

  /**
   * Python Arena.constrain_position() (lines 64-75). Projects points
   * outside the arena onto the circle of radius (radius - 1).
   * The `- 1` is preserved literally from the source.
   */
  clampInside(x: number, y: number): { x: number; y: number } {
    const dx = x - this.centerX;
    const dy = y - this.centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance >= this.radius) {
      const angle = Math.atan2(dy, dx);
      return {
        x: this.centerX + Math.cos(angle) * (this.radius - 1),
        y: this.centerY + Math.sin(angle) * (this.radius - 1),
      };
    }
    return { x, y };
  }
}
