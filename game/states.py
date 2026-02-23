import sys
import time  # time.timeを使用するため
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame
from game.constants import (
    ACTION_NAMES,
    BENI_RED,
    BLACK,
    CYAN,
    GRAY,
    NEGI_GREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOFU_WHITE,
    WHITE,
    YELLOW,
)

# Gameクラスを循環参照なしで型ヒントとして利用するためのインポート
if TYPE_CHECKING:
    from game.game import Game


class BaseState(ABC):
    """状態クラスの基底クラス"""

    def __init__(self, game: "Game"):
        self.game = game  # Gameオブジェクトへの参照
        # 前の状態を保持するための変数（オプション）
        self.previous_state = None

    def enter(self):
        """状態遷移でこの状態に入るときの処理。"""
        self.game.stop_title_bgm()

    def exit(self):
        """状態遷移でこの状態を出るときの処理。"""
        pass

    def needs_game_update(self):
        return False

    def uses_simple_ai_opponent(self):
        return False

    def is_auto_test_mode(self):
        return False

    def resets_health_on_zero(self):
        return False

    @abstractmethod
    def handle_input(self, event: pygame.event.Event):
        """イベント（キー入力など）を処理する"""
        # ESCキーの共通処理（サブクラスでオーバーライド可能）
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.handle_escape()

    # ESCキー処理のデフォルト実装
    def handle_escape(self):
        """ESCキーが押されたときの処理（デフォルト：何もしない）"""
        pass

    @abstractmethod
    def update(self):
        """状態のロジックを更新する"""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """画面を描画する"""
        pass


class TitleState(BaseState):
    """タイトル画面の状態"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        self.selected_item = 0
        self.menu_items = self.game.menu_items
        # フォントをキャッシュ
        self.title_font = pygame.font.SysFont(self.game.font_name, 72)
        self.menu_font = pygame.font.SysFont(self.game.font_name, 36)
        self.version_font = pygame.font.SysFont(self.game.font_name, 20)
        self.background_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.background_game = None
        self.background_test_start_time = 0.0

    def enter(self):
        self.game.play_title_bgm()
        if not self.game.enable_title_background:
            return
        from game.game import Game

        self.background_game = Game(
            self.game.screen, debug=False, enable_audio=False, enable_title_background=False
        )
        self.background_game.change_state(AutoTestState(self.background_game))
        self.background_test_start_time = time.time()

    def exit(self):
        self.background_game = None

    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                if "menu" in self.game.sounds:
                    self.game.sounds["menu"].play()
            elif event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
                if "menu" in self.game.sounds:
                    self.game.sounds["menu"].play()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_z:
                self.select_menu_item()
                if "special" in self.game.sounds:
                    self.game.sounds["special"].play()
            elif event.key == pygame.K_ESCAPE:
                # タイトル画面でESCを押すとゲームを終了
                pygame.quit()
                sys.exit()

    def select_menu_item(self):
        """選択したメニュー項目に応じた処理を実行"""
        # プレイヤーが存在する場合は、状態遷移前にキー状態をリセット
        if hasattr(self.game, "player1") and hasattr(self.game, "player2"):
            self.game.player1.key_states = {
                key: False for key in self.game.player1.key_states
            }
            self.game.player2.key_states = {
                key: False for key in self.game.player2.key_states
            }

        selected_option = self.menu_items[self.selected_item]
        if selected_option == "シングル対戦モード":
            self.game.change_state(SingleVersusGameState(self.game))
            self.game.reset_players()
        elif selected_option == "トレーニングモード":
            self.game.change_state(TrainingState(self.game))
            self.game.reset_players()
        elif selected_option == "自動テスト":
            self.game.change_state(AutoTestState(self.game))
            self.game.reset_players()
        elif selected_option == "操作説明":
            self.game.change_state(InstructionsState(self.game))
        elif selected_option == "オプション":
            self.game.change_state(OptionsState(self.game))
        elif selected_option == "終了":
            pygame.quit()
            sys.exit()

    def update(self):
        if not self.background_game:
            return
        current_time = time.time()
        if current_time - self.background_test_start_time > 10:
            from game.game import Game

            self.background_game = Game(
                self.game.screen, debug=False, enable_audio=False, enable_title_background=False
            )
            self.background_game.change_state(AutoTestState(self.background_game))
            self.background_test_start_time = current_time
        self.background_game.update()

    def draw(self, screen: pygame.Surface):
        """タイトル画面の描画処理"""
        screen.fill((0, 0, 0))
        if self.background_game:
            self.background_surface.fill((0, 0, 0, 0))
            self.background_game.draw_to_surface(self.background_surface)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.background_surface.blit(overlay, (0, 0))
            screen.blit(self.background_surface, (0, 0))

        # ゲームタイトル
        title_text = self.title_font.render("アクセラレーションオブ豆腐", True, CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_text, title_rect)

        # メニュー項目
        for i, item in enumerate(self.menu_items):
            if i == self.selected_item:
                text = self.menu_font.render(f"> {item} <", True, CYAN)
            else:
                text = self.menu_font.render(item, True, WHITE)

            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 300 + i * 50))
            screen.blit(text, rect)

        # バージョン表示
        version_text = self.version_font.render("Ver 0.1.0", True, (100, 100, 100))
        version_rect = version_text.get_rect(
            bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20)
        )
        screen.blit(version_text, version_rect)


class SingleVersusGameState(BaseState):
    """ゲームプレイ中の状態（シングル対戦モード）"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        # ゲーム開始時の初期化処理
        self.game.reset_players()
        # ゲーム開始時は弾をクリアしない（状態遷移時に保持するため）
        # self.game.projectiles.clear()
        # self.game.effects.clear()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def needs_game_update(self):
        return True

    def uses_simple_ai_opponent(self):
        return True

    def handle_input(self, event: pygame.event.Event):
        """ゲーム中の入力処理"""
        if event.type == pygame.KEYDOWN:
            key = event.key

            # ESCキーでポーズ画面に遷移
            if key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            # Game.keys_pressed を更新 (プレイヤー1のキーマッピングを使用)
            if key in self.game.key_mapping_p1:
                action = self.game.key_mapping_p1[key]
                if action in self.game.keys_pressed:
                    self.game.keys_pressed[action] = True

            # プレイヤー1の入力処理
            self.game.player1.handle_key_event(event)

            # プレイヤー2の入力処理
            self.game.player2.handle_key_event(event)
        elif event.type == pygame.KEYUP:
            key = event.key

            # Game.keys_pressed を更新 (プレイヤー1のキーマッピングを使用)
            if key in self.game.key_mapping_p1:
                action = self.game.key_mapping_p1[key]
                if action in self.game.keys_pressed:
                    self.game.keys_pressed[action] = False

            # プレイヤー1のキーリリース処理
            self.game.player1.handle_key_event(event)

            # プレイヤー2のキーリリース処理
            self.game.player2.handle_key_event(event)

    def handle_escape(self):
        """ゲーム中はESCキーでポーズ画面に遷移"""
        # キー状態をリセット
        self.game.player1.key_states = {
            key: False for key in self.game.player1.key_states
        }
        self.game.player2.key_states = {
            key: False for key in self.game.player2.key_states
        }
        self.game.change_state(PauseState(self.game, self))

    def update(self):
        """ゲーム状態の更新"""
        self.game.update_gameplay_elements(use_simple_ai=self.uses_simple_ai_opponent())

    def draw(self, screen: pygame.Surface):
        """ゲーム画面の描画"""
        # ゲーム背景の描画
        self.game.draw_background(screen)

        # プレイヤーの描画
        self.game.player1.draw(screen)
        self.game.player2.draw(screen)

        # プロジェクタイルの描画
        for projectile in self.game.projectiles:
            projectile.draw(screen)

        # HUDの描画
        self.draw_hud(screen)

    def draw_hud(self, screen: pygame.Surface):
        """HUD（ヘッドアップディスプレイ）を描画する"""
        # プレイヤー1の体力バー
        p1_health_text = f"P1: {self.game.player1.health}"
        p1_health_surf = self.font.render(p1_health_text, True, (255, 255, 255))
        screen.blit(p1_health_surf, (20, 20))

        # プレイヤー2の体力バー
        p2_health_text = f"P2: {self.game.player2.health}"
        p2_health_surf = self.font.render(p2_health_text, True, (255, 255, 255))
        screen.blit(p2_health_surf, (self.game.width - 120, 20))

        # ゲーム時間の表示（テスト用に簡易表示）
        game_time_text = "TIME: 00:00"
        time_surf = self.font.render(game_time_text, True, (255, 255, 255))
        screen.blit(time_surf, (self.game.width // 2 - time_surf.get_width() // 2, 20))


class TrainingState(SingleVersusGameState):  # SingleVersusGameStateを継承して基本的な動作は共通化
    """トレーニングモードの状態"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        # トレーニングモード固有の初期化

    def uses_simple_ai_opponent(self):
        return False

    def resets_health_on_zero(self):
        return True

    # SingleVersusGameStateを継承しているので、handle_escapeは同じ動作になる


class AutoTestState(SingleVersusGameState):
    """自動テストモードの状態"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        # 自動テストモード固有の初期化（タイマー、時間設定など）
        self.game.test_timer = 0
        self.test_font = pygame.font.SysFont(self.game.font_name, 24)
        # TODO: 選択されたテスト時間に基づいてdurationを設定するロジックをGameから移動

    # SingleVersusGameStateを継承しているので、handle_escapeは同じ動作になる

    def is_auto_test_mode(self):
        return True

    def uses_simple_ai_opponent(self):
        return False

    def update(self):
        self.game.update_auto_test_mode()

    def draw(self, screen: pygame.Surface):
        """自動テストモード用の描画処理"""
        if not isinstance(screen, pygame.Surface):
            self.draw_hud(screen)
            return
        # ゲーム背景の描画
        self.game.draw_background(screen)

        # プレイヤーの描画
        self.game.player1.draw(screen)
        self.game.player2.draw(screen)

        # プロジェクタイルの描画
        for projectile in self.game.projectiles:
            projectile.draw(screen)

        # HUDの描画
        self.draw_hud(screen)

        # テスト情報の表示
        test_info = f"自動テスト中: {self.game.test_timer // 60}秒経過"
        test_text = self.test_font.render(test_info, True, (255, 255, 0))
        screen.blit(test_text, (self.game.width // 2 - test_text.get_width() // 2, 50))


class InstructionsState(BaseState):
    """操作説明画面の状態"""

    def __init__(self, game: "Game", previous_state=None):
        super().__init__(game)
        self.previous_state = previous_state or TitleState(game)
        self.title_font = pygame.font.SysFont(self.game.font_name, 48)
        self.font = pygame.font.SysFont(self.game.font_name, 24)

    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            # どのキーでも前の状態に戻る
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
            else:
                action = None
                if event.key in self.game.key_mapping_p1:
                    action = self.game.key_mapping_p1[event.key]

                if action == "weapon_a":  # 決定キーでも戻る
                    self.handle_escape()

    def handle_escape(self):
        """ESCキーで前の状態に戻る"""
        if self.previous_state:
            self.game.change_state(self.previous_state)
        else:
            self.game.change_state(TitleState(self.game))

    def update(self):
        # 操作説明画面では特に更新処理はない
        pass

    def draw(self, screen: pygame.Surface):
        # 背景
        screen.fill((0, 0, 0))

        # タイトル
        title = self.title_font.render("操作説明", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        screen.blit(title, title_rect)

        # プレイヤー1の操作説明
        p1_title = self.font.render("プレイヤー1", True, (0, 255, 255))
        screen.blit(p1_title, (100, 120))

        y_offset = 155
        for action, description in [
            ("移動", "↑/↓/←/→: 上/下/左/右"),
            ("武器A（ビーム）", "Z or J"),
            ("武器B（バリスティック）", "X or K"),
            ("ハイパーモード", "Space or L"),
            ("ダッシュ", "左Shift or H"),
            ("スペシャル攻撃", "C"),
            ("シールド", "V"),
        ]:
            text = self.font.render(f"  {action}: {description}", True, (255, 255, 255))
            screen.blit(text, (120, y_offset))
            y_offset += 28

        # プレイヤー2の操作説明
        p2_title = self.font.render("プレイヤー2", True, (255, 100, 100))
        screen.blit(p2_title, (100, y_offset + 15))

        y_offset += 50
        for action, description in [
            ("移動", "W/A/S/D: 上/左/下/右"),
            ("武器A（ビーム）", "F"),
            ("武器B（バリスティック）", "G"),
            ("ハイパーモード", "R"),
            ("ダッシュ", "E"),
            ("スペシャル攻撃", "T"),
            ("シールド", "Y"),
        ]:
            text = self.font.render(f"  {action}: {description}", True, (255, 255, 255))
            screen.blit(text, (120, y_offset))
            y_offset += 28

        # 共通操作
        common_title = self.font.render("共通", True, (200, 200, 100))
        screen.blit(common_title, (100, y_offset + 15))
        y_offset += 50
        for text_str in ["ESC: ポーズ/戻る", "Enter or Z: 決定"]:
            text = self.font.render(f"  {text_str}", True, (200, 200, 200))
            screen.blit(text, (120, y_offset))
            y_offset += 28

        # 戻る方法
        back_text = self.font.render("戻る: ESCキー または 決定ボタン", True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(back_text, back_rect)


class OptionsState(BaseState):
    """オプション画面の状態"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        self.selected_item = 0
        self.menu_items = ["プレイヤー1設定", "プレイヤー2設定", "サウンド設定", "戻る"]
        self.previous_state = TitleState(game)  # デフォルトの前の状態はタイトル
        self.title_font = pygame.font.SysFont(self.game.font_name, 48)
        self.menu_font = pygame.font.SysFont(self.game.font_name, 36)

    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            action = None
            if event.key in self.game.key_mapping_p1:
                action = self.game.key_mapping_p1[event.key]

            if action == "up":
                if "menu" in self.game.sounds:
                    self.game.sounds["menu"].play()
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif action == "down":
                if "menu" in self.game.sounds:
                    self.game.sounds["menu"].play()
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif action == "weapon_a" or event.key == pygame.K_z:  # 決定（K_zキーも直接チェック）
                if "special" in self.game.sounds:
                    self.game.sounds["special"].play()
                selected_option = self.menu_items[self.selected_item]
                if selected_option == "プレイヤー1設定":
                    self.game.key_config_player = 1
                    self.game.key_config_selected_item = 0
                    self.game.waiting_for_key_input = False
                    self.game.change_state(
                        KeyConfigState(self.game, self)
                    )  # 自身を前の状態として渡す
                elif selected_option == "プレイヤー2設定":
                    self.game.key_config_player = 2
                    self.game.key_config_selected_item = 0
                    self.game.waiting_for_key_input = False
                    self.game.change_state(
                        KeyConfigState(self.game, self)
                    )  # 自身を前の状態として渡す
                elif selected_option == "サウンド設定":
                    # TODO: サウンド設定画面を実装
                    pass
                elif selected_option == "戻る":
                    self.handle_escape()

    def handle_escape(self):
        """ESCキーでタイトル画面に戻る"""
        if self.previous_state:
            self.game.change_state(self.previous_state)
        else:
            self.game.change_state(TitleState(self.game))

    def update(self):
        # オプション画面では特に更新処理はない
        pass

    def draw(self, screen: pygame.Surface):
        # 背景
        screen.fill((0, 0, 0))

        # タイトル
        title_text = self.title_font.render("オプション", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))

        # メニュー項目
        for i, item in enumerate(self.menu_items):
            color = (0, 255, 255) if i == self.selected_item else (255, 255, 255)
            text = self.menu_font.render(item, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 60))
            screen.blit(text, rect)


class KeyConfigState(BaseState):
    """キーコンフィグ画面の状態"""

    def __init__(self, game: "Game", previous_state=None):
        super().__init__(game)
        # Gameオブジェクトからキーコンフィグ関連の変数を初期化
        self.player = self.game.key_config_player
        self.selected_item = self.game.key_config_selected_item
        self.waiting_for_input = self.game.waiting_for_key_input
        self.config_items = self.game.key_config_items
        self.previous_state = previous_state or OptionsState(game)
        self.title_font = pygame.font.SysFont(self.game.font_name, 48)
        self.player_font = pygame.font.SysFont(self.game.font_name, 36)
        self.menu_font = pygame.font.SysFont(self.game.font_name, 28)
        self.inst_font = pygame.font.SysFont(self.game.font_name, 20)

    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            if self.waiting_for_input:
                # キー入力待ちの処理
                self.game.assign_key(event.key)  # Gameのメソッド呼び出し (仮)
                self.waiting_for_input = False
                # 次の項目へ自動で移動
                self.selected_item = (self.selected_item + 1) % len(self.config_items)
                # Game側の状態も更新しておく
                self.game.waiting_for_key_input = self.waiting_for_input
                self.game.key_config_selected_item = self.selected_item
            else:
                action = None
                if event.key in self.game.key_mapping_p1:  # メニュー操作はP1キー
                    action = self.game.key_mapping_p1[event.key]

                if action == "up":
                    self.selected_item = (self.selected_item - 1) % len(
                        self.config_items
                    )
                elif action == "down":
                    self.selected_item = (self.selected_item + 1) % len(
                        self.config_items
                    )
                elif action == "left" or action == "right":
                    self.player = 1 if self.player == 2 else 2
                    # Game側の状態も更新
                    self.game.key_config_player = self.player
                elif action == "weapon_a":  # 決定 -> キー入力待ちへ
                    self.waiting_for_input = True
                elif action == "weapon_b":  # 戻る
                    self.handle_escape()
                elif event.key == pygame.K_r:  # リセット
                    self.game.reset_key_config()  # リセット処理を呼び出す

                # Game側の状態も更新しておく (waiting以外)
                self.game.key_config_selected_item = self.selected_item
                self.game.waiting_for_key_input = self.waiting_for_input

    def handle_escape(self):
        """ESCキーで設定を保存して前の画面に戻る"""
        self.game.save_key_config()  # 保存処理を呼び出す
        if self.previous_state:
            self.game.change_state(self.previous_state)
        else:
            self.game.change_state(OptionsState(self.game))

    def update(self):
        pass

    def draw(self, screen: pygame.Surface):
        """キー設定画面の描画処理"""
        # 背景
        screen.fill((0, 0, 0))

        # タイトル
        title_text = self.title_font.render("キー設定", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

        # プレイヤー選択表示
        player_text = f"プレイヤー {self.player}"
        player_label = self.player_font.render(player_text, True, WHITE)
        screen.blit(
            player_label, (SCREEN_WIDTH // 2 - player_label.get_width() // 2, 120)
        )

        # 設定項目の表示
        y_pos = 180

        for i, action in enumerate(self.config_items):
            action_color = YELLOW if i == self.selected_item else WHITE
            action_text = f"{ACTION_NAMES[action]}: "
            action_label = self.menu_font.render(action_text, True, action_color)

            # 現在のキー名を取得 (修正)
            key_mapping = (
                self.game.key_mapping_p1
                if self.player == 1
                else self.game.key_mapping_p2
            )
            key_id = None

            # アクションからキーIDを逆引き
            for k, v in key_mapping.items():
                if v == action:
                    key_id = k
                    break

            # キーIDからキー名を取得
            if key_id is None:
                key_name = "未設定"
            else:
                try:
                    key_name = pygame.key.name(key_id).upper()
                except:
                    key_name = f"キー({key_id})"

            if i == self.selected_item and self.waiting_for_input:
                key_text = "キーを押してください..."
            else:
                key_text = key_name

            key_label = self.menu_font.render(key_text, True, action_color)

            # 描画
            screen.blit(action_label, (SCREEN_WIDTH // 3, y_pos))
            screen.blit(
                key_label, (SCREEN_WIDTH // 3 + action_label.get_width() + 10, y_pos)
            )
            y_pos += 40

        # 操作説明
        instructions = ["↑/↓: 項目選択", "ENTER: キー設定変更", "TAB: プレイヤー切替", "ESC: 戻る"]

        y_pos = 480
        for instruction in instructions:
            inst_label = self.inst_font.render(instruction, True, GRAY)
            screen.blit(
                inst_label, (SCREEN_WIDTH // 2 - inst_label.get_width() // 2, y_pos)
            )
            y_pos += 30


class PauseState(BaseState):
    """ポーズ画面の状態"""

    def __init__(self, game, prev_state=None):
        super().__init__(game)
        # 日本語フォントを使用するように変更
        self.menu_font = pygame.font.SysFont(self.game.font_name, 36)
        self.title_font = pygame.font.SysFont(self.game.font_name, 48)
        self.selected_item = 0
        self.menu_items = ["ゲームに戻る", "操作説明", "タイトルに戻る", "ゲーム終了"]
        self.menu_positions = []
        self.previous_state = prev_state or TitleState(game)
        self.setup_menu_positions()

    # Setup positions for each menu item
    def setup_menu_positions(self):
        screen_center_x = self.game.width // 2
        start_y = self.game.height // 2
        spacing = 50

        self.menu_positions = []
        for i in range(len(self.menu_items)):
            self.menu_positions.append((screen_center_x, start_y + i * spacing))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            # ESCキーでゲームに戻る
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            # Menu navigation
            if event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            # Selection
            elif event.key == pygame.K_RETURN or event.key == pygame.K_z:
                if self.selected_item == 0:  # Resume game
                    self.handle_escape()
                elif self.selected_item == 1:  # Instructions
                    self.game.change_state(InstructionsState(self.game, self))
                elif self.selected_item == 2:  # Back to title
                    self.game.change_state(TitleState(self.game))
                elif self.selected_item == 3:  # Exit game
                    pygame.quit()
                    sys.exit()

    def handle_escape(self):
        """ESCキーで前の状態（ゲーム画面）に戻る"""
        # キー状態をリセット
        if hasattr(self.game, "player1") and hasattr(self.game, "player2"):
            self.game.player1.key_states = {
                key: False for key in self.game.player1.key_states
            }
            self.game.player2.key_states = {
                key: False for key in self.game.player2.key_states
            }

        if self.previous_state:
            self.game.change_state(self.previous_state)
        else:
            self.game.change_state(TitleState(self.game))

    def update(self):
        """ポーズ画面の更新処理"""
        pass

    def draw(self, screen):
        """ポーズ画面の描画処理"""
        # 背景を暗く表示
        s = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))  # 半透明の黒
        screen.blit(s, (0, 0))

        # メニューの表示
        for i, item in enumerate(self.menu_items):
            color = (255, 255, 0) if i == self.selected_item else (255, 255, 255)
            text = self.menu_font.render(item, True, color)
            x, y = self.menu_positions[i]
            screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))


class SplashScreenState(BaseState):
    """スプラッシュスクリーン状態 - ゲーム起動時に表示される"""

    def __init__(self, game: "Game"):
        super().__init__(game)
        self.display_duration = 2500  # 表示時間 (ミリ秒)
        self.fade_duration = 400  # フェード時間 (ミリ秒)
        self.start_time = pygame.time.get_ticks()
        self.force_transition_after = 2500
        self.transition_started = False

        self.font_large = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 24)

        self.alpha = 0
        self.fade_state = 0  # 0: フェードイン, 1: 表示中, 2: フェードアウト, 3: 完了
        self.logo_text = "ACCELERATION OF TOFU"
        self.subtitle_text = "Enjoy the Game"
        self.credit_text = "Presented by Tofu Dev Team"

    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            self.skip_to_title()

    def skip_to_title(self):
        """即座にタイトル画面に遷移"""
        if self.transition_started:
            return
        self.transition_started = True
        self.game.change_state(TitleState(self.game))

    def update(self):
        """スプラッシュ画面の更新処理"""
        if self.transition_started:
            return

        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time

        # 強制遷移チェック
        if elapsed_time >= self.force_transition_after:
            self.skip_to_title()
            return

        # フェードイン
        if self.fade_state == 0:
            if elapsed_time < self.fade_duration:
                self.alpha = int(255 * (elapsed_time / self.fade_duration))
            else:
                self.alpha = 255
                self.fade_state = 1

        # 表示中
        elif self.fade_state == 1:
            if elapsed_time > self.display_duration - self.fade_duration:
                self.fade_state = 2

        # フェードアウト
        elif self.fade_state == 2:
            fade_progress = (
                elapsed_time - (self.display_duration - self.fade_duration)
            ) / self.fade_duration
            self.alpha = max(0, int(255 * (1 - fade_progress)))
            if self.alpha <= 0:
                self.fade_state = 3
                self.skip_to_title()

    def draw(self, screen: pygame.Surface):
        """スプラッシュ画面の描画"""
        screen.fill((0, 0, 50))

        # ロゴテキスト
        logo_render = self.font_large.render(self.logo_text, True, (255, 255, 255))
        logo_surface = pygame.Surface(logo_render.get_size(), pygame.SRCALPHA)
        logo_surface.blit(logo_render, (0, 0))
        logo_surface.set_alpha(self.alpha)

        # サブタイトル
        subtitle_render = self.font_small.render(self.subtitle_text, True, (0, 255, 255))
        subtitle_surface = pygame.Surface(subtitle_render.get_size(), pygame.SRCALPHA)
        subtitle_surface.blit(subtitle_render, (0, 0))
        subtitle_surface.set_alpha(self.alpha)

        # クレジット
        credit_render = self.font_small.render(self.credit_text, True, (200, 200, 200))
        credit_surface = pygame.Surface(credit_render.get_size(), pygame.SRCALPHA)
        credit_surface.blit(credit_render, (0, 0))
        credit_surface.set_alpha(self.alpha)

        # 画面中央に配置
        screen.blit(logo_surface, (SCREEN_WIDTH // 2 - logo_render.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(subtitle_surface, (SCREEN_WIDTH // 2 - subtitle_render.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(credit_surface, (SCREEN_WIDTH // 2 - credit_render.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
