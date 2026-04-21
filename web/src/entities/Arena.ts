import Phaser from "phaser";
import { WHITE, RED, GRAY } from "../config/colors";

/**
 * Arena
 *
 * Port of game/arena.py::Arena for the web build. Owns the circular
 * playfield rendering and exposes the geometry helpers the rest of the
 * scene code needs (containment test + clamp-to-inside).
 *
 * The warning ring pulses subtly via scene.time to mimic the Python
 * source's border_alpha oscillation, at a fixed cheap cost (one alpha
 * recalc + one graphics redraw per frame).
 */
export class Arena {
  public readonly centerX: number;
  public readonly centerY: number;
  public readonly radius: number;
  public readonly warningRadius: number;

  private readonly scene: Phaser.Scene;
  private warningG: Phaser.GameObjects.Graphics | null = null;

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
  }

  /**
   * Draw the outer boundary, inner warning ring (dashed), and a small
   * floor crosshair. Call once from Scene.create().
   *
   * After this, calling update() each frame will re-render only the
   * warning ring with a pulsed alpha value.
   */
  create(): void {
    const g = this.scene.add.graphics();

    // Outer boundary: solid 3px white.
    g.lineStyle(3, WHITE, 1.0);
    g.strokeCircle(this.centerX, this.centerY, this.radius);

    // Floor cross-hair (small, grey, for orientation).
    const arm = 12;
    g.lineStyle(1, GRAY, 0.5);
    g.beginPath();
    g.moveTo(this.centerX - arm, this.centerY);
    g.lineTo(this.centerX + arm, this.centerY);
    g.moveTo(this.centerX, this.centerY - arm);
    g.lineTo(this.centerX, this.centerY + arm);
    g.strokePath();

    // Separate graphics layer for the pulsing warning ring so we can
    // clear+redraw cheaply each frame without trashing the boundary.
    this.warningG = this.scene.add.graphics();
    this.redrawWarning(0.4);
  }

  /**
   * Recompute warning-ring alpha and redraw. Called from scene.update().
   * Kept cheap: one sin() + one graphics.clear()/strokeCircle per frame.
   */
  update(): void {
    if (!this.warningG) return;
    // 60-frame period pulse, alpha in [0.2, 0.6].
    const t = this.scene.time.now / 1000; // seconds
    const phase = Math.sin((t * 2 * Math.PI) / 1.0); // 1Hz
    const alpha = 0.4 + 0.2 * phase;
    this.redrawWarning(alpha);
  }

  private redrawWarning(alpha: number): void {
    if (!this.warningG) return;
    this.warningG.clear();

    // Emulate a "dashed" ring with short segments. Cheap approximation:
    // 48 dashes evenly spaced around the circle.
    this.warningG.lineStyle(1, RED, alpha);
    const dashes = 48;
    const segArc = (Math.PI * 2) / dashes;
    const dashSpan = segArc * 0.5;
    for (let i = 0; i < dashes; i++) {
      const a0 = i * segArc;
      const a1 = a0 + dashSpan;
      const x0 = this.centerX + Math.cos(a0) * this.warningRadius;
      const y0 = this.centerY + Math.sin(a0) * this.warningRadius;
      const x1 = this.centerX + Math.cos(a1) * this.warningRadius;
      const y1 = this.centerY + Math.sin(a1) * this.warningRadius;
      this.warningG.beginPath();
      this.warningG.moveTo(x0, y0);
      this.warningG.lineTo(x1, y1);
      this.warningG.strokePath();
    }
  }

  /** Strictly inside (distance from center < radius). Mirrors Python. */
  isInside(x: number, y: number): boolean {
    const dx = x - this.centerX;
    const dy = y - this.centerY;
    return dx * dx + dy * dy < this.radius * this.radius;
  }

  /**
   * Project (x, y) toward the center so it lies on the arena boundary
   * when outside. Points already inside are returned unchanged.
   */
  clampInside(x: number, y: number): { x: number; y: number } {
    const dx = x - this.centerX;
    const dy = y - this.centerY;
    const distSq = dx * dx + dy * dy;
    const rSq = this.radius * this.radius;
    if (distSq <= rSq) {
      return { x, y };
    }
    const dist = Math.sqrt(distSq) || 1;
    const r = this.radius - 1;
    return {
      x: this.centerX + (dx / dist) * r,
      y: this.centerY + (dy / dist) * r,
    };
  }
}
