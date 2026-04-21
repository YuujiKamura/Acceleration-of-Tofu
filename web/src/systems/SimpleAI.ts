import type { Player, KeyStates } from "../entities/Player";
import { emptyKeyStates } from "../entities/Player";
import type { Projectile } from "../entities/Projectile";
import type { Arena } from "../entities/Arena";

/**
 * CPU AI controller — port of game/ai.py::AIController.auto_test_ai_control
 * plus the legacy game/ai.py::AIController.simple_ai_control fallback.
 *
 * Exports:
 *   - autoTestAiControl(self, opponent, arena, projectiles) — richer,
 *     projectile-aware behavior tree.
 *   - simpleAiControl(self, opponent, frameCounter) — legacy trivial AI,
 *     kept for any scene that has not yet migrated.
 *   - resetAi(player) — drop per-Player AI state (call on scene reset).
 *
 * Per-Player AI state (fire cooldowns, dash bursts, RNG-ish timers) is
 * stashed in a WeakMap so the state follows the Player identity across
 * frames. Two independent CPUs (P1+P2) each get their own record.
 */

// ---------- internal state ----------

interface AiState {
  /** frames remaining on the current dash burst */
  dashFrames: number;
  /** frames until we're allowed to start a new dash burst */
  dashCooldown: number;
  /** frames until the next weapon_a shot is allowed (advance-and-fire mode) */
  fireCooldown: number;
  /** deterministic per-Player rng so jitter doesn't thrash sprite every frame */
  rngSeed: number;
  /** internal tick counter; drives jitter phase */
  tick: number;
  /** remembered jitter vector, refreshed every ~20 ticks */
  jitterX: number;
  jitterY: number;
  jitterFramesLeft: number;
}

const STATE = new WeakMap<Player, AiState>();

function initialState(): AiState {
  // Seed from Math.random so two parallel CPUs start out of phase. This
  // only runs once per Player, the actual per-frame RNG is the LCG below.
  return {
    dashFrames: 0,
    dashCooldown: 0,
    fireCooldown: 0,
    rngSeed: (Math.random() * 0x7fffffff) | 0 || 1,
    tick: 0,
    jitterX: 0,
    jitterY: 0,
    jitterFramesLeft: 0,
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

// ---------- main API ----------

/**
 * Decide inputs for a CPU-controlled player this frame.
 *
 * Priority order, matching auto_test_ai_control():
 *   1. Incoming projectile → dodge perpendicular, dash, maybe shield
 *   2. Very close (<150px) → back off while firing weapon_a
 *   3. Mid range (150-400) → advance while firing weapon_a on cooldown
 *   4. Far (>=400) → close fast in dash bursts
 *   5. Light random jitter for visual variety
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
  if (st.dashFrames > 0) {
    st.dashFrames -= 1;
  }
  if (st.dashCooldown > 0) st.dashCooldown -= 1;
  if (st.fireCooldown > 0) st.fireCooldown -= 1;
  if (st.jitterFramesLeft > 0) st.jitterFramesLeft -= 1;

  // --- geometry ---
  const dx = opponent.x - self.x;
  const dy = opponent.y - self.y;
  const distance = Math.sqrt(dx * dx + dy * dy) || 1;

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
    // Close call? Pop shield.
    if (hit.timeToHit < 15 && rand(st) < 0.6) {
      keys.shield = true;
    }
    return keys;
  }

  // Secondary "proximity" panic shield — not lethal yet, but close.
  const nearBullet = isProjectileNearby(self, projectiles, 70);

  // 2/3/4) movement tier by range --------------------------------------
  if (distance < 150) {
    // Too close — back off along (self - opponent) direction and shoot.
    keys.left = dx > 0;
    keys.right = dx < 0;
    keys.up = dy > 0;
    keys.down = dy < 0;
    if (st.fireCooldown <= 0) {
      keys.weapon_a = true;
      st.fireCooldown = 15;
    }
  } else if (distance < 400) {
    // Mid range — advance toward opponent and fire every ~15 frames.
    keys.right = dx > 0;
    keys.left = dx < 0;
    keys.down = dy > 0;
    keys.up = dy < 0;
    if (st.fireCooldown <= 0) {
      keys.weapon_a = true;
      st.fireCooldown = 15;
    }
  } else {
    // Far — close distance with dash bursts.
    keys.right = dx > 0;
    keys.left = dx < 0;
    keys.down = dy > 0;
    keys.up = dy < 0;
    if (st.dashFrames > 0) {
      keys.dash = true;
    } else if (st.dashCooldown <= 0) {
      st.dashFrames = 30;
      st.dashCooldown = 90;
      keys.dash = true;
    }
    // Still take opportunistic shots on the way in.
    if (st.fireCooldown <= 0) {
      keys.weapon_a = true;
      st.fireCooldown = 25;
    }
  }

  // 5) occasional random jitter so the sprite isn't a perfect chaser ---
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

  // Panic shield if a bullet is inside the short-range halo.
  if (nearBullet && rand(st) < 0.15) {
    keys.shield = true;
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
