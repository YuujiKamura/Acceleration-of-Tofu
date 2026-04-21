import Phaser from "phaser";
import {
  MAX_HEALTH,
  MAX_HEAT,
  MAX_HYPER,
  PLAYER_SPEED,
} from "../config/constants";
import { TOFU_WHITE, NEGI_GREEN } from "../config/colors";
import { Projectile } from "./Projectile";

/**
 * Player
 *
 * Minimum-viable port of game/player.py. This first milestone covers only:
 *   - movement (up/down/left/right) with arena clamp
 *   - weapon_a -> spawn a BeamProjectile aimed at the opponent, with a
 *     simple shoot_cooldown identical in spirit to player.shoot_cooldown
 *   - take_damage / hp-floor at 0
 *
 * Deliberately SKIPPED for now: dash, hyper, shield, fermentation, heat
 * ramp-up from dash speed, weapon_b burst, spread shot. Those will land
 * in later passes once the CPU-vs-CPU demo renders & scores consistently.
 *
 * We render as a filled circle (Phaser.GameObjects.Arc) in the player's
 * color, so no physics engine is needed. Collision is done manually in
 * AutoTestScene via Projectile.collidesWith().
 */
export type ActionName =
  | "up"
  | "down"
  | "left"
  | "right"
  | "weapon_a"
  | "weapon_b"
  | "hyper"
  | "dash"
  | "special"
  | "shield";

export type KeyStates = Record<ActionName, boolean>;

export function emptyKeyStates(): KeyStates {
  return {
    up: false,
    down: false,
    left: false,
    right: false,
    weapon_a: false,
    weapon_b: false,
    hyper: false,
    dash: false,
    special: false,
    shield: false,
  };
}

// Cooldown (frames @ 60fps) for weapon_a. Matches weapon.cooldown=30 in
// game/player.py: weapons["weapon_a"] = Weapon("ビームライフル", BEAM, 20, 30).
const WEAPON_A_COOLDOWN_FRAMES = 30;
const WEAPON_A_DAMAGE = 20;

export class Player {
  public x: number;
  public y: number;
  public vx = 0;
  public vy = 0;
  public readonly radius = 15;
  public readonly isPlayer1: boolean;
  public readonly color: number;

  public health: number = MAX_HEALTH;
  public heat = 0;
  public hyperGauge = 0;
  public waterLevel = 100;
  public beans = 100;
  public aging = 0;

  public keyStates: KeyStates = emptyKeyStates();

  public readonly sprite: Phaser.GameObjects.Arc;

  private readonly initialX: number;
  private readonly initialY: number;
  private shootCooldown = 0;
  private flashFrames = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, isPlayer1: boolean) {
    this.x = x;
    this.y = y;
    this.initialX = x;
    this.initialY = y;
    this.isPlayer1 = isPlayer1;
    this.color = isPlayer1 ? TOFU_WHITE : NEGI_GREEN;
    this.sprite = scene.add.circle(x, y, this.radius, this.color);
    this.sprite.setStrokeStyle(2, 0xffffff);
  }

  /**
   * Advance one frame. `spawnProjectile` is a scene-provided callback
   * that registers the new projectile with the scene's projectile list
   * so the scene owns collision + lifetime.
   */
  update(
    dtScale: number,
    arenaCenterX: number,
    arenaCenterY: number,
    arenaRadius: number,
    opponent: Player,
    spawnProjectile: (p: Projectile) => void,
    scene: Phaser.Scene
  ): void {
    // --- movement ---
    let dx = 0;
    let dy = 0;
    if (this.keyStates.up) dy -= 1;
    if (this.keyStates.down) dy += 1;
    if (this.keyStates.left) dx -= 1;
    if (this.keyStates.right) dx += 1;

    if (dx !== 0 && dy !== 0) {
      const inv = 1 / Math.sqrt(2);
      dx *= inv;
      dy *= inv;
    }

    const speed = PLAYER_SPEED;
    this.vx = dx * speed;
    this.vy = dy * speed;
    this.x += this.vx * dtScale;
    this.y += this.vy * dtScale;

    // --- arena clamp (circle) ---
    const cdx = this.x - arenaCenterX;
    const cdy = this.y - arenaCenterY;
    const distSq = cdx * cdx + cdy * cdy;
    const maxR = arenaRadius - this.radius;
    if (distSq > maxR * maxR) {
      const dist = Math.sqrt(distSq) || 1;
      this.x = arenaCenterX + (cdx / dist) * maxR;
      this.y = arenaCenterY + (cdy / dist) * maxR;
    }

    // --- weapon_a fire ---
    if (this.shootCooldown > 0) this.shootCooldown -= dtScale;
    if (
      this.keyStates.weapon_a &&
      this.shootCooldown <= 0 &&
      this.beans > 0 &&
      this.health > 0
    ) {
      const ox = opponent.x - this.x;
      const oy = opponent.y - this.y;
      const angle = Math.atan2(oy, ox);
      const p = new Projectile(
        scene,
        "beam",
        this.x,
        this.y,
        angle,
        WEAPON_A_DAMAGE,
        this
      );
      spawnProjectile(p);
      this.shootCooldown = WEAPON_A_COOLDOWN_FRAMES;
      this.beans = Math.max(0, this.beans - 2);
      this.flashFrames = 5;
    }

    // --- cosmetic muzzle flash ---
    if (this.flashFrames > 0) {
      this.flashFrames -= dtScale;
      this.sprite.setStrokeStyle(3, 0xffff00);
    } else {
      this.sprite.setStrokeStyle(2, 0xffffff);
    }

    this.sprite.setPosition(this.x, this.y);

    // visually fade-to-grey when health is low; keeps demo readable
    if (this.health <= 0) {
      this.sprite.setFillStyle(0x404040);
    }
  }

  takeDamage(amount: number): void {
    if (this.health <= 0) return;
    this.health = Math.max(0, this.health - amount);
    this.beans = Math.max(0, this.beans - amount * 0.5);
    this.hyperGauge = Math.min(MAX_HYPER, this.hyperGauge + amount / 10);
  }

  reset(): void {
    this.x = this.initialX;
    this.y = this.initialY;
    this.vx = 0;
    this.vy = 0;
    this.health = MAX_HEALTH;
    this.heat = 0;
    this.hyperGauge = 0;
    this.waterLevel = 100;
    this.beans = 100;
    this.aging = 0;
    this.shootCooldown = 0;
    this.flashFrames = 0;
    this.keyStates = emptyKeyStates();
    this.sprite.setPosition(this.x, this.y);
    this.sprite.setFillStyle(this.color);
    this.sprite.setStrokeStyle(2, 0xffffff);
  }

  get isAlive(): boolean {
    return this.health > 0;
  }

  // ergonomic read-only accessor for HUD/tests
  get maxHealth(): number {
    return MAX_HEALTH;
  }
  get maxHeat(): number {
    return MAX_HEAT;
  }
  get maxHyper(): number {
    return MAX_HYPER;
  }
}
