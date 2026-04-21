// Translation dictionary ported from game/i18n.py.
// Keys use the same dot-separated convention as the Python source so shared
// references (e.g. "hud.heat", "controls.title") stay stable across ports.

export type LangCode = "ja" | "en";

export const DEFAULT_LANG: LangCode = "ja";

export const TRANSLATIONS: Record<LangCode, Record<string, string>> = {
  ja: {
    // --- window / meta ---
    title: "アクセラレーションオブ豆腐",

    // --- HUD (placeholders use {value}) ---
    "hud.heat": "ヒート: {value}%",
    "hud.hyper": "ハイパー: {value}%",
    "hud.water": "水分: {value}%",
    "hud.bean": "豆: {value}%",
    "hud.aging": "熟成: {value}%",
    "hud.overheat": "OVERHEAT",
    "hud.hyper_active": "ハイパーモード発動中! (ダメージ2倍)",

    // --- splash / main menu ---
    "splash.title": "アクセラレーションオブ豆腐",
    "title.mute_hint_on": "M: 音声 ON",
    "title.mute_hint_off": "M: 音声 OFF",

    // --- title menu entries (web-only addition for TitleScene) ---
    "menu.single": "シングル対戦モード",
    "menu.training": "トレーニングモード",
    "menu.autotest": "自動テスト",
    "menu.controls": "操作説明",
    "menu.options": "オプション",
    "menu.quit": "終了",

    // --- controls screen ---
    "controls.title": "操作説明",
    "controls.player1": "プレイヤー1",
    "controls.player2": "プレイヤー2",
    "controls.common": "共通",
    "controls.back": "戻る: ESCキー または 決定ボタン",

    // --- options / key-config ---
    "options.title": "オプション",
    "keyconfig.title": "キー設定",
  },
  en: {
    title: "Acceleration of Tofu",

    "hud.heat": "Heat: {value}%",
    "hud.hyper": "Hyper: {value}%",
    "hud.water": "Water: {value}%",
    "hud.bean": "Bean: {value}%",
    "hud.aging": "Aged: {value}%",
    "hud.overheat": "OVERHEAT",
    "hud.hyper_active": "Hyper Mode Active! (2x damage)",

    "splash.title": "Acceleration of Tofu",
    "title.mute_hint_on": "M: Sound ON",
    "title.mute_hint_off": "M: Sound OFF",

    "menu.single": "Single Versus",
    "menu.training": "Training",
    "menu.autotest": "Auto Test",
    "menu.controls": "Controls",
    "menu.options": "Options",
    "menu.quit": "Quit",

    "controls.title": "Controls",
    "controls.player1": "Player 1",
    "controls.player2": "Player 2",
    "controls.common": "Common",
    "controls.back": "Back: ESC or Confirm button",

    "options.title": "Options",
    "keyconfig.title": "Key Config",
  },
};
