import type { Player, KeyStates } from "../entities/Player";
import { emptyKeyStates } from "../entities/Player";
import type { Projectile } from "../entities/Projectile";
import type { Arena } from "../entities/Arena";
import { HYPER_ACTIVATION_COST } from "../config/constants";

/**
 * CPU AI controller — port of game/ai.py::AIController.auto_test_ai_control
 * plus the legacy game/ai.py::AIController.simple_ai_control fallback.
 *
 * Exports:
 *   - autoTestAiControl(self, opponent, arena, projectiles) — richer,
 *     projectile-aware behavior tree with weapon_b / hyper / shield /
 *     special branches and a randomly-switched movement style.
 *   - simpleAiControl(self, opponent, frameCounter) — legacy trivial AI,
 *     kept for any scene that has not yet migrated.
 *   - resetAi(player) — drop per-Player AI state (call on scene reset).
 *   - isProjectileNearby / predictProjectileCollision — used both here
 *     and by the HUD / debug overlays.
 *
 * Per-Player AI state (fire cooldowns, dash bursts, RNG-ish timers,
 * movement style, weapon/hyper/shield cooldowns) is stashed in a WeakMap
 * so the state follows the Player identity across frames. Two independent
 * CPUs (P1+P2) each get their own record.
 *
 * The behavior tree mirrors the Python original (legacy/pygbag/game/ai.py)
 * but ported to a deterministic-ish LCG so the two CPUs start out of phase
 * without pulling on Math.random every single frame.
 */

// ---------- internal state ----------

/** One of four high-level movement archetypes. Refreshed every 3–5s. */
type MovementStyle = "orbit" | "charge" | "retreat" | "chaos";

interface AiState {
  /** frames remaining on the current dash burst */
  dashFrames: number;
  /** frames until we're allowed to start a new dash burst */
  dashCooldown: number;
  /** frames until the next weapon_a shot is allowed */
  fireCooldown: number;
  /** frames until the next weapon_b (ballistic) shot is allowed */
  weaponBCooldown: number;
  /** frames until the next special shot is allowed */
  specialCooldown: number;
  /** frames until we re-evaluate trying to activate hyper */
  hyperAttemptCooldown: number;
  /** frames until the next voluntary shield pop is allowed */
  shieldCooldown: number;
  /** deterministic per-Player rng so jitter doesn't thrash sprite every frame */
  rngSeed: number;
  /** internal tick counter; drives jitter phase and time-based decisions */
  tick: number;
  /** remembered jitter vector, refreshed every ~20 ticks */
  jitterX: number;
  jitterY: number;
  jitterFramesLeft: number;
  /** current high-level movement archetype */
  style: MovementStyle;
  /** tick at which the current style expires and is re-rolled */
  styleEndTick: number;
  /** stable sign (+/-1) picked when the style starts — orbit direction, etc. */
  styleSign: number;
}

const STATE = new WeakMap<Player, AiState>();

function initialState(): AiState {
  // Seed from Math.random so two parallel CPUs start out of phase. This
  // only runs once per Player, the actual per-frame RNG is the LCG below.
  return {
    dashFrames: 0,
    dashCooldown: 0,
    fireCooldown: 0,
    weaponBCooldown: 0,
    specialCooldown: 0,
    hyperAttemptCooldown: 0,
    shieldCooldown: 0,
    rngSeed: (Math.random() * 0x7fffffff) | 0 || 1,
    tick: 0,
    jitterX: 0,
    jitterY: 0,
    jitterFramesLeft: 0,
    style: "charge",
    styleEndTick: 0,
    styleSign: 1,
  };
}

function getState(player: Player): AiState {
  let s = STATE.get(player);
  if (!s) {
    s = initialState();
    STATE.set(player, s);
  }
  return s;
}

/** Reset AI state for this Player. Call when the scene resets the player. */
export function resetAi(player: Player): void {
  STATE.set(player, initialState());
}

// Tiny deterministic LCG (same family as numerical-recipes). Using a
// dedicated generator per-Player avoids cross-entity coupling through
// Math.random, and keeps jitter stable frame-to-frame.
function rand(state: AiState): number {
  // Numerical Recipes LCG params, modulo 2^31.
  state.rngSeed = (state.rngSeed * 1664525 + 1013904223) | 0;
  // Map to [0, 1).
  return ((state.rngSeed >>> 0) % 0x7fffffff) / 0x7fffffff;
}

// ---------- helpers ----------

/**
 * Any enemy projectile within `threshold` px whose velocity is pointed
 * roughly at us? Mirrors ai.py::is_projectile_nearby but tightened with
 * a velocity dot-product gate so we don't dodge bullets that are flying
 * away.
 */
export function isProjectileNearby(
  self: Player,
  projectiles: Projectile[],
  threshold = 80
): boolean {
  const tSq = threshold * threshold;
  for (const p of projectiles) {
    if (p.isExpired) continue;
    if (p.owner === self) continue;
    const dx = self.x - p.x;
    const dy = self.y - p.y;
    if (dx * dx + dy * dy > tSq) continue;
    // projectile's velocity dotted with (proj -> self) — positive means
    // it's still heading toward us.
    const dot = p.vx * dx + p.vy * dy;
    if (dot > 0) return true;
  }
  return false;
}

/**
 * Cheaper, non-quadratic form of ai.py::predict_projectile_collision.
 * For each incoming enemy projectile, step its velocity forward `lookahead`
 * frames and check whether at any intermediate tick it will land inside
 * (self.radius + proj.radius). Returns the closest dangerous projectile
 * (or null) together with its estimated time-to-hit.
 */
export function predictProjectileCollision(
  self: Player,
  projectiles: Projectile[],
  lookahead = 30
): { proj: Projectile; timeToHit: number } | null {
  let bestT = Infinity;
  let best: Projectile | null = null;

  for (const p of projectiles) {
    if (p.isExpired) continue;
    if (p.owner === self) continue;

    const rvx = p.vx;
    const rvy = p.vy;
    // relative position (proj -> self)
    const dx = self.x - p.x;
    const dy = self.y - p.y;

    // Solve |p + v*t - self|^2 = (r_self + r_proj)^2 for t.
    // With d = self - p, v = proj velocity, we want |v*t - d|^2 = R^2.
    const a = rvx * rvx + rvy * rvy;
    if (a <= 0) continue;
    const b = -2 * (rvx * dx + rvy * dy);
    const R = self.radius + p.radius;
    const c = dx * dx + dy * dy - R * R;
    const disc = b * b - 4 * a * c;
    if (disc < 0) continue;

    const sq = Math.sqrt(disc);
    const t1 = (-b - sq) / (2 * a);
    const t2 = (-b + sq) / (2 * a);
    let t: number | null = null;
    if (t1 > 0) t = t1;
    else if (t2 > 0) t = t2;
    if (t === null) continue;
    if (t > lookahead) continue;
    if (t < bestT) {
      bestT = t;
      best = p;
    }
  }

  return best ? { proj: best, timeToHit: bestT } : null;
}

// ---------- movement style ----------

/**
 * Compose the direction inputs according to the current movement style.
 * Mirrors Python's decide_movement_style() but runs every frame (not on
 * an interval) so direction is responsive to the opponent moving. The
 * style itself is what switches on an interval.
 */
function applyMovementStyle(
  st: AiState,
  keys: KeyStates,
  dx: number,
  dy: number,
  distance: number,
  arenaDx: number,
  arenaDy: number
): void {
  const sign = st.styleSign;
  switch (st.style) {
    case "charge": {
      // Pure approach. If we're already in melee range, back off like the
      // Python branch move_style<=5 does at distance<=150.
      if (distance > 150) {
        keys.right = dx > 0;
        keys.left = dx < 0;
        keys.down = dy > 0;
        keys.up = dy < 0;
      } else {
        keys.left = dx > 0;
        keys.right = dx < 0;
        keys.up = dy > 0;
        keys.down = dy < 0;
      }
      break;
    }
    case "orbit": {
      // Strafe perpendicular to the opponent vector. Python flips the
      // perpendicular with a 50/50 clockwise pick — we keep that flip
      // stable per-style (st.styleSign) so the orbit doesn't stutter.
      if (sign >= 0) {
        keys.left = dy > 0;
        keys.right = dy < 0;
        keys.up = dx > 0;
        keys.down = dx < 0;
      } else {
        keys.left = dy < 0;
        keys.right = dy > 0;
        keys.up = dx < 0;
        keys.down = dx > 0;
      }
      // Mild inward bias so we don't orbit out of the arena.
      if (distance > 300) {
        keys.right = keys.right || dx > 0;
        keys.left = keys.left || dx < 0;
      }
      break;
    }
    case "retreat": {
      // Head toward arena center (move_style<=8 in Python). Keeps the CPU
      // from being pinned on the ring boundary and lets the camera breathe.
      keys.right = arenaDx > 0;
      keys.left = arenaDx < 0;
      keys.down = arenaDy > 0;
      keys.up = arenaDy < 0;
      break;
    }
    case "chaos": {
      // Python's move_style==9/10 picks a random single-axis/diagonal dir.
      // We choose one on the rare ticks that jitterFramesLeft re-rolls,
      // and in-between keep a faint bias toward the opponent so the CPU
      // doesn't moonwalk off into a wall.
      const r = rand(st);
      if (r < 0.25) {
        keys.up = true;
      } else if (r < 0.5) {
        keys.down = true;
      } else if (r < 0.75) {
        keys.left = true;
      } else {
        keys.right = true;
      }
      // Faint opponent lean so chaos still contributes to combat.
      if (rand(st) < 0.3) {
        keys.right = keys.right || dx > 0;
        keys.left = keys.left || dx < 0;
      }
      break;
    }
  }
}

/**
 * Re-roll the movement style if its deadline has elapsed. Picks a new
 * style weighted toward charge/orbit (the ones that produce watchable
 * combat) and assigns a new expiry 3–5 seconds out @60fps.
 */
function maybeRerollStyle(st: AiState): void {
  if (st.tick < st.styleEndTick) return;
  const r = rand(st);
  let next: MovementStyle;
  if (r < 0.4) next = "charge";
  else if (r < 0.75) next = "orbit";
  else if (r < 0.9) next = "retreat";
  else next = "chaos";
  st.style = next;
  st.styleSign = rand(st) < 0.5 ? -1 : 1;
  // 3–5s at 60fps -> 180–300 frames.
  st.styleEndTick = st.tick + 180 + Math.floor(rand(st) * 120);
}

// ---------- main API ----------

/**
 * Decide inputs for a CPU-controlled player this frame.
 *
 * Priority order, matching auto_test_ai_control():
 *   1. Incoming projectile predicted to hit → dodge perpendicular,
 *      dash, shield if very close to impact.
 *   2. Otherwise apply the current movement style (charge/orbit/retreat/
 *      chaos) on a 3–5s picker. Within that:
 *        - weapon_a on its own cooldown (frequent beam fire)
 *        - weapon_b on its own cooldown (ballistic, less frequent)
 *        - special on its own cooldown when the opponent is close
 *        - hyper whenever the gauge allows and the attempt cooldown is 0
 *        - dash tactically in the far-range tier and occasionally
 *          during chaos style to shake the sprite off a predictable line
 *        - shield proactively if a bullet is inside the short-range halo
 *   3. Light random jitter so the sprite isn't a perfect chaser.
 *
 * Returns a fully-populated KeyStates (all 10 actions present).
 */
export function autoTestAiControl(
  self: Player,
  opponent: Player,
  arena: Arena,
  projectiles: Projectile[]
): KeyStates {
  const keys = emptyKeyStates();
  if (!self.isAlive || !opponent.isAlive) return keys;

  const st = getState(self);
  st.tick += 1;

  // --- decrement internal timers ---
  if (st.dashFrames > 0) st.dashFrames -= 1;
  if (st.dashCooldown > 0) st.dashCooldown -= 1;
  if (st.fireCooldown > 0) st.fireCooldown -= 1;
  if (st.weaponBCooldown > 0) st.weaponBCooldown -= 1;
  if (st.specialCooldown > 0) st.specialCooldown -= 1;
  if (st.hyperAttemptCooldown > 0) st.hyperAttemptCooldown -= 1;
  if (st.shieldCooldown > 0) st.shieldCooldown -= 1;
  if (st.jitterFramesLeft > 0) st.jitterFramesLeft -= 1;

  // --- geometry ---
  const dx = opponent.x - self.x;
  const dy = opponent.y - self.y;
  const distance = Math.sqrt(dx * dx + dy * dy) || 1;
  const arenaDx = arena.centerX - self.x;
  const arenaDy = arena.centerY - self.y;

  // Refresh movement style if its interval expired.
  maybeRerollStyle(st);

  // 1) DODGE incoming projectile ----------------------------------------
  const hit = predictProjectileCollision(self, projectiles, 30);
  if (hit) {
    const proj = hit.proj;
    // perpendicular to the projectile velocity
    const pvLen = Math.sqrt(proj.vx * proj.vx + proj.vy * proj.vy) || 1;
    let perpX = -proj.vy / pvLen;
    let perpY = proj.vx / pvLen;

    // If we're near the arena edge, prefer the perpendicular direction
    // that bends us back toward the arena center.
    const toCx = arena.centerX - self.x;
    const toCy = arena.centerY - self.y;
    const toCDist = Math.sqrt(toCx * toCx + toCy * toCy) || 1;
    if (toCDist > arena.radius * 0.7) {
      const cX = toCx / toCDist;
      const cY = toCy / toCDist;
      if (cX * perpX + cY * perpY < 0) {
        perpX = -perpX;
        perpY = -perpY;
      }
    } else if (rand(st) < 0.5) {
      perpX = -perpX;
      perpY = -perpY;
    }

    keys.right = perpX > 0.1;
    keys.left = perpX < -0.1;
    keys.down = perpY > 0.1;
    keys.up = perpY < -0.1;

    // Dash out of the way if we're allowed.
    if (st.dashCooldown <= 0) {
      keys.dash = true;
      st.dashFrames = 20;
      st.dashCooldown = 60;
    }
    // Can't dodge in time? Pop shield. Python uses 0.7; we gate on a
    // separate shield cooldown so it can't re-arm the very next frame.
    if (hit.timeToHit < 15 && st.shieldCooldown <= 0 && rand(st) < 0.7) {
      keys.shield = true;
      st.shieldCooldown = 90;
    }
    return keys;
  }

  // 2) movement via current style --------------------------------------
  applyMovementStyle(st, keys, dx, dy, distance, arenaDx, arenaDy);

  // Bias: in charge style when we're far, pile on a dash burst to close.
  if (st.style === "charge" && distance >= 400) {
    if (st.dashFrames > 0) {
      keys.dash = true;
    } else if (st.dashCooldown <= 0) {
      st.dashFrames = 30;
      st.dashCooldown = 90;
      keys.dash = true;
    }
  } else if (st.style === "orbit" && rand(st) < 0.01 && st.dashCooldown <= 0) {
    // Occasional strafe dash during orbits — makes CPU harder to track.
    st.dashFrames = 12;
    st.dashCooldown = 120;
    keys.dash = true;
  } else if (st.style === "chaos" && rand(st) < 0.02 && st.dashCooldown <= 0) {
    st.dashFrames = 12;
    st.dashCooldown = 90;
    keys.dash = true;
  }

  // 3) WEAPON A (beam) — frequent pressure shot ------------------------
  // Fire whenever cooldown lets us and opponent is within a reasonable
  // angle/range. We don't gate on angle because Player.ts re-aims each
  // shot at the opponent, but we do skip if we're retreating far to let
  // the CPU actually reposition.
  if (st.fireCooldown <= 0) {
    const fireChance =
      st.style === "retreat" ? 0.35 :
      st.style === "chaos" ? 0.45 :
      0.7;
    if (rand(st) < fireChance) {
      keys.weapon_a = true;
      st.fireCooldown = distance < 150 ? 12 : distance < 400 ? 15 : 22;
    } else {
      // Short retry window so we don't starve on a stretch of unlucky rolls.
      st.fireCooldown = 8;
    }
  }

  // 4) WEAPON B (ballistic) — medium-range arc shot --------------------
  // Python fires weapon_b with p=0.3. We copy that but gate on a 60-frame
  // cooldown (matches Player.ts WEAPON_B_COOLDOWN_FRAMES) so we don't ask
  // for it every frame and waste Player's edge-trigger.
  if (st.weaponBCooldown <= 0 && distance > 120 && distance < 500) {
    if (rand(st) < 0.3) {
      keys.weapon_b = true;
      st.weaponBCooldown = 70; // a bit above Player's 60 to add jitter
    } else {
      st.weaponBCooldown = 20;
    }
  }

  // 5) SPECIAL — close-range spread burst -------------------------------
  // Python fires special with p=0.1. Gate it on distance<300 and its own
  // cooldown so we don't mash it on every open frame.
  if (st.specialCooldown <= 0 && distance < 300) {
    if (rand(st) < 0.1) {
      keys.special = true;
      st.specialCooldown = 120;
    } else {
      st.specialCooldown = 30;
    }
  }

  // 6) HYPER — burn the gauge when it's full ---------------------------
  // Python: if hyper_gauge >= 100 and random<0.3. TS: HYPER_ACTIVATION_COST
  // is 50, so we use it as the trigger threshold instead of hardcoding 100.
  // Attempt cooldown avoids asking every frame while the gauge is full.
  if (
    st.hyperAttemptCooldown <= 0 &&
    self.hyperGauge >= HYPER_ACTIVATION_COST &&
    !self.isHyperActive
  ) {
    if (rand(st) < 0.3) {
      keys.hyper = true;
      // Don't try again for ~3s — either we activated (hyper lasts 180f)
      // or we rolled no this time and want to try again soon-ish.
      st.hyperAttemptCooldown = 180;
    } else {
      st.hyperAttemptCooldown = 30;
    }
  }

  // 7) PROACTIVE SHIELD — bullet in the short halo but not on a
  //    collision course (those are handled in branch 1). Python uses
  //    shield_chance=0.7 when nearby, 0.1 otherwise. We keep that shape
  //    but gate on shieldCooldown so the shield doesn't flicker.
  if (st.shieldCooldown <= 0) {
    const nearBullet = isProjectileNearby(self, projectiles, 70);
    const shieldChance = nearBullet ? 0.35 : 0.02;
    if (rand(st) < shieldChance) {
      keys.shield = true;
      st.shieldCooldown = 120;
    }
  }

  // 8) jitter so the sprite isn't a perfect chaser --------------------
  if (st.jitterFramesLeft <= 0) {
    const r = rand(st);
    if (r < 0.2) {
      st.jitterX = rand(st) < 0.5 ? -1 : 1;
      st.jitterY = rand(st) < 0.5 ? -1 : 1;
      st.jitterFramesLeft = 18;
    } else {
      st.jitterX = 0;
      st.jitterY = 0;
      st.jitterFramesLeft = 30;
    }
  }
  if (st.jitterX !== 0 || st.jitterY !== 0) {
    // Apply jitter as an OR onto the existing movement so the base
    // direction is preserved, we just nudge orthogonally.
    if (st.jitterX > 0) keys.right = true;
    else if (st.jitterX < 0) keys.left = true;
    if (st.jitterY > 0) keys.down = true;
    else if (st.jitterY < 0) keys.up = true;
  }

  return keys;
}

/**
 * Legacy, projectile-free CPU from the earliest milestone. Preserved so
 * other in-progress scenes that import `simpleAiControl` keep compiling
 * during the port. New code should prefer `autoTestAiControl`.
 */
export function simpleAiControl(
  self: Player,
  opponent: Player,
  frameCounter: number
): KeyStates {
  const keys = emptyKeyStates();
  if (!self.isAlive || !opponent.isAlive) return keys;

  const dx = opponent.x - self.x;
  const dy = opponent.y - self.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance > 200) {
    keys.right = dx > 0;
    keys.left = dx < 0;
    keys.down = dy > 0;
    keys.up = dy < 0;
    if (frameCounter % 45 === 0) keys.weapon_a = true;
  } else if (distance > 120) {
    const len = distance || 1;
    const px = -dy / len;
    const py = dx / len;
    keys.right = px > 0;
    keys.left = px < 0;
    keys.down = py > 0;
    keys.up = py < 0;
    if (frameCounter % 20 === 0) keys.weapon_a = true;
  } else {
    keys.left = dx > 0;
    keys.right = dx < 0;
    keys.up = dy > 0;
    keys.down = dy < 0;
    if (frameCounter % 15 === 0) keys.weapon_a = true;
  }

  return keys;
}
