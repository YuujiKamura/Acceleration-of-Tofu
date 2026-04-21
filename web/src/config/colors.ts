// Color palette ported from game/constants.py.
// Values are 24-bit 0xRRGGBB numbers, ready for Phaser's setTint/fillStyle APIs.
// Phaser's GameObject.setTint() and Graphics.fillStyle() both take this form.

export const WHITE = 0xffffff;
export const BLACK = 0x000000;
export const RED = 0xff0000;
export const GREEN = 0x00ff00;
export const BLUE = 0x0000ff;
export const SKY = 0x0096ff;
export const YELLOW = 0xffff00;
export const CYAN = 0x00ffff;
export const MAGENTA = 0xff00ff;
export const ORANGE = 0xffa500;
export const GRAY = 0x808080;

// Tofu-themed accents
export const NEGI_GREEN = 0x00b446;
export const BENI_RED = 0xc83232;
export const TOFU_WHITE = 0xf5f5f0;

export const COLORS = {
  WHITE,
  BLACK,
  RED,
  GREEN,
  BLUE,
  SKY,
  YELLOW,
  CYAN,
  MAGENTA,
  ORANGE,
  GRAY,
  NEGI_GREEN,
  BENI_RED,
  TOFU_WHITE,
} as const;

export type ColorName = keyof typeof COLORS;
