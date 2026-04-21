import Phaser from "phaser";
import {
  MAX_HEALTH,
  MAX_HEAT,
  MAX_HYPER,
  PLAYER_SPEED,
  PLAYER_DASH_SPEED,
  DASH_RING_DURATION,
  DASH_COOLDOWN,
  DASH_TURN_SPEED,
  SHIELD_DURATION,
  SHIELD_COOLDOWN,
  HYPER_DURATION,
  HYPER_CONSUMPTION_RATE,
  HYPER_ACTIVATION_COST,
  HEAT_DECREASE_RATE,
} from "../config/constants";
import { NEGI_GREEN, BENI_RED, MAGENTA, YELLOW } from "../config/colors";
import { Projectile, createProjectile } from "./Projectile";
import { DashRing } from "./effects/DashRing";
import { ShieldEffect } from "./effects/ShieldEffect";
import { AudioManager } from "../systems/Audio";

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
  // py line 199: self.square_size = 30
  public readonly squareSize = 30;
  // py line 240: self.facing_angle = 0
  public facingAngle = 0;

  // --- gauges ---
  public health: number = MAX_HEALTH;
  public heat = 0;
  public hyperGauge = 0;
  public waterLevel = 100;
  public beans = 100;
  public aging = 0;

  // py line 194: self.ferment_particles = []
  public fermentParticles: { x: number; y: number; life: number }[] = [];

  // py line 213: self.dash_rings = []
  public dashRings: DashRing[] = [];
  // py line 245: self.shield_effect = None
  public shieldEffect: ShieldEffect | null = null;

  // py line 205: self.hyper_duration = 0 — used for glow pulse math
  public hyperDuration = 0;

  // --- action state (raw frame counters; getters below expose `is*` views) ---
  public keyStates: KeyStates = emptyKeyStates();

  // Action frame counters. All decrement each update() and gate the
  // corresponding `is*` booleans. Cooldown counters are separate so the
  // action can fully finish before the next activation becomes legal.
  private dashFrames = 0;
  private dashCooldown = 0;
  // py lines 223-224
  private dashRingCounter = 0;
  private readonly dashRingInterval = 4;
  // py ctor: self.dash_direction_x/y = 0 — stored direction used by LP filter
  // and passed to DashRing on spawn (after the low-pass filter smoothing).
  private dashDirectionX = 0;
  private dashDirectionY = 0;
  private shieldFrames = 0;
  private shieldCooldown = 0;
  private hyperActiveFrames = 0;
  // Weapon-specific fire cooldowns. Tracked independently of dash/shield.
  private weaponACooldown = 0;
  private weaponBCooldown = 0;
  private damageFlashFrames = 0;
  private muzzleFlashFrames = 0;

  // Primary render target. All per-frame body drawing (hyper glow, tofu
  // square, aging color, border, weapon line, fermentation particles) lands
  // on this single Graphics object. Replaces the old Phaser.Arc sprite.
  public readonly bodyG: Phaser.GameObjects.Graphics;

  private readonly initialX: number;
  private readonly initialY: number;

  constructor(scene: Phaser.Scene, x: number, y: number, isPlayer1: boolean) {
    this.x = x;
    this.y = y;
    this.initialX = x;
    this.initialY = y;
    this.isPlayer1 = isPlayer1;
    // py line 197: NEGI_GREEN if is_player1 else BENI_RED
    this.color = isPlayer1 ? NEGI_GREEN : BENI_RED;
    this.bodyG = scene.add.graphics();
    this.render();
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
      // still render (dead bodies stay put but shouldn't input)
      this.render();
      return;
    }

    // --- action-window counters ---
    // Tick these BEFORE reading the is* getters for this frame's logic so
    // that actions started on frame N stay active on frame N (we want the
    // frame of activation to count as "in-window").
    this.decrementCounters(dtScale);

    // --- aging progresses passively; matches Python's +0.02/frame ---
    // py lines 357-360: on the frame aging crosses 100, play "hyper" SE
    // (fermentation transition). Edge-triggered: capture pre-increment state.
    const wasFermented = this.isFermented;
    this.aging = Math.min(100, this.aging + 0.02 * dtScale);
    if (!wasFermented && this.isFermented) {
      AudioManager.get().playSfx("hyper");
    }

    // --- shield activation: edge-triggered (cooldown gated) ---
    if (
      this.keyStates.shield &&
      this.shieldCooldown <= 0 &&
      this.shieldFrames <= 0
    ) {
      this.shieldFrames = SHIELD_DURATION;
      this.shieldCooldown = SHIELD_DURATION + SHIELD_COOLDOWN;
      // py: self.shield_effect = ShieldEffect(self)
      if (this.shieldEffect) this.shieldEffect.destroy();
      this.shieldEffect = new ShieldEffect(scene, this);
    }

    // --- hyper activation: only if gauge sufficient and not already active ---
    if (
      this.keyStates.hyper &&
      !this.isHyperActive &&
      this.hyperGauge >= HYPER_ACTIVATION_COST
    ) {
      this.hyperGauge -= HYPER_ACTIVATION_COST;
      this.hyperActiveFrames = HYPER_DURATION;
      this.hyperDuration = HYPER_DURATION;
    }

    // --- hyper consumption while active ---
    if (this.isHyperActive) {
      this.hyperGauge = Math.max(
        0,
        this.hyperGauge - HYPER_CONSUMPTION_RATE * dtScale
      );
      this.hyperDuration = Math.max(0, this.hyperDuration - dtScale);
      if (this.hyperGauge <= 0) {
        this.hyperActiveFrames = 0;
        this.hyperDuration = 0;
      }
    }

    // --- movement ---
    // py lines 501-515: build input vector + has_input flag
    let dx = 0;
    let dy = 0;
    if (this.keyStates.up) dy -= 1;
    if (this.keyStates.down) dy += 1;
    if (this.keyStates.left) dx -= 1;
    if (this.keyStates.right) dx += 1;
    const hasInput = dx !== 0 || dy !== 0;
    // py lines 540-544: normalize diagonals so speed stays constant
    if (dx !== 0 && dy !== 0) {
      const inv = 1 / Math.sqrt(2);
      dx *= inv;
      dy *= inv;
    }

    // py lines 547-549: heat >= MAX_HEAT force-ends dash (pre-activation check)
    if (this.heat >= MAX_HEAT) {
      this.dashFrames = 0;
      // (overheat flag is not yet modelled in TS; mirrors Python's
      // `self.is_overheated = True` — state carried implicitly.)
    }

    // py lines 552-567: dash activation + end-on-release.
    // py:552 uses the literal 200 (not MAX_HEAT=300) — it's an "almost
    // overheated" soft gate, stricter than the hard force-end at MAX_HEAT.
    const heatOkForDash = this.heat < 200;
    if (
      this.keyStates.dash &&
      this.dashCooldown <= 0 &&
      !this.isDashing &&
      hasInput &&
      heatOkForDash
    ) {
      // py 555-558: store direction at activation
      this.dashFrames = DASH_RING_DURATION;
      this.dashCooldown = DASH_RING_DURATION + DASH_COOLDOWN;
      this.dashDirectionX = dx;
      this.dashDirectionY = dy;
      // py 560-561: +20 heat on activation
      this.heat = Math.min(MAX_HEAT, this.heat + 20);
      // py 563: spawn initial DashRing in input direction
      this.dashRings.push(
        new DashRing(
          scene,
          this.x,
          this.y,
          DASH_RING_DURATION,
          dx,
          dy
        )
      );
      // py 565: counter reset
      this.dashRingCounter = 0;
    } else if (!this.keyStates.dash) {
      // py 566-567: releasing dash immediately ends the dash
      this.dashFrames = 0;
    }

    // py lines 570-596: while dashing — re-check overheat, LP-turn, trail
    if (this.isDashing) {
      // py 573-576: heat may have crossed MAX_HEAT this frame
      if (this.heat >= MAX_HEAT) {
        this.dashFrames = 0;
      } else if (hasInput && (dx !== 0 || dy !== 0)) {
        // py 583-584: low-pass filter dash direction toward input.
        // Python runs at fixed 60Hz with alpha=0.15 per frame. We scale by
        // dtScale to keep turn-rate time-invariant when the browser drops
        // frames; Python behaviour is recovered when dtScale === 1.
        const alpha = DASH_TURN_SPEED * dtScale;
        this.dashDirectionX =
          this.dashDirectionX * (1 - alpha) + dx * alpha;
        this.dashDirectionY =
          this.dashDirectionY * (1 - alpha) + dy * alpha;
        // py 586-590: renormalize
        const len = Math.sqrt(
          this.dashDirectionX * this.dashDirectionX +
            this.dashDirectionY * this.dashDirectionY
        );
        if (len > 0) {
          this.dashDirectionX /= len;
          this.dashDirectionY /= len;
        }
        // py 592-596: trail DashRing at fixed interval
        this.dashRingCounter += dtScale;
        if (this.dashRingCounter >= this.dashRingInterval) {
          this.dashRings.push(
            new DashRing(
              scene,
              this.x,
              this.y,
              DASH_RING_DURATION,
              this.dashDirectionX,
              this.dashDirectionY
            )
          );
          this.dashRingCounter = 0;
        }
      }
    }

    // py lines 598-599: speed = dash_speed if is_dashing else speed.
    // While dashing, vx/vy follow dashDirection (LP-filtered); otherwise
    // follow raw input.
    const speed = this.isDashing ? PLAYER_DASH_SPEED : PLAYER_SPEED;
    if (this.isDashing) {
      this.vx = this.dashDirectionX * speed;
      this.vy = this.dashDirectionY * speed;
    } else {
      this.vx = dx * speed;
      this.vy = dy * speed;
    }
    this.x += this.vx * dtScale;
    this.y += this.vy * dtScale;

    // py line 353: facing_angle = atan2(opponent.y - y, opponent.x - x)
    this.facingAngle = Math.atan2(opponent.y - this.y, opponent.x - this.x);

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
        this,
        opponent
      );
      spawnProjectile(p);
      // py lines 915-917: weapon_a fire -> play "shot" SE
      AudioManager.get().playSfx("shot");
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
        this,
        opponent
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

    // --- update effects ---
    // py lines 411-414: prune dead dash rings
    for (let i = this.dashRings.length - 1; i >= 0; i--) {
      const ring = this.dashRings[i];
      ring.update();
      if (ring.isDead) {
        ring.destroy();
        this.dashRings.splice(i, 1);
      }
    }
    // py: shield_effect.update()
    if (this.shieldEffect) {
      this.shieldEffect.update();
      if (this.shieldEffect.isDead) {
        this.shieldEffect.destroy();
        this.shieldEffect = null;
      }
    }

    // py lines 868-874: fermentation particles (only emitted while fermented)
    if (this.isFermented) {
      // spawn a new particle with the same {x,y,life} shape Python uses
      this.fermentParticles.push({
        x: this.x + (Math.random() - 0.5) * this.squareSize * 1.2,
        y: this.y + (Math.random() - 0.5) * this.squareSize * 1.2,
        life: 30,
      });
    }
    for (let i = this.fermentParticles.length - 1; i >= 0; i--) {
      this.fermentParticles[i].life -= dtScale;
      if (this.fermentParticles[i].life <= 0) {
        this.fermentParticles.splice(i, 1);
      }
    }

    this.render();
  }

  /**
   * Render the player body. 1:1 port of game/player.py Player.draw()
   * lines 813-889 using a single Phaser.GameObjects.Graphics instance.
   */
  render(): void {
    const g = this.bodyG;
    g.clear();

    // Dead body: simple dark square (kept from existing behavior).
    if (!this.isAlive) {
      g.fillStyle(0x404040, 1.0);
      g.fillRect(
        Math.floor(this.x - this.squareSize / 2),
        Math.floor(this.y - this.squareSize / 2),
        this.squareSize,
        this.squareSize
      );
      return;
    }

    // py lines 823-838: hyper glow
    if (this.isHyperActive) {
      const glowRadius = this.radius + 5;
      const pulse = (this.hyperDuration % 20) / 20.0;
      // py: glow_color = (255, 255, 0, int(200 * pulse + 50))
      const glowAlpha = Math.floor(200 * pulse + 50) / 255;
      g.fillStyle(0xffff00, glowAlpha);
      g.fillCircle(
        Math.floor(this.x),
        Math.floor(this.y),
        glowRadius + Math.floor(pulse * 3)
      );
      const glowSize = this.squareSize + 6;
      g.lineStyle(2, 0xffff00, glowAlpha);
      g.strokeRect(
        Math.floor(this.x - glowSize / 2),
        Math.floor(this.y - glowSize / 2),
        glowSize,
        glowSize
      );
    }

    // py lines 841-844: color override during hyper
    let color = this.color;
    if (this.isHyperActive) {
      color = this.isPlayer1 ? MAGENTA : YELLOW;
    }

    // py lines 847-853: aging color lerp TOFU_WHITE -> Golden (255,215,0)
    const agingFactor = this.aging / 100.0;
    const rC = 255;
    const gC = Math.floor(255 - (255 - 215) * agingFactor);
    const bC = Math.floor(255 - 255 * agingFactor);
    let agingColor = (rC << 16) | (gC << 8) | bC;

    // py lines 856-857: fermented overrides to Natto Brown (139,69,19)
    if (this.isFermented) {
      agingColor = 0x8b4513;
    }

    // py lines 859-865: filled tofu square
    g.fillStyle(agingColor, 1.0);
    g.fillRect(
      Math.floor(this.x - this.squareSize / 2),
      Math.floor(this.y - this.squareSize / 2),
      this.squareSize,
      this.squareSize
    );

    // py lines 868-874: fermentation particles (strings of natto)
    // p_color = (210, 180, 140) = 0xD2B48C
    if (this.fermentParticles.length > 0) {
      for (const p of this.fermentParticles) {
        const alpha = (255 * (p.life / 30.0)) / 255;
        g.fillStyle(0xd2b48c, alpha);
        g.fillCircle(Math.floor(p.x), Math.floor(p.y), 2);
        g.lineStyle(1, 0xd2b48c, alpha);
        g.lineBetween(
          Math.floor(this.x),
          Math.floor(this.y),
          Math.floor(p.x),
          Math.floor(p.y)
        );
      }
    }

    // py lines 877-883: colored border (negi/beni)
    g.lineStyle(2, color, 1.0);
    g.strokeRect(
      Math.floor(this.x - this.squareSize / 2),
      Math.floor(this.y - this.squareSize / 2),
      this.squareSize,
      this.squareSize
    );

    // py lines 885-889: weapon direction line
    const weaponLength = this.radius * 2.5;
    const endX = this.x + Math.cos(this.facingAngle) * weaponLength;
    const endY = this.y + Math.sin(this.facingAngle) * weaponLength;
    g.lineStyle(3, color, 1.0);
    g.lineBetween(this.x, this.y, endX, endY);

    // Damage flash overlay: draw a faint white square over everything.
    if (this.damageFlashFrames > 0) {
      g.fillStyle(0xffffff, 0.6);
      g.fillRect(
        Math.floor(this.x - this.squareSize / 2),
        Math.floor(this.y - this.squareSize / 2),
        this.squareSize,
        this.squareSize
      );
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
    this.dashRingCounter = 0;
    this.dashDirectionX = 0;
    this.dashDirectionY = 0;
    this.shieldFrames = 0;
    this.shieldCooldown = 0;
    this.hyperActiveFrames = 0;
    this.hyperDuration = 0;
    this.weaponACooldown = 0;
    this.weaponBCooldown = 0;
    this.damageFlashFrames = 0;
    this.muzzleFlashFrames = 0;
    this.facingAngle = 0;
    this.keyStates = emptyKeyStates();
    for (const r of this.dashRings) r.destroy();
    this.dashRings = [];
    if (this.shieldEffect) {
      this.shieldEffect.destroy();
      this.shieldEffect = null;
    }
    this.fermentParticles = [];
    this.render();
  }
}
