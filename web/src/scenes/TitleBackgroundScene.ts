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

/**
 * TitleBackgroundScene
 *
 * Python の TitleState は内部で別インスタンスの Game を抱え、裏側で
 * AutoTestState を回して試合映像をそのままタイトル背景にしていた
 * (game/states.py:106 前後)。Phaser 上ではそれを 1 つの Scene として
 * 分離する。AutoTestScene との違いは:
 *   - ESC ハンドラなし (タイトル入力は TitleScene 側で管理)
 *   - HUD テキストなし (見た目を汚さない)
 *   - BGM 制御なし
 *   - 10 秒リセットだけ継承
 * TitleScene.create() で scene.launch("TitleBackgroundScene") し、
 * メニュー確定時および TitleScene の SHUTDOWN で stop する。
 */
export class TitleBackgroundScene extends Phaser.Scene {
  private arena!: Arena;
  private player1!: Player;
  private player2!: Player;
  private projectiles: Projectile[] = [];
  private lastResetMs = 0;

  constructor() {
    super({ key: "TitleBackgroundScene" });
  }

  create(): void {
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

    resetAi(this.player1);
    resetAi(this.player2);

    this.lastResetMs = this.time.now;
    this.events.on(Phaser.Scenes.Events.SHUTDOWN, this.cleanup, this);
  }

  override update(_time: number, delta: number): void {
    const dtScale = delta / (1000 / 60);

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

    const survivors: Projectile[] = [];
    for (const p of this.projectiles) {
      if (p.isExpired) p.destroy();
      else survivors.push(p);
    }
    this.projectiles = survivors;

    this.arena.update();
    this.arena.render();

    // --- distance-based camera zoom (mirrors Python draw_to_surface
    // in legacy/pygbag/game/game.py:431-495). Near → 1.5x zoom,
    // far → 1.0x zoom, linear in between. Center on player midpoint. ---
    this.updateCameraZoom();

    if (this.time.now - this.lastResetMs > 10_000) {
      for (const p of this.projectiles) p.destroy();
      this.projectiles = [];
      this.player1.reset();
      this.player2.reset();
      resetAi(this.player1);
      resetAi(this.player2);
      this.lastResetMs = this.time.now;
    }
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

  private cleanup(): void {
    for (const p of this.projectiles) p.destroy();
    this.projectiles = [];
  }
}
