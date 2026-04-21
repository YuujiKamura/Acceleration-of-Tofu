# -*- coding: utf-8 -*-
"""
Lightweight i18n layer.

Usage:
    from game.i18n import tr, set_language, get_language
    tr("title")                      # -> "アクセラレーションオブ豆腐" (default ja)
    set_language("en"); tr("title")  # -> "Acceleration of Tofu"
    tr("hud.heat", value=42)         # -> "Heat: 42%"

Language resolution order (first hit wins):
    1. Explicit set_language(code) call
    2. URL query ?lang=xx   (in pygbag/WASM via window.location)
    3. Environment variable TOFU_LANG
    4. CLI arg --lang (parsed by main.py and passed to set_language)
    5. Browser navigator.language first 2 chars (WASM only)
    6. Default "ja"

Missing keys fall back to the default language, then to the key itself.
Never crashes on an unknown key — keeps the UI alive.
"""

from __future__ import annotations

import os
import sys

DEFAULT_LANG = "ja"

# ---------------------------------------------------------------------------
# Translation dictionary
# Keep keys stable and dot-separated by subsystem. New languages = add a new
# top-level key here. Missing entries fall back to DEFAULT_LANG.
# ---------------------------------------------------------------------------
TRANSLATIONS: dict[str, dict[str, str]] = {
    "ja": {
        # --- window / meta ---
        "title": "アクセラレーションオブ豆腐",

        # --- HUD (f-string-ready with {value} placeholders) ---
        "hud.heat": "ヒート: {value}%",
        "hud.hyper": "ハイパー: {value}%",
        "hud.water": "水分: {value}%",
        "hud.bean": "豆: {value}%",
        "hud.aging": "熟成: {value}%",
        "hud.overheat": "OVERHEAT",
        "hud.hyper_active": "ハイパーモード発動中! (ダメージ2倍)",

        # --- splash / main menu ---
        "splash.title": "アクセラレーションオブ豆腐",
        "title.mute_hint_on": "M: 音声 ON",
        "title.mute_hint_off": "M: 音声 OFF",

        # --- controls screen ---
        "controls.title": "操作説明",
        "controls.player1": "プレイヤー1",
        "controls.player2": "プレイヤー2",
        "controls.common": "共通",
        "controls.back": "戻る: ESCキー または 決定ボタン",

        # --- options / key-config ---
        "options.title": "オプション",
        "keyconfig.title": "キー設定",
    },
    "en": {
        "title": "Acceleration of Tofu",

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

        "controls.title": "Controls",
        "controls.player1": "Player 1",
        "controls.player2": "Player 2",
        "controls.common": "Common",
        "controls.back": "Back: ESC or Confirm button",

        "options.title": "Options",
        "keyconfig.title": "Key Config",
    },
}

_current_lang = DEFAULT_LANG


def _detect_from_url() -> str | None:
    """Read ?lang=xx from browser URL when running under pygbag/pyodide."""
    if sys.platform != "emscripten":
        return None
    try:
        # When running under pygbag, `platform.window` gives access to the JS window.
        import platform as _platform  # type: ignore

        href = _platform.window.location.href  # type: ignore[attr-defined]
    except Exception:
        return None
    # Manual tiny query parser to avoid urllib overhead on boot.
    if "?" not in href:
        return None
    query = href.split("?", 1)[1].split("#", 1)[0]
    for part in query.split("&"):
        if part.startswith("lang="):
            code = part[5:].strip().lower()[:5]
            return code or None
    return None


def _detect_from_navigator() -> str | None:
    """Fallback: browser navigator.language (e.g. "en-US" -> "en")."""
    if sys.platform != "emscripten":
        return None
    try:
        import platform as _platform  # type: ignore

        lang = _platform.window.navigator.language  # type: ignore[attr-defined]
    except Exception:
        return None
    if not lang:
        return None
    return str(lang).lower().split("-", 1)[0][:5]


def _detect_from_env() -> str | None:
    code = os.environ.get("TOFU_LANG") or os.environ.get("LANG")
    if not code:
        return None
    # "ja_JP.UTF-8" -> "ja"
    return code.split("_", 1)[0].split(".", 1)[0].strip().lower()[:5] or None


def _resolve_lang(preferred: str | None) -> str:
    """Return a language code present in TRANSLATIONS, falling back to default."""
    candidates = [
        preferred,
        _detect_from_url(),
        _detect_from_env(),
        _detect_from_navigator(),
        DEFAULT_LANG,
    ]
    for c in candidates:
        if c and c in TRANSLATIONS:
            return c
    return DEFAULT_LANG


def set_language(code: str | None) -> str:
    """Override current language. Returns the resolved code actually applied."""
    global _current_lang
    _current_lang = _resolve_lang(code)
    return _current_lang


def get_language() -> str:
    return _current_lang


def available_languages() -> list[str]:
    return sorted(TRANSLATIONS.keys())


def tr(key: str, **kwargs) -> str:
    """Translate `key` into the current language, with optional {placeholder} fill.

    Resolution: current -> default -> key itself. Never raises.
    """
    entry = TRANSLATIONS.get(_current_lang, {}).get(key)
    if entry is None:
        entry = TRANSLATIONS.get(DEFAULT_LANG, {}).get(key, key)
    if kwargs:
        try:
            return entry.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return entry
    return entry


# Eager auto-detect on import so modules that capture tr(...) at import-time
# (e.g. constants.py) see the right language. Explicit set_language() later
# still wins.
set_language(None)
