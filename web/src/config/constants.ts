// Ported from game/constants.py
// Values kept in sync with the Python source. Frame-based durations stay
// frame-based (we run Phaser at FPS=60) so gameplay tuning transfers 1:1.

// --- Window ---
export const SCREEN_WIDTH = 1280;
export const SCREEN_HEIGHT = 720;
export const FPS = 60;
export const TITLE = "アクセラレーションオブ豆腐";

// --- Arena ---
export const ARENA_RADIUS = 300;
export const ARENA_CENTER_X = SCREEN_WIDTH / 2;
export const ARENA_CENTER_Y = SCREEN_HEIGHT / 2;
export const ARENA_WARNING_RADIUS = ARENA_RADIUS - 20;

// --- Player ---
export const PLAYER_SPEED = 5;
export const PLAYER_DASH_SPEED = 9;
export const DASH_RING_DURATION = 30;
export const DASH_COOLDOWN = 5;
// Ported from game/player.py ctor: self.dash_turn_speed = 0.15
// Low-pass filter alpha for dash direction turning (per-frame @ 60Hz).
export const DASH_TURN_SPEED = 0.15;
export const SHIELD_DURATION = 50;
export const SHIELD_COOLDOWN = 120;
export const HYPER_DURATION = 180;
export const MAX_HEALTH = 1000;
export const MAX_HEAT = 300;
export const MAX_HYPER = 300;
export const HEAT_DECREASE_RATE = 1.0;
export const HYPER_DECREASE_RATE_AT_BORDER = 2;
export const HYPER_CONSUMPTION_RATE = 1.0;
export const HYPER_ACTIVATION_COST = 50;

// --- Weapon_B burst / special spread (player.py:255-256) ---
// Python 原版は burst_total=10 だが、視覚的に弾幕が多すぎる
// (灰色の豆みたいな弾が大量) という UX 判断で 5 に削減。burst_delay は維持。
export const WEAPON_B_BURST_TOTAL = 5;
export const WEAPON_B_BURST_DELAY = 5;
// player.py:675,678 — special (weapon_b + special) costs 100 hyper gauge.
export const SPECIAL_HYPER_COST = 100;
// player.py:899 spread_angle = math.pi / 8 (22.5°) — base fan step.
export const SPECIAL_SPREAD_ANGLE = Math.PI / 8;
// player.py:934 — second bullet of special spread is offset by an extra
// pi/16 (11.25°) beyond the primary bullet.
export const SPECIAL_SPREAD_OFFSET = Math.PI / 16;
// special_b weapon stats (player.py:230): BEAM, damage=10, cooldown=15.
export const SPECIAL_B_DAMAGE = 10;
export const SPECIAL_B_COOLDOWN_FRAMES = 15;
// Blue color for special spread projectiles — (50,100,255) in Python.
export const SPECIAL_SPREAD_COLOR = 0x3264ff;

// --- Weapons ---
export const WEAPON_TYPES = {
  BEAM: "beam",
  BALLISTIC: "ballistic",
  MELEE: "melee",
} as const;

export type WeaponType = (typeof WEAPON_TYPES)[keyof typeof WEAPON_TYPES];

// --- Game modes ---
export const GAME_MODES = {
  TITLE: 0,
  GAME: 1,
  TRAINING: 2,
  AUTO_TEST: 3,
} as const;

export type GameMode = (typeof GAME_MODES)[keyof typeof GAME_MODES];

// --- Action names ---
// Mirrors ACTION_NAMES from the Python source. Kept as a plain record
// because the values are display strings, not stable identifiers.
export const ACTION_NAMES: Record<string, string> = {
  up: "上移動",
  down: "下移動",
  left: "左移動",
  right: "右移動",
  weapon_a: "武器A (ビームライフル)",
  weapon_b: "武器B (バリスティック)",
  hyper: "ハイパーモード",
  dash: "ダッシュ",
  special: "スペシャル攻撃",
  shield: "シールド",
};

// --- Key mappings ---
// Maps `KeyboardEvent.code` strings to action names. The Python source keys
// by pygame keycode; we translate to DOM key codes here.
export const DEFAULT_KEY_MAPPING_P1: Record<string, string> = {
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
  KeyZ: "weapon_a",
  KeyJ: "weapon_a",
  KeyX: "weapon_b",
  KeyK: "weapon_b",
  Space: "hyper",
  KeyL: "hyper",
  ShiftLeft: "dash",
  KeyH: "dash",
  KeyC: "special",
  KeyV: "shield",
};

export const DEFAULT_KEY_MAPPING_P2: Record<string, string> = {
  KeyW: "up",
  KeyS: "down",
  KeyA: "left",
  KeyD: "right",
  KeyF: "weapon_a",
  KeyG: "weapon_b",
  KeyR: "hyper",
  KeyE: "dash",
  KeyT: "special",
  KeyY: "shield",
};

// --- Sound effect paths (Vite-relative; public/ hosts the assets tree) ---
export const SOUND_EFFECTS = {
  BGM: {
    TITLE: "assets/sounds/rockman_title.ogg",
  },
  UI: {
    CURSOR: "assets/sounds/menu.ogg",
    SELECT: "assets/sounds/stage_clear.ogg",
    CANCEL: "assets/sounds/damage.ogg",
    HIGHSCORE: "assets/sounds/1up.ogg",
  },
  PLAYER: {
    JUMP: "assets/sounds/jump.ogg",
    LAND: "assets/sounds/land.ogg",
    DASH: "assets/sounds/special.ogg",
    SHIELD: "assets/sounds/shield.ogg",
    HYPER: "assets/sounds/hyper.ogg",
  },
  WEAPON: {
    SHOT: "assets/sounds/shot.ogg",
    CHARGE: "assets/sounds/charge.ogg",
    HIT: "assets/sounds/hit.ogg",
    SPECIAL: "assets/sounds/special.ogg",
  },
  SYSTEM: {
    BOSS: "assets/sounds/boss_appear.ogg",
    DAMAGE: "assets/sounds/damage.ogg",
    ITEM: "assets/sounds/item.ogg",
  },
} as const;

// --- Volume settings ---
// NOTE: spec asks for BGM: 0.3 (the Python source has 0.7). Using the spec value.
export const VOLUME_SETTINGS = {
  BGM: 0.3,
  UI: 0.6,
  PLAYER: 0.7,
  WEAPON: 0.5,
  SYSTEM: 0.7,
} as const;
