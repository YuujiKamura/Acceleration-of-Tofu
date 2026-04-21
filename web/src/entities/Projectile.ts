import Phaser from "phaser";
import { CYAN, WHITE, YELLOW, ORANGE } from "../config/colors";
import type { Player } from "./Player";

/**
 * Projectile
 *
 * Port of game/projectile.py covering the two active subclasses:
 *   - BeamProjectile: straight fast line shot (weapon_a)
 *   - BallisticProjectile: arc-like slower shot with gravity-like vy ramp
 *     (weapon_b). Expires at lifetimeFrames=60 or when outside arena.
 *
 * We keep a single concrete class + `type` discriminator for now instead
 * of a subclass hierarchy, because:
 *   (a) the TS code has just two variants, both trivial to branch on;
 *   (b) the Phaser sprite wrapping doesn't benefit from polymorphism;
 *   (c) Combat.ts needs to read `type`, `owner`, `damage` uniformly.
 *
 * The hosting scene does NOT need to manage render primitives — the Arc
 * is created in the constructor and destroyed via `proj.destroy()`.
 */
export type ProjectileType = "beam" | "ballistic";

// Tuned to match game/projectile.py.
const BEAM_SPEED = 15;
const BEAM_RADIUS = 4;
const BEAM_LIFETIME = 60;

const BALLISTIC_SPEED = 8;
const BALLISTIC_RADIUS = 6;
const BALLISTIC_LIFETIME = 60; // spec: 60 frames (shorter than beam's reach)
// per-frame gravity-like pull on vy. Matches the spec's "vy += 0.15/frame".
const BALLISTIC_GRAVITY = 0.15;

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
      this.vx = Math.cos(angleRad) * BEAM_SPEED;
      this.vy = Math.sin(angleRad) * BEAM_SPEED;
      this.radius = BEAM_RADIUS;
      this.lifetimeFrames = BEAM_LIFETIME;
    } else {
      // ballistic
      this.vx = Math.cos(angleRad) * BALLISTIC_SPEED;
      this.vy = Math.sin(angleRad) * BALLISTIC_SPEED;
      this.radius = BALLISTIC_RADIUS;
      this.lifetimeFrames = BALLISTIC_LIFETIME;
    }

    // Color scheme mirrors the Python source: beam=CYAN/MAGENTA,
    // ballistic=YELLOW/ORANGE. We pick per owner (P1 uses the "cool" variant).
    const color =
      type === "beam"
        ? CYAN
        : owner.isPlayer1
        ? YELLOW
        : ORANGE;
    this.sprite = scene.add.circle(x, y, this.radius, color);
    this.sprite.setStrokeStyle(1, WHITE);
  }

  /**
   * Advance one logical tick. `dtScale` normalizes delta-time to 60fps
   * ticks (i.e. dtScale=1.0 at 60fps, 2.0 at 30fps). For a first
   * milestone we accept a passthrough of 1.0 from the scene.
   */
  update(
    dtScale: number,
    arenaCenterX: number,
    arenaCenterY: number,
    arenaRadius: number
  ): void {
    if (this.isExpired) return;

    // Ballistic shots get a gravity-like pull on vy each frame. Beam is
    // a straight line — no acceleration. We apply gravity BEFORE moving
    // so the first frame of the arc already bends.
    if (this.type === "ballistic") {
      this.vy += BALLISTIC_GRAVITY * dtScale;
    }

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

/**
 * Factory helper — preferred over `new Projectile(...)` at call sites
 * because it lets us later swap to dedicated subclasses without touching
 * Player.ts. Combat.ts / Player.ts use this; the ctor is kept public so
 * any external test can still construct directly.
 */
export function createProjectile(
  scene: Phaser.Scene,
  type: ProjectileType,
  x: number,
  y: number,
  angleRad: number,
  damage: number,
  owner: Player
): Projectile {
  return new Projectile(scene, type, x, y, angleRad, damage, owner);
}
