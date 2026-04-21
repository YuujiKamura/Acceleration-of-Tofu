import Phaser from "phaser";
import { CYAN, WHITE } from "../config/colors";
import type { Player } from "./Player";

/**
 * Projectile
 *
 * Minimal port of game/projectile.py BeamProjectile / BallisticProjectile.
 * A Projectile is a kinematic point that advances at (vx, vy) per frame
 * (60fps base) and is considered expired either when its lifetime
 * decrements to zero or when it leaves the circular arena.
 *
 * It owns a small Phaser GameObject (Arc) so the hosting scene does not
 * need to manage render primitives separately — the caller only has to
 * add the sprite via `scene.add.existing(proj.sprite)` and destroy via
 * `proj.destroy()` when expired.
 */
export type ProjectileType = "beam" | "ballistic";

export class Projectile {
  public readonly type: ProjectileType;
  public x: number;
  public y: number;
  public vx: number;
  public vy: number;
  public damage: number;
  public owner: Player;
  public radius: number;
  public lifetimeFrames: number;
  public isExpired: boolean;
  public sprite: Phaser.GameObjects.Arc;

  constructor(
    scene: Phaser.Scene,
    type: ProjectileType,
    x: number,
    y: number,
    angleRad: number,
    damage: number,
    owner: Player
  ) {
    this.type = type;
    this.x = x;
    this.y = y;
    this.damage = damage;
    this.owner = owner;
    this.isExpired = false;

    if (type === "beam") {
      const speed = 15;
      this.vx = Math.cos(angleRad) * speed;
      this.vy = Math.sin(angleRad) * speed;
      this.radius = 4;
      this.lifetimeFrames = 60;
    } else {
      const speed = 8;
      this.vx = Math.cos(angleRad) * speed;
      this.vy = Math.sin(angleRad) * speed;
      this.radius = 6;
      this.lifetimeFrames = 90;
    }

    const color = type === "beam" ? CYAN : 0xffff00;
    this.sprite = scene.add.circle(x, y, this.radius, color);
    // thin white outline so beams read against dark bg
    this.sprite.setStrokeStyle(1, WHITE);
  }

  /**
   * Advance one logical tick. `dtScale` normalizes delta-time to 60fps
   * ticks (i.e. dtScale=1.0 at 60fps, 2.0 at 30fps). For a first
   * milestone we accept a passthrough of 1.0 from the scene.
   */
  update(dtScale: number, arenaCenterX: number, arenaCenterY: number, arenaRadius: number): void {
    if (this.isExpired) return;

    this.x += this.vx * dtScale;
    this.y += this.vy * dtScale;
    this.sprite.setPosition(this.x, this.y);

    this.lifetimeFrames -= dtScale;
    if (this.lifetimeFrames <= 0) {
      this.isExpired = true;
      return;
    }

    const ddx = this.x - arenaCenterX;
    const ddy = this.y - arenaCenterY;
    if (ddx * ddx + ddy * ddy > arenaRadius * arenaRadius) {
      this.isExpired = true;
    }
  }

  /**
   * Circle-circle hit test. We intentionally DO NOT treat the owner as
   * hittable — bullets never collide with their shooter.
   */
  collidesWith(player: Player): boolean {
    if (this.isExpired) return false;
    if (player === this.owner) return false;
    const dx = this.x - player.x;
    const dy = this.y - player.y;
    const r = this.radius + player.radius;
    return dx * dx + dy * dy <= r * r;
  }

  destroy(): void {
    this.isExpired = true;
    this.sprite.destroy();
  }
}
