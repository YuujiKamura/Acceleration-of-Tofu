import type { Player, KeyStates } from "../entities/Player";
import { emptyKeyStates } from "../entities/Player";

/**
 * simpleAiControl
 *
 * Minimal port of game/ai.py::AIController.simple_ai_control. Goal for
 * the first milestone is "two circles visibly circling and shooting" —
 * not competitive play. Behavior:
 *   - far (>150px): advance toward opponent, fire weapon_a periodically
 *   - close (<=150px): strafe sideways, fire more often
 *
 * The returned KeyStates is a FRESH object per call; safe to assign
 * directly to `player.keyStates`.
 *
 * `frameCounter` is provided by the caller (scene update count) and
 * drives the periodic fire gates — same role as game.current_time in
 * the Python source.
 */
export function simpleAiControl(
  self: Player,
  opponent: Player,
  frameCounter: number
): KeyStates {
  const keys = emptyKeyStates();
  if (!self.isAlive || !opponent.isAlive) {
    return keys;
  }

  const dx = opponent.x - self.x;
  const dy = opponent.y - self.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  if (distance > 200) {
    // close the gap
    keys.right = dx > 0;
    keys.left = dx < 0;
    keys.down = dy > 0;
    keys.up = dy < 0;
    if (frameCounter % 45 === 0) {
      keys.weapon_a = true;
    }
  } else if (distance > 120) {
    // mid-range: strafe perpendicular to the line-of-sight while keeping
    // the opponent roughly in front. Perp of (dx, dy) is (-dy, dx).
    const len = distance || 1;
    const px = -dy / len;
    const py = dx / len;
    keys.right = px > 0;
    keys.left = px < 0;
    keys.down = py > 0;
    keys.up = py < 0;
    if (frameCounter % 20 === 0) {
      keys.weapon_a = true;
    }
  } else {
    // back off a little so they don't stack on top of each other
    keys.left = dx > 0;
    keys.right = dx < 0;
    keys.up = dy > 0;
    keys.down = dy < 0;
    if (frameCounter % 15 === 0) {
      keys.weapon_a = true;
    }
  }

  return keys;
}
