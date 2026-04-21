import Phaser from "phaser";
import {
  WHITE,
  CYAN,
  MAGENTA,
  YELLOW,
  ORANGE,
  GREEN,
  RED,
} from "../config/colors";
import type { Player } from "./Player";

/**
 * Projectile
 *
 * Literal 1:1 port of the draw() methods in `legacy/pygbag/game/projectile.py`.
 * A single concrete TS class + `type` discriminator covers all four pygame
 * subclasses (BeamProjectile, BallisticProjectile, MeleeProjectile,
 * SoybeanCollectible) plus the base Projectile's white-circle fallback.
 *
 * Rendering: each instance owns a `Phaser.GameObjects.Graphics` (not an Arc).
 * `render()` clears it and redraws per `type` every frame — exactly what
 * pygame did every draw call. `update()` invokes `render()` at the tail so
 * existing scenes (which only call update) continue to work without edits.
 */
export type ProjectileType = "beam" | "ballistic" | "melee" | "soybean";

// Per-Python-subclass constants ---------------------------------------------
// Values transcribed from projectile.py line-for-line.

// BeamProjectile: speed=15, radius=3, length=20
const BEAM_SPEED = 15;
const BEAM_RADIUS = 3;
const BEAM_LENGTH = 20;
const BEAM_LIFETIME = 60;

// BallisticProjectile: speed=8, radius=6
const BALLISTIC_SPEED = 8;
const BALLISTIC_RADIUS = 6;
const BALLISTIC_LIFETIME = 60;
// Preserved from the previous TS pass: gravity-like vy pull per frame.
const BALLISTIC_GRAVITY = 0.15;

// MeleeProjectile: speed=12, radius=15, lifetime=10
const MELEE_SPEED = 12;
const MELEE_RADIUS = 15;
const MELEE_LIFETIME = 10;

// SoybeanCollectible: radius=4, lifetime=300 (5s @60fps)
const SOYBEAN_RADIUS = 4;
const SOYBEAN_LIFETIME = 300;

// Base Projectile default radius
const BASE_RADIUS = 5;

// SoybeanCollectible color (210, 180, 140) -> 0xd2b48c
const SOYBEAN_COLOR = 0xd2b48c;

export class Projectile {
  public readonly type: ProjectileType;
  public x: number;
  public y: number;
  public vx: number;
  public vy: number;
  public angle: number;
  public damage: number;
  public owner: Player;
  public radius: number;
  public lifetimeFrames: number;
  public isExpired: boolean;
  public sprite: Phaser.GameObjects.Graphics;

  // Homing fields — literal port of Projectile base class in
  // legacy/pygbag/game/projectile.py:21-22. Per-type values are set in the
  // switch below to mirror the BeamProjectile/BallisticProjectile subclasses.
  public homing: boolean;
  public homingStrength: number;
  /**
   * Optional homing target. Since `Player` has no persistent `opponent`
   * reference (scenes pass the opponent into Player.update each tick), and
   * the existing Projectile.update(dtScale, cx, cy, arenaRadius) signature
   * is consumed by 3 scenes + would ripple if changed, we store the target
   * on the Projectile itself. The caller (Player.ts at fire time, or a
   * scene passing the opponent through createProjectile's optional arg) is
   * expected to set this; if null, homing silently no-ops — keeping this
   * drop-in backward compatible with callers that haven't been updated.
   */
  public target: Player | null;

  constructor(
    scene: Phaser.Scene,
    type: ProjectileType,
    x: number,
    y: number,
    angleRad: number,
    damage: number,
    owner: Player,
    target: Player | null = null
  ) {
    this.type = type;
    this.x = x;
    this.y = y;
    this.angle = angleRad;
    this.damage = damage;
    this.owner = owner;
    this.isExpired = false;
    this.target = target;

    // Defaults from Python base class (projectile.py:21-22).
    this.homing = false;
    this.homingStrength = 0.0;

    switch (type) {
      case "beam": {
        this.vx = Math.cos(angleRad) * BEAM_SPEED;
        this.vy = Math.sin(angleRad) * BEAM_SPEED;
        this.radius = BEAM_RADIUS;
        this.lifetimeFrames = BEAM_LIFETIME;
        // BeamProjectile: projectile.py:95-96 — homing_strength=0.02
        this.homing = true;
        this.homingStrength = 0.02;
        break;
      }
      case "ballistic": {
        this.vx = Math.cos(angleRad) * BALLISTIC_SPEED;
        this.vy = Math.sin(angleRad) * BALLISTIC_SPEED;
        this.radius = BALLISTIC_RADIUS;
        this.lifetimeFrames = BALLISTIC_LIFETIME;
        // BallisticProjectile: projectile.py:123-124 — homing_strength=0.03
        this.homing = true;
        this.homingStrength = 0.03;
        break;
      }
      case "melee": {
        this.vx = Math.cos(angleRad) * MELEE_SPEED;
        this.vy = Math.sin(angleRad) * MELEE_SPEED;
        this.radius = MELEE_RADIUS;
        this.lifetimeFrames = MELEE_LIFETIME;
        // MeleeProjectile: projectile.py:148 — homing = False
        break;
      }
      case "soybean": {
        this.vx = 0;
        this.vy = 0;
        this.radius = SOYBEAN_RADIUS;
        this.lifetimeFrames = SOYBEAN_LIFETIME;
        // SoybeanCollectible is a pickup, not a weapon — non-homing.
        break;
      }
      default: {
        // Base Projectile fallback (shouldn't normally hit in the TS union,
        // but matches the Python base class's white-filled circle at radius=5)
        this.vx = 0;
        this.vy = 0;
        this.radius = BASE_RADIUS;
        this.lifetimeFrames = 60;
      }
    }

    this.sprite = scene.add.graphics();
    this.render();
  }

  /**
   * Literal port of `Projectile.home_towards(target)` in
   * legacy/pygbag/game/projectile.py:55-69. Nudges `this.angle` toward the
   * target direction by `homingStrength` of the shortest-arc angular delta,
   * then re-derives vx/vy from the new angle and the current speed so the
   * bullet keeps its magnitude (matters for ballistic, which also has
   * gravity mutating vy between frames — we reconstitute from angle here
   * and let gravity re-apply on the next tick, same ordering as Python).
   */
  homeTowards(target: { x: number; y: number }): void {
    const dx = target.x - this.x;
    const dy = target.y - this.y;
    const targetAngle = Math.atan2(dy, dx);

    // Wrap diff to [-PI, PI] — Python uses `(diff + pi) % (2*pi) - pi`.
    // JS `%` returns negative for negative operands, so we fix up after.
    const TWO_PI = 2 * Math.PI;
    let angleDiff = ((targetAngle - this.angle + Math.PI) % TWO_PI) - Math.PI;
    if (angleDiff < -Math.PI) angleDiff += TWO_PI;

    this.angle += angleDiff * this.homingStrength;

    // Re-derive vx/vy from the new angle and current speed magnitude.
    const speed = Math.hypot(this.vx, this.vy);
    this.vx = Math.cos(this.angle) * speed;
    this.vy = Math.sin(this.angle) * speed;
  }

  /**
   * Advance one logical tick. `dtScale` normalizes delta-time to 60fps ticks
   * (dtScale=1.0 at 60fps, 2.0 at 30fps). Preserves the previous TS pass's
   * ballistic gravity and arena-boundary expiry.
   */
  update(
    dtScale: number,
    arenaCenterX: number,
    arenaCenterY: number,
    arenaRadius: number
  ): void {
    if (this.isExpired) return;

    // Homing: projectile.py:35-39 — applied before movement each tick.
    // Owner is never a valid target (can't home on the shooter), and a
    // dead target gets skipped to match Python's `if target is None` guard
    // (Python uses `owner.game.player1/2` which never goes None, but we
    // treat an !isAlive target as equivalent to None).
    if (this.homing && this.target && this.target !== this.owner && this.target.isAlive) {
      this.homeTowards(this.target);
    }

    if (this.type === "ballistic") {
      this.vy += BALLISTIC_GRAVITY * dtScale;
    }

    this.x += this.vx * dtScale;
    this.y += this.vy * dtScale;

    this.lifetimeFrames -= dtScale;
    if (this.lifetimeFrames <= 0) {
      this.isExpired = true;
      this.render();
      return;
    }

    const ddx = this.x - arenaCenterX;
    const ddy = this.y - arenaCenterY;
    if (ddx * ddx + ddy * ddy > arenaRadius * arenaRadius) {
      this.isExpired = true;
    }

    // Tail-call render so scenes that only invoke update() still get visuals
    // updated each frame. Scenes may also call render() directly if desired.
    this.render();
  }

  /**
   * Clear the Graphics object and redraw per type — a literal mirror of the
   * pygame draw() method on each subclass.
   */
  render(): void {
    const g = this.sprite;
    g.clear();
    if (this.isExpired) return;

    const x = this.x;
    const y = this.y;

    switch (this.type) {
      case "beam": {
        // color = CYAN if owner.is_player1 else MAGENTA
        const color = this.owner.isPlayer1 ? CYAN : MAGENTA;
        const endX = x + Math.cos(this.angle) * BEAM_LENGTH;
        const endY = y + Math.sin(this.angle) * BEAM_LENGTH;
        // pygame.draw.line(screen, color, (x, y), (end_x, end_y), 3)
        g.lineStyle(3, color, 1);
        g.beginPath();
        g.moveTo(x, y);
        g.lineTo(endX, endY);
        g.strokePath();
        // pygame.draw.circle(screen, WHITE, (int(end_x), int(end_y)), 2)
        g.fillStyle(WHITE, 1);
        g.fillCircle(endX, endY, 2);
        break;
      }
      case "ballistic": {
        // color = YELLOW if owner.is_player1 else ORANGE
        const color = this.owner.isPlayer1 ? YELLOW : ORANGE;
        // pygame.draw.circle(screen, color, (x, y), radius)
        g.fillStyle(color, 1);
        g.fillCircle(x, y, this.radius);
        break;
      }
      case "melee": {
        // color = GREEN if owner.is_player1 else RED
        const color = this.owner.isPlayer1 ? GREEN : RED;
        // pygame.draw.circle(screen, color, (x, y), radius, 2) -- outline only
        g.lineStyle(2, color, 1);
        g.strokeCircle(x, y, this.radius);
        break;
      }
      case "soybean": {
        // pygame.draw.circle(screen, (210, 180, 140), (x, y), radius)
        g.fillStyle(SOYBEAN_COLOR, 1);
        g.fillCircle(x, y, this.radius);
        // pygame.draw.circle(screen, WHITE, (x, y), radius, 1) -- white outline
        g.lineStyle(1, WHITE, 1);
        g.strokeCircle(x, y, this.radius);
        break;
      }
      default: {
        // Base class: white filled circle at radius=5
        g.fillStyle(WHITE, 1);
        g.fillCircle(x, y, this.radius);
      }
    }
  }

  /**
   * Circle-circle hit test. Bullets never collide with their shooter.
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
 * Factory helper — preferred over `new Projectile(...)` at call sites so we
 * can later swap in dedicated subclasses without touching Player.ts.
 */
export function createProjectile(
  scene: Phaser.Scene,
  type: ProjectileType,
  x: number,
  y: number,
  angleRad: number,
  damage: number,
  owner: Player,
  target: Player | null = null
): Projectile {
  return new Projectile(scene, type, x, y, angleRad, damage, owner, target);
}
