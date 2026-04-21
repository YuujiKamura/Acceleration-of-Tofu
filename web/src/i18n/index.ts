// Lightweight i18n runtime ported from game/i18n.py.
//
// Resolution order (first hit wins):
//   1. Explicit setLanguage(code) call
//   2. URL query ?lang=xx (window.location.search)
//   3. navigator.language first 2 chars
//   4. DEFAULT_LANG ("ja")
//
// Missing keys fall back to DEFAULT_LANG, then to the key itself. Never throws.

import { TRANSLATIONS, DEFAULT_LANG, type LangCode } from "./dict";

export type { LangCode };
export { DEFAULT_LANG };

let _currentLang: LangCode = DEFAULT_LANG;

function _isKnown(code: string | null | undefined): code is LangCode {
  return !!code && Object.prototype.hasOwnProperty.call(TRANSLATIONS, code);
}

function _detectFromUrl(): string | null {
  if (typeof window === "undefined" || !window.location) return null;
  try {
    const params = new URLSearchParams(window.location.search || "");
    const code = params.get("lang");
    if (!code) return null;
    return code.trim().toLowerCase().slice(0, 5) || null;
  } catch {
    return null;
  }
}

function _detectFromNavigator(): string | null {
  if (typeof navigator === "undefined") return null;
  const raw = navigator.language;
  if (!raw) return null;
  return raw.toLowerCase().split("-", 1)[0].slice(0, 5) || null;
}

function _resolveLang(preferred: string | null | undefined): LangCode {
  const candidates: Array<string | null> = [
    preferred ? String(preferred).toLowerCase() : null,
    _detectFromUrl(),
    _detectFromNavigator(),
    DEFAULT_LANG,
  ];
  for (const c of candidates) {
    if (_isKnown(c)) return c;
  }
  return DEFAULT_LANG;
}

/** Override the current language. Returns the actually applied code. */
export function setLanguage(code: string | null): LangCode {
  _currentLang = _resolveLang(code);
  return _currentLang;
}

export function getLanguage(): LangCode {
  return _currentLang;
}

export function availableLanguages(): LangCode[] {
  return (Object.keys(TRANSLATIONS) as LangCode[]).sort();
}

/**
 * Translate a key. Optional args fill `{name}` placeholders via simple regex
 * substitution. Resolution: current -> default -> key itself. Never throws.
 */
export function tr(key: string, args?: Record<string, string | number>): string {
  let entry = TRANSLATIONS[_currentLang]?.[key];
  if (entry === undefined) {
    entry = TRANSLATIONS[DEFAULT_LANG]?.[key];
  }
  if (entry === undefined) {
    entry = key;
  }
  if (args) {
    return entry.replace(/\{(\w+)\}/g, (match, name: string) => {
      const v = args[name];
      return v === undefined || v === null ? match : String(v);
    });
  }
  return entry;
}

// Eager auto-detect on import so modules that capture tr(...) at import-time
// see the right language. Explicit setLanguage() later still wins.
setLanguage(null);
