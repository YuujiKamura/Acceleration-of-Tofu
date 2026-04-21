import Phaser from "phaser";

/**
 * AudioManager
 *
 * Port of the Python audio subsystem from legacy/pygbag/game/game.py
 * (init_sounds / init_title_bgm / play_title_bgm / toggle_mute).
 *
 * Responsibilities:
 *   - Preload the 7 required .ogg assets (via loadAll, driven by BootScene).
 *   - Play looping BGM keyed by name (currently "rockman_title" at 0.3).
 *   - Play one-shot SFX keyed by name (shot/special/hit/shield/hyper/menu).
 *   - Global mute toggle bound to the "M" key at the DOM level so it
 *     works from any scene regardless of per-scene input routing.
 *
 * Usage:
 *   - Call AudioManager.init(game) once, right after `new Phaser.Game(config)`.
 *   - Call AudioManager.get().loadAll(scene) from BootScene to preload.
 *   - Call playBgm / stopBgm / playSfx from scenes as needed.
 */

const SFX_KEYS = [
  "shot",
  "special",
  "hit",
  "shield",
  "hyper",
  "menu",
] as const;
const BGM_KEYS = ["rockman_title"] as const;

type SfxKey = (typeof SFX_KEYS)[number];
type BgmKey = (typeof BGM_KEYS)[number];
type AudioKey = SfxKey | BgmKey;

const SOUND_FILES: Record<AudioKey, string> = {
  rockman_title: "sounds/rockman_title.ogg",
  shot: "sounds/shot.ogg",
  special: "sounds/special.ogg",
  hit: "sounds/hit.ogg",
  shield: "sounds/shield.ogg",
  hyper: "sounds/hyper.ogg",
  menu: "sounds/menu.ogg",
};

const BGM_VOLUMES: Record<BgmKey, number> = {
  // Match the Python init_title_bgm(): set_volume(0.3) at startup so the
  // first user interaction doesn't blast them.
  rockman_title: 0.3,
};

// BGM (0.3) と揃える。Python 原版の set_volume(0.3) と同値。
// 「一瞬でかい」問題は音量値ではなく WebAudio unlock 直後のゲイン経路の
// 初期化タイミングが原因 (warmupSfxGraph 参照)。
const DEFAULT_SFX_VOLUME = 0.3;

export class AudioManager {
  private static instance: AudioManager | null = null;

  private readonly game: Phaser.Game;
  private currentBgm: Phaser.Sound.BaseSound | null = null;
  private currentBgmKey: BgmKey | null = null;
  private muted = false;
  private keydownHandler: ((ev: KeyboardEvent) => void) | null = null;
  private indicator: HTMLButtonElement | null = null;

  private constructor(game: Phaser.Game) {
    this.game = game;
    this.installGlobalMuteHotkey();
    this.installMuteIndicator();
  }

  static init(game: Phaser.Game): AudioManager {
    if (AudioManager.instance) {
      return AudioManager.instance;
    }
    AudioManager.instance = new AudioManager(game);
    // Also stash on the Game registry so other systems (or a future
    // devtool overlay) can discover the singleton without importing it.
    game.registry.set("audioManager", AudioManager.instance);
    AudioManager.instance.warmupSfxGraph();
    return AudioManager.instance;
  }

  /**
   * "First-play full volume pop" 対策。
   *
   * WebAudio の AudioContext は最初のユーザー操作 (keydown/click) で
   * unlock されるまで suspend されている。Phaser は unlock 後に各サウンド
   * キーを都度 add+play で再生するが、ある特定のキーが「この AudioContext
   * で初めて鳴る」タイミングでは GainNode と Source の接続順に数ミリ秒の
   * 競合があり、gain=0.3 を設定する前の最初のサンプルが 1.0 (フルレベル)
   * で漏れる。結果「menu ボタンを最初に押した一瞬だけ爆音」になる。
   *
   * 対策: unlock を検知した瞬間に全 SFX キーを volume=0 で一度 play →
   * 即 stop。これで各キーの GainNode + Source graph が事前に確立され、
   * ユーザー操作で本当の playSfx が呼ばれた時には既に経路が warm になっている。
   */
  private warmupSfxGraph(): void {
    const sm = this.game.sound;
    const runWarmup = (): void => {
      for (const key of SFX_KEYS) {
        if (!this.game.cache.audio.exists(key)) continue;
        try {
          const snd = sm.add(key, { volume: 0 });
          snd.play();
          snd.stop();
          snd.destroy();
        } catch {
          // AudioContext が想定外の状態でも本番 SFX は後で普通に鳴るので無視。
        }
      }
    };
    // 既に unlock 済み (非 locking ブラウザ) なら即実行。
    // それ以外は Phaser が発火する "unlocked" イベントで 1 回だけ実行。
    // `locked` プロパティは WebAudio backend の型にしか存在しない。
    const locked =
      (sm as unknown as { locked?: boolean }).locked === true;
    if (!locked) {
      runWarmup();
    } else {
      sm.once("unlocked", runWarmup);
    }
  }

  static get(): AudioManager {
    if (!AudioManager.instance) {
      throw new Error(
        "[AudioManager] get() called before init(game); call AudioManager.init(game) in main.ts first.",
      );
    }
    return AudioManager.instance;
  }

  /**
   * Preload every registered .ogg through Phaser's loader on the given
   * scene. Safe to call multiple times: Phaser short-circuits keys that
   * are already cached. Resolves when the loader's "complete" fires.
   */
  loadAll(scene: Phaser.Scene): Promise<void> {
    return new Promise((resolve) => {
      let queued = 0;
      for (const key of Object.keys(SOUND_FILES) as AudioKey[]) {
        if (scene.cache.audio.exists(key)) continue;
        scene.load.audio(key, SOUND_FILES[key]);
        queued += 1;
      }
      if (queued === 0) {
        resolve();
        return;
      }
      scene.load.once(Phaser.Loader.Events.COMPLETE, () => resolve());
      scene.load.once(Phaser.Loader.Events.FILE_LOAD_ERROR, (file: unknown) => {
        // eslint-disable-next-line no-console
        console.warn("[AudioManager] asset failed to load:", file);
      });
      scene.load.start();
    });
  }

  playBgm(key: string): void {
    if (!this.isBgmKey(key)) {
      // eslint-disable-next-line no-console
      console.warn(`[AudioManager] unknown BGM key: ${key}`);
      return;
    }
    // Already playing this track? leave it alone.
    if (this.currentBgmKey === key && this.currentBgm?.isPlaying) {
      return;
    }
    this.stopBgm();
    const soundManager = this.game.sound;
    if (!soundManager.get(key) && !this.game.cache.audio.exists(key)) {
      // eslint-disable-next-line no-console
      console.warn(
        `[AudioManager] playBgm("${key}") called before asset was cached; ignoring.`,
      );
      return;
    }
    const volume = BGM_VOLUMES[key];
    const bgm = soundManager.add(key, { loop: true, volume });
    bgm.play();
    this.currentBgm = bgm;
    this.currentBgmKey = key;
  }

  stopBgm(): void {
    if (this.currentBgm) {
      try {
        this.currentBgm.stop();
        this.currentBgm.destroy();
      } catch {
        // Phaser can throw if the context was never unlocked; ignore.
      }
      this.currentBgm = null;
      this.currentBgmKey = null;
    }
  }

  playSfx(key: string, volume: number = DEFAULT_SFX_VOLUME): void {
    if (this.muted) return;
    if (!this.isSfxKey(key)) {
      // eslint-disable-next-line no-console
      console.warn(`[AudioManager] unknown SFX key: ${key}`);
      return;
    }
    if (!this.game.cache.audio.exists(key)) {
      // Asset not yet loaded — silently drop rather than spam the console.
      return;
    }
    this.game.sound.play(key, { volume });
  }

  /**
   * Flip the global mute. Mirrors the Python toggle_mute() semantics: all
   * channels go to 0 / 1. Phaser's sound manager has a single `mute` flag
   * that applies to every attached track, so we use that.
   */
  toggleMute(): boolean {
    this.muted = !this.muted;
    this.game.sound.mute = this.muted;
    this.refreshIndicator();
    return this.muted;
  }

  isMuted(): boolean {
    return this.muted;
  }

  private installGlobalMuteHotkey(): void {
    if (typeof window === "undefined") return;
    this.keydownHandler = (ev: KeyboardEvent): void => {
      if (ev.code === "KeyM") {
        this.toggleMute();
      }
    };
    window.addEventListener("keydown", this.keydownHandler);
  }

  /**
   * DOM overlay button showing current mute state. Positioned top-right
   * outside Phaser's canvas so it persists across all scene transitions
   * and is clickable without being affected by per-scene input routing.
   * Click toggles mute; label + color reflect the live state.
   */
  private installMuteIndicator(): void {
    if (typeof document === "undefined") return;
    const btn = document.createElement("button");
    btn.id = "mute-indicator";
    btn.type = "button";
    btn.style.cssText = [
      "position: fixed",
      "top: 12px",
      "right: 12px",
      "z-index: 9999",
      "padding: 6px 12px",
      "font-family: sans-serif",
      "font-size: 14px",
      "font-weight: bold",
      "border: 2px solid currentColor",
      "border-radius: 4px",
      "background: rgba(0, 0, 0, 0.6)",
      "cursor: pointer",
      "user-select: none",
    ].join("; ");
    btn.addEventListener("click", () => {
      this.toggleMute();
    });
    document.body.appendChild(btn);
    this.indicator = btn;
    this.refreshIndicator();
  }

  private refreshIndicator(): void {
    if (!this.indicator) return;
    if (this.muted) {
      this.indicator.textContent = "♪ 音声 OFF";
      this.indicator.style.color = "#ff6464";
    } else {
      this.indicator.textContent = "♪ 音声 ON";
      this.indicator.style.color = "#64ff96";
    }
  }

  private isSfxKey(key: string): key is SfxKey {
    return (SFX_KEYS as readonly string[]).includes(key);
  }

  private isBgmKey(key: string): key is BgmKey {
    return (BGM_KEYS as readonly string[]).includes(key);
  }
}
