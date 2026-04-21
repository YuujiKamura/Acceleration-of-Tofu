import type { Player } from "../entities/Player";
import type { Projectile } from "../entities/Projectile";

/**
 * Combat
 *
 * Pure (no Phaser/DOM) collision + special-interaction system. Ported
 * from the relevant branches of game/game.py::Game.handle_collisions
 * and Game._apply_sticky_tether.
 *
 * Kept separate from Projectile.ts because the damage rules pull in
 * attacker state (heat, hyper) — forcing that logic into Projectile
 * would couple the projectile class to the Player class more tightly
 * than it should be.
 *
 * Functions here MUST stay pure (aside from the documented mutations
 * on their arguments) so we can unit-test them in node without a
 * Phaser scene.
 */

// Sticky-tether range (px) and max per-frame pull speed (px/frame).
// Matches legacy/pygbag/game/game.py::_apply_sticky_tether exactly:
//     distance < 100 and distance > 5
//     strength = (1.0 - (distance / 100.0)) * 1.5
const TETHER_RANGE = 100;
const TETHER_MIN_DISTANCE = 5;
const TETHER_STRENGTH_SCALAR = 1.5;

/**
 * Resolve projectile-vs-player collisions in-place.
 *
 * For each projectile not already expired, check each *opposing* player
 * (projectiles never hit their own owner). On a hit:
 *   damage = proj.damage * (1 + attacker.heat/100) * (isHyper ? 2 : 1)
 * where attacker = proj.owner. Mark the projectile expired and call the
 * defender's takeDamage() (which handles shield + flash internally).
 *
 * `effects` is a passthrough: future hit-spark code will push into it,
 * but the MVP doesn't emit anything yet. We accept it so the scene
 * signature stays stable when D4 wires this in.
 */
export function handleCollisions(
  players: Player[],
  projectiles: Projectile[],
  _effects: unknown[]
): void {
  for (const proj of projectiles) {
    if (proj.isExpired) continue;
    for (const defender of players) {
      if (defender === proj.owner) continue;
      if (!defender.isAlive) continue;
      if (!proj.collidesWith(defender)) continue;

      const attacker = proj.owner;
      const heatMult = 1 + attacker.heat / 100;
      const hyperMult = attacker.isHyperActive ? 2 : 1;
      const dmg = proj.damage * heatMult * hyperMult;
      defender.takeDamage(dmg);
      proj.isExpired = true;
      break; // one projectile, at most one hit per frame
    }
  }
}

/**
 * Apply the fermented-player sticky tether: pull the opponent toward
 * the fermented player, with strength falling off linearly with
 * distance. No-op if the fermented side isn't fermented, if the pair
 * is further than TETHER_RANGE apart, or if they're already
 * overlapping (< TETHER_MIN_DISTANCE).
 *
 * Mutates `opponent.x` / `opponent.y` directly, same shape as the
 * Python source. Caller should invoke this AFTER both players have
 * moved for the frame, BEFORE collision resolution — matches the
 * ordering in game.py::update_gameplay_elements.
 */
export function applyStickyTether(fermented: Player, opponent: Player): void {
  if (!fermented.isFermented) return;
  const dx = fermented.x - opponent.x;
  const dy = fermented.y - opponent.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  if (distance >= TETHER_RANGE || distance <= TETHER_MIN_DISTANCE) return;

  const strength =
    (1 - distance / TETHER_RANGE) * TETHER_STRENGTH_SCALAR;
  // angle from opponent -> fermented (so movement is toward fermented)
  const angle = Math.atan2(dy, dx);
  opponent.x += Math.cos(angle) * strength;
  opponent.y += Math.sin(angle) * strength;
}

/**
 * Resolve player-vs-player overlap with water_level-weighted push-back.
 *
 * 1:1 port of legacy/pygbag/game/game.py::Game.handle_collisions
 * lines 349-378. If the two player circles overlap, both are shoved
 * apart along the line between them; the share of the push each player
 * absorbs is weighted by the OPPONENT's effective mass, so a "heavier"
 * (higher waterLevel) player is pushed LESS and the lighter player is
 * pushed MORE.
 *
 * Effective mass = 0.5 + (waterLevel/100) * 0.5, i.e. in [0.5, 1.0].
 * Degenerate case: if the two players are exactly co-located, pick a
 * random angle to break the tie (same as Python).
 *
 * Mutates p1.x/p1.y and p2.x/p2.y directly. No effect if the players
 * are not overlapping.
 */
export function resolvePlayerCollision(p1: Player, p2: Player): void {
  const dx = p1.x - p2.x;
  const dy = p1.y - p2.y;
  const distance = Math.hypot(dx, dy);
  const minDist = p1.radius + p2.radius;
  if (distance >= minDist) return;

  let angle: number;
  let overlap: number;
  if (distance === 0) {
    angle = Math.random() * Math.PI * 2;
    overlap = minDist;
  } else {
    angle = Math.atan2(dy, dx);
    overlap = minDist - distance;
  }

  const w1 = 0.5 + (p1.waterLevel / 100) * 0.5;
  const w2 = 0.5 + (p2.waterLevel / 100) * 0.5;
  const totalW = w1 + w2;
  const ratio1 = w2 / totalW;
  const ratio2 = w1 / totalW;

  const cosA = Math.cos(angle);
  const sinA = Math.sin(angle);
  p1.x += cosA * (overlap * ratio1);
  p1.y += sinA * (overlap * ratio1);
  p2.x -= cosA * (overlap * ratio2);
  p2.y -= sinA * (overlap * ratio2);
}
