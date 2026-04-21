import Phaser from "phaser";

/**
 * DashRing - literal 1:1 port of legacy/pygbag/game/player.py lines 23-95.
 *
 * Python draw() creates a separate pygame.Surface for the ellipse, outlines
 * it with width=2, then rotates it by -angle degrees about its center. We
 * emulate this by drawing the unrotated ellipse into a child Graphics object,
 * then setting its angle (deg) and position.
 */
export class DashRing {
  public x: number;
  public y: number;
  public duration: number;
  public readonly maxDuration: number;
  public readonly startRadius = 10; // py line 30
  public radius: number;
  public readonly maxRadius = 40; // py line 32
  public directionX: number;
  public directionY: number;

  private g: Phaser.GameObjects.Graphics;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    duration: number,
    directionX = 0,
    directionY = 0
  ) {
    this.x = x;
    this.y = y;
    this.duration = duration;
    this.maxDuration = duration;
    this.radius = this.startRadius;
    this.directionX = directionX;
    this.directionY = directionY;
    // py lines 37-39: if no direction, default (1, 0)
    if (this.directionX === 0 && this.directionY === 0) {
      this.directionX = 1;
    }
    this.g = scene.add.graphics();
  }

  /** py lines 40-45 */
  update(): void {
    this.duration -= 1;
    const progress = 1.0 - this.duration / this.maxDuration;
    this.radius =
      this.startRadius + (this.maxRadius - this.startRadius) * progress;
    this.render();
  }

  /** py lines 47-90 */
  private render(): void {
    this.g.clear();
    if (this.isDead) return;

    // py line 49: alpha = int(255 * (self.duration / self.max_duration))
    const alpha = (255 * (this.duration / this.maxDuration)) / 255;
    // py line 50: color = (100, 200, 255, alpha)
    const color = 0x64c8ff;

    // py lines 52-59: normalize direction vector
    const length = Math.sqrt(
      this.directionX * this.directionX + this.directionY * this.directionY
    );
    let normDirX: number;
    let normDirY: number;
    if (length > 0) {
      normDirX = this.directionX / length;
      normDirY = this.directionY / length;
    } else {
      normDirX = 1;
      normDirY = 0;
    }

    // py lines 62-63
    const ellipseWidth = Math.floor(this.radius * 0.8);
    const ellipseHeight = Math.floor(this.radius * 1.5);

    // py line 66: angle = math.degrees(math.atan2(norm_dir_y, norm_dir_x))
    const angle = (Math.atan2(normDirY, normDirX) * 180) / Math.PI;

    // py line 81: pygame.draw.ellipse(ellipse_surface, color, pygame.Rect(0, 0, w, h), 2)
    // Draw unrotated ellipse centered at (x,y), then rotate the Graphics
    // container. Phaser rotation pivots around the Graphics origin (0,0) by
    // default, so we position at (x,y) and draw relative to origin.
    this.g.lineStyle(2, color, alpha);
    // Phaser strokeEllipse(centerX, centerY, width, height)
    this.g.strokeEllipse(0, 0, ellipseWidth, ellipseHeight);

    this.g.setPosition(Math.floor(this.x), Math.floor(this.y));
    // py line 84: pygame.transform.rotate(surface, -angle) -- clockwise.
    // Phaser setAngle is clockwise-positive in degrees, so -angle matches.
    this.g.setAngle(-angle);
  }

  /** py lines 92-95 */
  get isDead(): boolean {
    return this.duration <= 0;
  }

  destroy(): void {
    this.g.destroy();
  }
}
