import Phaser from "phaser";
import type { ActionName, KeyStates } from "../entities/Player";
import { emptyKeyStates } from "../entities/Player";

/**
 * mapKeyboardToActions
 *
 * Takes a mapping keyed by DOM `KeyboardEvent.code` strings (the same
 * shape Agent C exports as DEFAULT_KEY_MAPPING_P1 / P2 — e.g.
 * `{ "ArrowUp": "up", "KeyZ": "weapon_a", "Space": "hyper" }`) and
 * returns a `readKeyStates()` sampler. Call the sampler once per frame;
 * it produces a fresh KeyStates snapshot so Players / AI can OR-together
 * control sources without mutating each other.
 *
 * Implementation note: Phaser's `keyboard.addKey()` accepts a numeric
 * keycode from `Phaser.Input.Keyboard.KeyCodes`. We translate DOM
 * `code` values -> Phaser KeyCodes via `domCodeToPhaserKeyCode`. Codes
 * we don't recognize are ignored with a console warning; a bad key
 * binding should not crash the whole game.
 */
export type KeyActionMapping = Record<string, string>;

const DOM_CODE_TO_PHASER: Record<string, number | undefined> = (() => {
  const K = Phaser.Input.Keyboard.KeyCodes;
  const m: Record<string, number | undefined> = {};

  // Arrows
  m.ArrowUp = K.UP;
  m.ArrowDown = K.DOWN;
  m.ArrowLeft = K.LEFT;
  m.ArrowRight = K.RIGHT;

  // Modifiers / whitespace
  m.Space = K.SPACE;
  m.Enter = K.ENTER;
  m.Escape = K.ESC;
  m.ShiftLeft = K.SHIFT;
  m.ShiftRight = K.SHIFT;
  m.ControlLeft = K.CTRL;
  m.ControlRight = K.CTRL;
  m.AltLeft = K.ALT;
  m.AltRight = K.ALT;
  m.Tab = K.TAB;
  m.Backspace = K.BACKSPACE;

  // Letters KeyA..KeyZ
  for (let i = 0; i < 26; i++) {
    const letter = String.fromCharCode(65 + i); // "A".."Z"
    const code = (K as Record<string, number | undefined>)[letter];
    m[`Key${letter}`] = code;
  }

  // Digits Digit0..Digit9
  for (let i = 0; i < 10; i++) {
    const code = (K as Record<string, number | undefined>)[`_${i}`] ??
      (K as Record<string, number | undefined>)[`NUMBER_${i}`] ??
      (K as Record<string, number | undefined>)[`DIGIT_${i}`];
    m[`Digit${i}`] = code ?? 48 + i; // fallback: ascii
  }

  return m;
})();

export function domCodeToPhaserKeyCode(code: string): number | undefined {
  return DOM_CODE_TO_PHASER[code];
}

/**
 * @param mapping DOM code -> action name (e.g. "KeyZ" -> "weapon_a").
 *                Only keys whose values are valid ActionName enter the
 *                binding set; unknown values are skipped silently.
 */
export function mapKeyboardToActions(
  scene: Phaser.Scene,
  mapping: KeyActionMapping
): () => KeyStates {
  const kb = scene.input.keyboard;
  if (!kb) {
    // eslint-disable-next-line no-console
    console.warn("[Input] keyboard plugin unavailable; returning empty states");
    return () => emptyKeyStates();
  }

  const validActions = new Set<ActionName>([
    "up",
    "down",
    "left",
    "right",
    "weapon_a",
    "weapon_b",
    "hyper",
    "dash",
    "special",
    "shield",
  ]);

  const bindings: Array<{ key: Phaser.Input.Keyboard.Key; action: ActionName }> = [];
  for (const domCode of Object.keys(mapping)) {
    const actionStr = mapping[domCode];
    if (!validActions.has(actionStr as ActionName)) {
      // eslint-disable-next-line no-console
      console.warn(`[Input] unknown action for ${domCode}: ${actionStr}`);
      continue;
    }
    const phaserCode = domCodeToPhaserKeyCode(domCode);
    if (phaserCode === undefined) {
      // eslint-disable-next-line no-console
      console.warn(`[Input] unknown DOM code: ${domCode}`);
      continue;
    }
    const key = kb.addKey(phaserCode);
    bindings.push({ key, action: actionStr as ActionName });
  }

  return (): KeyStates => {
    const states = emptyKeyStates();
    for (const b of bindings) {
      if (b.key.isDown) states[b.action] = true;
    }
    return states;
  };
}
