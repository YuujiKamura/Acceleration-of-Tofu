import Phaser from "phaser";

/**
 * HyperEffect - literal 1:1 port of legacy/pygbag/game/player.py lines 1000-1030.
 *
 * Standalone effect drawn in addition to Player.draw's inline hyper glow
 * (py lines 823-838). Follows its owner each frame.
 */
export interface HyperOwner {
  x: number;
  y: number;
}

export class HyperEffect {
  public x: number;
  public y: number;
  public readonly owner: HyperOwner;
  public duration: number;
  public readonly maxDuration: number;
  public radius = 10; // py line 1008
  public isDead = false;

  private g: Phaser.GameObjects.Graphics;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    owner: HyperOwner,
    duration: number
  ) {
    this.x = x;
    this.y = y;
    this.owner = owner;
    this.duration = duration;
    this.maxDuration = duration;
    this.g = scene.add.graphics();
  }

  /** py lines 1011-1018 */
  update(): void {
    this.duration -= 1;
    if (this.duration <= 0) {
      this.isDead = true;
    }
    this.x = this.owner.x;
    this.y = this.owner.y;
    this.render();
  }

  /** py lines 1020-1030 */
  private render(): void {
    this.g.clear();
    if (this.isDead) return;

    // py line 1025: alpha = int(255 * (self.duration / self.max_duration))
    const alpha = this.duration / this.maxDuration;
    // py line 1026
    const radius =
      this.radius + Math.floor((this.maxDuration - this.duration) / 2);

    // py line 1029: color = (200, 200, 255, alpha)
    const color = 0xc8c8ff;

    // py line 1030: for r in range(radius - 5, radius + 6, 3)
    for (let r = radius - 5; r < radius + 6; r += 3) {
      this.g.lineStyle(1, color, alpha);
      this.g.strokeCircle(Math.floor(this.x), Math.floor(this.y), r);
    }
  }

  destroy(): void {
    this.g.destroy();
  }
}
