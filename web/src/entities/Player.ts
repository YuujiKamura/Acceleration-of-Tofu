import Phaser from "phaser";
import {
  MAX_HEALTH,
  MAX_HEAT,
  MAX_HYPER,
  PLAYER_SPEED,
  PLAYER_DASH_SPEED,
  DASH_RING_DURATION,
  DASH_COOLDOWN,
  SHIELD_DURATION,
  SHIELD_COOLDOWN,
  HYPER_DURATION,
  HYPER_CONSUMPTION_RATE,
  HYPER_ACTIVATION_COST,
  HEAT_DECREASE_RATE,
} from "../config/constants";
import { TOFU_WHITE, NEGI_GREEN, CYAN } from "../config/colors";
import { Projectile, createProjectile } from "./Projectile";

/**
 * Player
 *
 * Port of game/player.py covering the gameplay-critical systems:
 *   - movement with dash window (speed ramp for DASH_RING_DURATION frames)
 *   - weapon_a (beam) + weapon_b (ballistic arc shot)
 *   - shield that blocks damage for SHIELD_DURATION frames, with cooldown
 *   - hyper mode: HYPER_ACTIVATION_COST to start, per-frame drain,
 *     outgoing damage ×2 while active (Combat.ts applies the multiplier)
 *   - heat with passive decay + contributions from firing / dashing
 *   - aging -> isFermented flag; Combat.applyStickyTether reads the flag
 *
 * Deliberately SKIPPED (not on critical path for MVP demo): special/spread
 * burst, overheat lock, water regen on center, hyper laser first-shot
 * variant, fermentation particle cosmetics, dash direction smoothing.
 *
 * Rendering stays Phaser.GameObjects.Arc — no physics. Collision is done
 * manually via Projectile.collidesWith() from the scene.
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
// weapons["weapon_b"] = Weapon("バリスティック", BALLISTIC, 40, 60) in Python.
const WEAPON_B_COOLDOWN_FRAMES = 60;
const WEAPON_B_DAMAGE = 40;

// Frames the sprite flashes white after takeDamage(). Spec: 6 frames.
const DAMAGE_FLASH_FRAMES = 6;
// Muzzle-flash frames after firing (purely cosmetic, not the damage flash).
const MUZZLE_FLASH_FRAMES = 5;

export class Player {
  public x: number;
  public y: number;
  public vx = 0;
  public vy = 0;
  public readonly radius = 15;
  public readonly isPlayer1: boolean;
  public readonly color: number;

  // --- gauges ---
  public health: number = MAX_HEALTH;
  public heat = 0;
  public hyperGauge = 0;
  public waterLevel = 100;
  public beans = 100;
  public aging = 0;

  // --- action state (raw frame counters; getters below expose `is*` views) ---
  public keyStates: KeyStates = emptyKeyStates();

  // Action frame counters. All decrement each update() and gate the
  // corresponding `is*` booleans. Cooldown counters are separate so the
  // action can fully finish before the next activation becomes legal.
  private dashFrames = 0;
  private dashCooldown = 0;
  private shieldFrames = 0;
  private shieldCooldown = 0;
  private hyperActiveFrames = 0;
  // Weapon-specific fire cooldowns. Tracked independently of dash/shield.
  private weaponACooldown = 0;
  private weaponBCooldown = 0;
  private damageFlashFrames = 0;
  private muzzleFlashFrames = 0;

  public readonly sprite: Phaser.GameObjects.Arc;

  private readonly initialX: number;
  private readonly initialY: number;

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

  // ---- state-predicate getters (read-only views for HUD / AI / Combat) ----

  get isAlive(): boolean {
    return this.health > 0;
  }

  /** Dash window active — speed multiplier applied during update(). */
  get isDashing(): boolean {
    return this.dashFrames > 0;
  }

  /** Shield active — takeDamage() becomes a no-op. */
  get isShielding(): boolean {
    return this.shieldFrames > 0;
  }

  /** Hyper active — Combat.ts multiplies outgoing damage ×2. */
  get isHyperActive(): boolean {
    return this.hyperActiveFrames > 0;
  }

  /** aging >= 100. Combat.applyStickyTether pulls opponents toward this. */
  get isFermented(): boolean {
    return this.aging >= 100;
  }

  // Gauge-maxes (convenient for HUD code in D2's scope).
  get maxHealth(): number {
    return MAX_HEALTH;
  }
  get maxHeat(): number {
    return MAX_HEAT;
  }
  get maxHyper(): number {
    return MAX_HYPER;
  }

  /**
   * Advance one frame. `spawnProjectile` is a scene-provided callback
   * that registers the new projectile with the scene's projectile list
   * so the scene owns collision + lifetime.
   *
   * `arenaCenterX/Y` are kept as params (not read from constants) so the
   * scene can test against an off-center arena if needed later.
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
    if (!this.isAlive) {
      // still position the sprite (dead bodies stay put but shouldn't input)
      this.sprite.setPosition(this.x, this.y);
      this.sprite.setFillStyle(0x404040);
      return;
    }

    // --- action-window counters ---
    // Tick these BEFORE reading the is* getters for this frame's logic so
    // that actions started on frame N stay active on frame N (we want the
    // frame of activation to count as "in-window").
    this.decrementCounters(dtScale);

    // --- aging progresses passively; matches Python's +0.02/frame ---
    this.aging = Math.min(100, this.aging + 0.02 * dtScale);

    // --- dash activation: edge-triggered (cooldown gated) ---
    if (
      this.keyStates.dash &&
      this.dashCooldown <= 0 &&
      this.dashFrames <= 0
    ) {
      this.dashFrames = DASH_RING_DURATION;
      this.dashCooldown = DASH_RING_DURATION + DASH_COOLDOWN;
      this.heat = Math.min(MAX_HEAT, this.heat + 2); // small heat tick on start
    }

    // --- shield activation: edge-triggered (cooldown gated) ---
    if (
      this.keyStates.shield &&
      this.shieldCooldown <= 0 &&
      this.shieldFrames <= 0
    ) {
      this.shieldFrames = SHIELD_DURATION;
      this.shieldCooldown = SHIELD_DURATION + SHIELD_COOLDOWN;
    }

    // --- hyper activation: only if gauge sufficient and not already active ---
    if (
      this.keyStates.hyper &&
      !this.isHyperActive &&
      this.hyperGauge >= HYPER_ACTIVATION_COST
    ) {
      this.hyperGauge -= HYPER_ACTIVATION_COST;
      this.hyperActiveFrames = HYPER_DURATION;
    }

    // --- hyper consumption while active ---
    if (this.isHyperActive) {
      this.hyperGauge = Math.max(
        0,
        this.hyperGauge - HYPER_CONSUMPTION_RATE * dtScale
      );
      if (this.hyperGauge <= 0) {
        this.hyperActiveFrames = 0;
      }
    }

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
    // dash multiplies base speed by (DASH_SPEED/BASE_SPEED). When the dash
    // window expires, speed naturally drops back. Matches Python's
    // `self.dash_speed if self.is_dashing else self.speed`.
    const speed = this.isDashing
      ? PLAYER_SPEED * (PLAYER_DASH_SPEED / PLAYER_SPEED)
      : PLAYER_SPEED;
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

    // --- weapon_a fire (beam). Shield locks out weapons, same as Python. ---
    if (
      !this.isShielding &&
      this.keyStates.weapon_a &&
      this.weaponACooldown <= 0 &&
      this.beans > 0
    ) {
      const angle = Math.atan2(opponent.y - this.y, opponent.x - this.x);
      const p = createProjectile(
        scene,
        "beam",
        this.x,
        this.y,
        angle,
        WEAPON_A_DAMAGE,
        this
      );
      spawnProjectile(p);
      this.weaponACooldown = WEAPON_A_COOLDOWN_FRAMES;
      this.beans = Math.max(0, this.beans - 2);
      this.muzzleFlashFrames = MUZZLE_FLASH_FRAMES;
    }

    // --- weapon_b fire (ballistic arc). Heat += 3 per shot (spec). ---
    if (
      !this.isShielding &&
      this.keyStates.weapon_b &&
      this.weaponBCooldown <= 0 &&
      this.beans > 0
    ) {
      const angle = Math.atan2(opponent.y - this.y, opponent.x - this.x);
      const p = createProjectile(
        scene,
        "ballistic",
        this.x,
        this.y,
        angle,
        WEAPON_B_DAMAGE,
        this
      );
      spawnProjectile(p);
      this.weaponBCooldown = WEAPON_B_COOLDOWN_FRAMES;
      this.heat = Math.min(MAX_HEAT, this.heat + 3);
      this.beans = Math.max(0, this.beans - 2);
      this.muzzleFlashFrames = MUZZLE_FLASH_FRAMES;
    }

    // --- heat passive decay (doesn't decay while dashing - matches Python) ---
    if (!this.isDashing && this.heat > 0) {
      this.heat = Math.max(0, this.heat - HEAT_DECREASE_RATE * dtScale);
    }

    // --- render state update ---
    this.sprite.setPosition(this.x, this.y);

    // Tint priority: damage-flash > hyper-active > muzzle-flash > default.
    if (this.damageFlashFrames > 0) {
      this.sprite.setFillStyle(0xffffff);
      this.sprite.setStrokeStyle(3, 0xffffff);
    } else if (this.isHyperActive) {
      // cyan overlay during hyper (spec) — re-uses Phaser Arc fill since we
      // don't have a proper tint pipeline on the bare Arc GameObject.
      this.sprite.setFillStyle(CYAN);
      this.sprite.setStrokeStyle(3, 0xffff00);
    } else if (this.muzzleFlashFrames > 0) {
      this.sprite.setFillStyle(this.color);
      this.sprite.setStrokeStyle(3, 0xffff00);
    } else {
      this.sprite.setFillStyle(this.color);
      this.sprite.setStrokeStyle(2, 0xffffff);
    }
  }

  /**
   * Decrement all per-frame counters (actions + cooldowns + flashes).
   * Kept separate from update() so a unit test can tick the player in
   * isolation without dealing with movement/fire side-effects.
   */
  private decrementCounters(dtScale: number): void {
    if (this.dashFrames > 0) this.dashFrames -= dtScale;
    if (this.dashCooldown > 0) this.dashCooldown -= dtScale;
    if (this.shieldFrames > 0) this.shieldFrames -= dtScale;
    if (this.shieldCooldown > 0) this.shieldCooldown -= dtScale;
    if (this.hyperActiveFrames > 0) this.hyperActiveFrames -= dtScale;
    if (this.weaponACooldown > 0) this.weaponACooldown -= dtScale;
    if (this.weaponBCooldown > 0) this.weaponBCooldown -= dtScale;
    if (this.damageFlashFrames > 0) this.damageFlashFrames -= dtScale;
    if (this.muzzleFlashFrames > 0) this.muzzleFlashFrames -= dtScale;
  }

  /**
   * Apply damage. Shield blocks ALL incoming damage. Dead players take no
   * more. Hyper gauge fills from damage taken (matches Python's amount/5
   * after the rebalance — we use amount/10 to keep early MVP less swingy).
   */
  takeDamage(amount: number): void {
    if (this.health <= 0) return;
    if (this.isShielding) return;
    this.health = Math.max(0, this.health - amount);
    this.beans = Math.max(0, this.beans - amount * 0.5);
    this.hyperGauge = Math.min(MAX_HYPER, this.hyperGauge + amount / 10);
    this.damageFlashFrames = DAMAGE_FLASH_FRAMES;
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
    this.dashFrames = 0;
    this.dashCooldown = 0;
    this.shieldFrames = 0;
    this.shieldCooldown = 0;
    this.hyperActiveFrames = 0;
    this.weaponACooldown = 0;
    this.weaponBCooldown = 0;
    this.damageFlashFrames = 0;
    this.muzzleFlashFrames = 0;
    this.keyStates = emptyKeyStates();
    this.sprite.setPosition(this.x, this.y);
    this.sprite.setFillStyle(this.color);
    this.sprite.setStrokeStyle(2, 0xffffff);
  }
}
