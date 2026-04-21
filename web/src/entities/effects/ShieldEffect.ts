import Phaser from "phaser";
import { SHIELD_DURATION } from "../../config/constants";

/**
 * ShieldEffect - literal 1:1 port of legacy/pygbag/game/player.py lines 98-178.
 *
 * Owner interface: needs .x, .y, .radius — we avoid importing Player to
 * prevent a circular module cycle.
 */
export interface ShieldOwner {
  x: number;
  y: number;
  radius: number;
}

interface RingSpec {
  radius: number;
  speed: number;
  angle: number;
  width: number;
}

export class ShieldEffect {
  public readonly owner: ShieldOwner;
  public duration: number = SHIELD_DURATION;
  public readonly maxDuration: number = SHIELD_DURATION;
  public readonly baseRadius: number;
  public readonly ringCount = 3; // py line 105
  public rings: RingSpec[] = [];
  public isDead = false;

  private g: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene, owner: ShieldOwner) {
    this.owner = owner;
    this.baseRadius = owner.radius + 12; // py line 104

    // py lines 110-116
    for (let i = 0; i < this.ringCount; i++) {
      this.rings.push({
        radius: this.baseRadius * (0.8 + i * 0.2),
        speed: 0.5 + i * 0.2,
        angle: Math.random() * 2 * Math.PI,
        width: 2 + i,
      });
    }
    this.g = scene.add.graphics();
  }

  /** py lines 118-126 */
  update(): void {
    this.duration -= 1;
    if (this.duration <= 0) {
      this.isDead = true;
    }
    for (const ring of this.rings) {
      ring.angle = (ring.angle + ring.speed * 0.1) % (2 * Math.PI);
    }
    this.render();
  }

  /** py lines 128-178 */
  private render(): void {
    this.g.clear();
    if (this.isDead) return;

    const x = Math.floor(this.owner.x);
    const y = Math.floor(this.owner.y);

    // py line 137
    const pulseFactor = 0.2 * Math.sin(this.duration * 0.1) + 1.0;
    // py line 140
    const alphaFactor = this.duration / this.maxDuration;

    for (const ring of this.rings) {
      // py lines 145-149
      const timeFactor = (this.duration / 20) % 1.0;
      const r = Math.floor(0 + timeFactor * 100);
      const gg = Math.floor(150 + timeFactor * 100);
      const b = Math.floor(200 + timeFactor * 55);
      const color = (r << 16) | (gg << 8) | b;

      // py line 152
      const actualRadius = ring.radius * pulseFactor;
      // py line 155
      const width = Math.max(1, Math.floor(ring.width * alphaFactor * 1.5));

      // py line 158: segments = 12
      const segments = 12;
      for (let i = 0; i < segments; i++) {
        // py line 160
        const a = ring.angle + i * ((2 * Math.PI) / segments);
        // py lines 162-163
        const startAngle = a - 0.2;
        const endAngle = a + 0.2;

        // py line 178: pygame.draw.arc in rect (x-r,y-r,2r,2r)
        // Phaser: g.arc(x, y, radius, startAngle, endAngle, anticlockwise)
        // then stroke the path.
        this.g.lineStyle(width, color, 1.0);
        this.g.beginPath();
        this.g.arc(x, y, actualRadius, startAngle, endAngle, false);
        this.g.strokePath();
      }
    }
  }

  destroy(): void {
    this.g.destroy();
  }
}
