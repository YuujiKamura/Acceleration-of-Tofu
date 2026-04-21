import Phaser from "phaser";
import {
  ARENA_CENTER_X,
  ARENA_CENTER_Y,
  ARENA_RADIUS,
  DEFAULT_KEY_MAPPING_P1,
  DEFAULT_KEY_MAPPING_P2,
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  ARENA_WARNING_RADIUS,
} from "../config/constants";
import { Player, type KeyStates } from "../entities/Player";
import { Projectile } from "../entities/Projectile";
import { Arena } from "../entities/Arena";
import { mapKeyboardToActions } from "../systems/Input";
import { handleCollisions } from "../systems/Combat";

/**
 * SingleVersusScene
 *
 * Player-vs-player arena scene. Both sides read their own keyboard
 * mapping (DEFAULT_KEY_MAPPING_P1 / _P2). HUD is run as an overlay
 * scene (HUDScene) so render layering is free. ESC pauses.
 *
 * Ports the essentials of game/states.py::SingleVersusGameState. For
 * now we use inline collision (same shape as AutoTestScene) because
 * the shared Combat.ts system is owned by a parallel agent and not yet
 * on disk. When that lands, replace the collision block with a single
 * handleCollisions(players, projectiles) call.
 */
const ROUND_END_MS = 3_000;

export class SingleVersusScene extends Phaser.Scene {
  private arena!: Arena;
  private player1!: Player;
  private player2!: Player;
  private projectiles: Projectile[] = [];
  private readP1!: () => KeyStates;
  private readP2!: () => KeyStates;

  private roundOver = false;
  private roundEndAt = 0;
  private resultText: Phaser.GameObjects.Text | null = null;

  constructor() {
    super({ key: "SingleVersusScene" });
  }

  create(): void {
    // arena: 移植済み Arena クラスで Python arena.py の見た目を再現。
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

    this.readP1 = mapKeyboardToActions(this, DEFAULT_KEY_MAPPING_P1);
    this.readP2 = mapKeyboardToActions(this, DEFAULT_KEY_MAPPING_P2);

    this.roundOver = false;
    this.roundEndAt = 0;
    this.resultText = null;
    this.projectiles = [];

    // Launch HUD as overlay
    this.scene.launch("HUDScene", {
      player1: this.player1,
      player2: this.player2,
    });

    const kb = this.input.keyboard;
    if (kb) {
      kb.on("keydown-ESC", () => {
        if (this.roundOver) return;
        this.scene.pause();
        this.scene.launch("PauseScene");
      });
    }

    this.events.on(Phaser.Scenes.Events.SHUTDOWN, this.cleanup, this);
  }

  override update(_time: number, delta: number): void {
    const dtScale = delta / (1000 / 60);

    if (this.roundOver) {
      if (this.time.now >= this.roundEndAt) {
        this.scene.stop("HUDScene");
        this.scene.start("TitleScene");
      }
      return;
    }

    // --- input ---
    this.player1.keyStates = this.readP1();
    this.player2.keyStates = this.readP2();

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

    // --- projectiles + collisions (heat/hyper damage multipliers live in Combat.ts) ---
    for (const p of this.projectiles) {
      p.update(dtScale, ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS);
    }
    handleCollisions([this.player1, this.player2], this.projectiles, []);

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

    // --- round end ---
    if (this.player1.health <= 0 || this.player2.health <= 0) {
      this.endRound(this.player1.health <= 0 ? 2 : 1);
    }
  }

  private endRound(winner: 1 | 2): void {
    if (this.roundOver) return;
    this.roundOver = true;
    this.roundEndAt = this.time.now + ROUND_END_MS;
    this.resultText = this.add
      .text(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, `P${winner} WIN`, {
        fontFamily: "MPLUS1p",
        fontSize: "72px",
        color: "#ffff00",
      })
      .setOrigin(0.5, 0.5);
  }

  private cleanup(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
    if (this.resultText) {
      this.resultText.destroy();
      this.resultText = null;
    }
  }
}
