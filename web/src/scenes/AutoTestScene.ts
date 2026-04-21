import Phaser from "phaser";
import {
  ARENA_RADIUS,
  ARENA_CENTER_X,
  ARENA_CENTER_Y,
} from "../config/constants";
import { WHITE, CYAN } from "../config/colors";
import { Player } from "../entities/Player";
import { Projectile } from "../entities/Projectile";
import { simpleAiControl } from "../systems/SimpleAI";

/**
 * AutoTestScene
 *
 * CPU-vs-CPU demo scene. Ports the essential shape of
 * game/states.py::AutoTestState for the web build.
 *
 * Responsibilities:
 *   - spawn two Players on opposite sides of the arena center
 *   - drive both Players with simpleAiControl() every frame
 *   - own the projectile list; advance + collide + prune each tick
 *   - every 10 real-time seconds: reset() both Players and clear
 *     projectiles (does NOT restart the scene — same as Python's
 *     "reset_auto_test_mode" call inside Game.update_auto_test_mode)
 *   - ESC -> TitleScene
 */
export class AutoTestScene extends Phaser.Scene {
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
    // arena ring
    const g = this.add.graphics();
    g.lineStyle(2, WHITE, 0.6);
    g.strokeCircle(ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS);
    // faint inner warning ring for visual reference
    g.lineStyle(1, CYAN, 0.25);
    g.strokeCircle(ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS - 20);

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
        this.scene.start("TitleScene");
      });
    }

    // paranoia cleanup: if the scene is stopped mid-game, drop projectile
    // sprites so Phaser doesn't leak them.
    this.events.on(Phaser.Scenes.Events.SHUTDOWN, this.cleanup, this);
  }

  override update(_time: number, delta: number): void {
    // --- 60fps tick-normalized dt ---
    const dtScale = delta / (1000 / 60);

    // --- AI drives both players ---
    this.player1.keyStates = simpleAiControl(
      this.player1,
      this.player2,
      this.frameCounter
    );
    this.player2.keyStates = simpleAiControl(
      this.player2,
      this.player1,
      this.frameCounter + 30 // phase-offset so they don't fire in lock-step
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

  private resetDemo(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
    this.player1.reset();
    this.player2.reset();
  }

  private cleanup(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
  }
}
