import Phaser from "phaser";
import {
  ARENA_RADIUS,
  ARENA_CENTER_X,
  ARENA_CENTER_Y,
  ARENA_WARNING_RADIUS,
} from "../config/constants";
import { Player } from "../entities/Player";
import { Projectile } from "../entities/Projectile";
import { Arena } from "../entities/Arena";
import { autoTestAiControl, resetAi } from "../systems/SimpleAI";
import { applyStickyTether, resolvePlayerCollision } from "../systems/Combat";
// D3: audio wiring — stop title BGM when the auto-test demo starts.
import { AudioManager } from "../systems/Audio";

/**
 * AutoTestScene
 *
 * CPU-vs-CPU demo scene. Ports the essential shape of
 * game/states.py::AutoTestState for the web build.
 *
 * Responsibilities:
 *   - instantiate Arena (visuals + geometry helpers)
 *   - spawn two Players on opposite sides of the arena center
 *   - drive both Players with autoTestAiControl() every frame, feeding
 *     it the live projectile list so the AI can dodge
 *   - own the projectile list; advance + collide + prune each tick
 *   - every 10 real-time seconds: reset() both Players, clear projectiles,
 *     and drop AI state so timers don't leak across resets
 *   - ESC -> TitleScene
 */
export class AutoTestScene extends Phaser.Scene {
  private arena!: Arena;
  private player1!: Player;
  private player2!: Player;
  private projectiles: Projectile[] = [];
  private frameCounter = 0;
  private lastResetMs = 0;
  private hudText!: Phaser.GameObjects.Text;

  constructor() {
    super({ key: "AutoTestScene" });
  }

  create(): void {
    // D3: audio wiring — kill any currently-playing BGM (e.g. title BGM).
    AudioManager.get().stopBgm();

    this.arena = new Arena(
      this,
      ARENA_CENTER_X,
      ARENA_CENTER_Y,
      ARENA_RADIUS,
      ARENA_WARNING_RADIUS
    );
    this.arena.create();

    this.player1 = new Player(
      this,
      ARENA_CENTER_X - 100,
      ARENA_CENTER_Y,
      true
    );
    this.player2 = new Player(
      this,
      ARENA_CENTER_X + 100,
      ARENA_CENTER_Y,
      false
    );

    // fresh AI state for both — matters if the scene is re-entered.
    resetAi(this.player1);
    resetAi(this.player2);

    this.hudText = this.add.text(10, 10, "", {
      fontFamily: "MPLUS1p",
      fontSize: "16px",
      color: "#ffff00",
    });

    this.lastResetMs = this.time.now;
    this.frameCounter = 0;

    const kb = this.input.keyboard;
    if (kb) {
      kb.on("keydown-ESC", () => {
        if (this.scene.isActive("PauseButtonOverlay")) {
          this.scene.stop("PauseButtonOverlay");
        }
        this.scene.start("TitleScene");
      });
    }

    // Floating PAUSE button (touch-friendly).  PauseScene's
    // PARENT_SCENE_KEY is hardcoded to SingleVersusScene so its
    // returnToTitle path already handles AutoTestScene cleanup via the
    // explicit isActive("AutoTestScene") branch we added.
    this.scene.launch("PauseButtonOverlay", { parentKey: "AutoTestScene" });

    // paranoia cleanup: if the scene is stopped mid-game, drop projectile
    // sprites so Phaser doesn't leak them.
    this.events.on(Phaser.Scenes.Events.SHUTDOWN, this.cleanup, this);
  }

  override update(_time: number, delta: number): void {
    // --- 60fps tick-normalized dt ---
    const dtScale = delta / (1000 / 60);

    // --- AI drives both players (now projectile-aware) ---
    this.player1.keyStates = autoTestAiControl(
      this.player1,
      this.player2,
      this.arena,
      this.projectiles
    );
    this.player2.keyStates = autoTestAiControl(
      this.player2,
      this.player1,
      this.arena,
      this.projectiles
    );

    const spawn = (p: Projectile): void => {
      this.projectiles.push(p);
    };

    this.player1.update(
      dtScale,
      ARENA_CENTER_X,
      ARENA_CENTER_Y,
      ARENA_RADIUS,
      this.player2,
      spawn,
      this
    );
    this.player2.update(
      dtScale,
      ARENA_CENTER_X,
      ARENA_CENTER_Y,
      ARENA_RADIUS,
      this.player1,
      spawn,
      this
    );

    // --- fermented sticky tether (Python update_gameplay_elements parity) ---
    if (this.player1.isFermented)
      applyStickyTether(this.player1, this.player2);
    if (this.player2.isFermented)
      applyStickyTether(this.player2, this.player1);

    // --- player-player collision push-back (water_level weighted) ---
    resolvePlayerCollision(this.player1, this.player2);

    // --- projectiles ---
    for (const p of this.projectiles) {
      p.update(dtScale, ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS);
      if (p.isExpired) continue;
      if (p.collidesWith(this.player1)) {
        this.player1.takeDamage(p.damage);
        p.isExpired = true;
      } else if (p.collidesWith(this.player2)) {
        this.player2.takeDamage(p.damage);
        p.isExpired = true;
      }
    }

    // prune expired
    const survivors: Projectile[] = [];
    for (const p of this.projectiles) {
      if (p.isExpired) {
        p.destroy();
      } else {
        survivors.push(p);
      }
    }
    this.projectiles = survivors;

    // --- arena warning-ring pulse ---
    this.arena.update();
    this.arena.render();

    // --- distance-based camera zoom (mirrors Python draw_to_surface
    // in legacy/pygbag/game/game.py:431-495). Near → 1.5x zoom,
    // far → 1.0x zoom, linear in between. Center on player midpoint. ---
    this.updateCameraZoom();

    // --- periodic reset every 10 real-time seconds ---
    if (this.time.now - this.lastResetMs > 10_000) {
      this.resetDemo();
      this.lastResetMs = this.time.now;
    }

    // --- HUD ---
    const secSince = Math.floor((this.time.now - this.lastResetMs) / 1000);
    this.hudText.setText(
      `AUTO-TEST  t=${secSince}s  P1 hp=${Math.round(
        this.player1.health
      )}  P2 hp=${Math.round(this.player2.health)}  bullets=${
        this.projectiles.length
      }  [ESC]`
    );

    this.frameCounter += 1;
  }

  private updateCameraZoom(): void {
    const minDistance = 150;
    const maxDistance = 400;
    const maxZoom = 1.5;
    const minZoom = 1.0;

    const distance = Math.hypot(
      this.player1.x - this.player2.x,
      this.player1.y - this.player2.y
    );

    let zoom: number;
    if (distance <= minDistance) {
      zoom = maxZoom;
    } else if (distance >= maxDistance) {
      zoom = minZoom;
    } else {
      zoom =
        maxZoom -
        ((distance - minDistance) / (maxDistance - minDistance)) *
          (maxZoom - minZoom);
    }

    const midX = (this.player1.x + this.player2.x) / 2;
    const midY = (this.player1.y + this.player2.y) / 2;

    this.cameras.main.setZoom(zoom);
    this.cameras.main.centerOn(midX, midY);
  }

  private resetDemo(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
    this.player1.reset();
    this.player2.reset();
    resetAi(this.player1);
    resetAi(this.player2);
  }

  private cleanup(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
  }
}
