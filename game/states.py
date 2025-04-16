import pygame
import sys
import time  # time.timeを使用するため
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GRAY, NEGI_GREEN, BENI_RED, TOFU_WHITE, YELLOW, ACTION_NAMES, CYAN

# Gameクラスを循環参照なしで型ヒントとして利用するためのインポート
if TYPE_CHECKING:
    from game.game import Game

class BaseState(ABC):
    """状態クラスの基底クラス"""
    def __init__(self, game: 'Game'):
        self.game = game # Gameオブジェクトへの参照
        # 前の状態を保持するための変数（オプション）
        self.previous_state = None

    @abstractmethod
    def handle_input(self, event: pygame.event.Event):
        """イベント（キー入力など）を処理する"""
        # ESCキーの共通処理（サブクラスでオーバーライド可能）
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.handle_escape()
    
    # ESCキー処理のデフォルト実装
    def handle_escape(self):
        """ESCキーが押されたときの処理（デフォルト：何もしない）"""
        print("BaseState.handle_escape()が呼ばれました。サブクラスでオーバーライドしてください。")
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
    def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: TitleState") # デバッグ用
        # ここにタイトル画面固有の初期化処理を追加
        # 例: メニュー項目の選択状態など
        self.selected_item = 0
        self.menu_items = self.game.menu_items # Gameからメニュー項目を取得
        
    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                if "menu" in self.game.sounds: self.game.sounds["menu"].play()
            elif event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
                if "menu" in self.game.sounds: self.game.sounds["menu"].play()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_z:
                self.select_menu_item()
                if "special" in self.game.sounds: self.game.sounds["special"].play()
            elif event.key == pygame.K_ESCAPE:
                # タイトル画面でESCを押すとゲームを終了
                pygame.quit()
                sys.exit()
    
    def select_menu_item(self):
        """選択したメニュー項目に応じた処理を実行"""
        # プレイヤーが存在する場合は、状態遷移前にキー状態をリセット
        if hasattr(self.game, 'player1') and hasattr(self.game, 'player2'):
            self.game.player1.key_states = {key: False for key in self.game.player1.key_states}
            self.game.player2.key_states = {key: False for key in self.game.player2.key_states}
            
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
        # タイトル画面固有の更新処理 (例: アニメーションなど)
        pass

    def draw(self, screen: pygame.Surface):
        """タイトル画面の描画処理"""
        # 背景色は描画しない（背景アドバタイズを表示するため）
        # screen.fill((0, 0, 0))  
        
        # ゲームタイトル
        title_font = pygame.font.SysFont(self.game.font_name, 72)
        title_text = title_font.render("アクセラレーションオブ豆腐", True, CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(title_text, title_rect)
        
        # メニュー項目
        menu_font = pygame.font.SysFont(self.game.font_name, 36)
        
        for i, item in enumerate(self.menu_items):
            if i == self.selected_item:
                # 選択中の項目は色を変える
                text = menu_font.render(f"> {item} <", True, CYAN)
            else:
                text = menu_font.render(item, True, WHITE)
            
            rect = text.get_rect(center=(SCREEN_WIDTH//2, 300 + i * 50))
            screen.blit(text, rect)
            
        # バージョン表示
        version_font = pygame.font.SysFont(self.game.font_name, 20)
        version_text = version_font.render("Ver 0.1.0", True, (100, 100, 100))
        version_rect = version_text.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        screen.blit(version_text, version_rect)

class SingleVersusGameState(BaseState):
    """ゲームプレイ中の状態（シングル対戦モード）"""
    def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: SingleVersusGameState")
        # ゲーム開始時の初期化処理
        self.game.reset_players()
        # ゲーム開始時は弾をクリアしない（状態遷移時に保持するため）
        # self.game.projectiles.clear()
        # self.game.effects.clear()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

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
        self.game.player1.key_states = {key: False for key in self.game.player1.key_states}
        self.game.player2.key_states = {key: False for key in self.game.player2.key_states}
        self.game.change_state(PauseState(self.game, self))

    def update(self):
        """ゲーム状態の更新"""
        # プレイヤーの更新 (arena と opponent のみを渡す)
        self.game.player1.update(self.game.arena, self.game.player2)
        self.game.player2.update(self.game.arena, self.game.player1)
        
        # 衝突判定
        self.game.handle_collisions()
        
        # プロジェクタイルの更新
        for projectile in self.game.projectiles:
            projectile.update()
            
        # 終了した弾を削除
        self.game.projectiles = [p for p in self.game.projectiles if not p.is_expired]

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

class TrainingState(SingleVersusGameState): # SingleVersusGameStateを継承して基本的な動作は共通化
    """トレーニングモードの状態"""
    def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: TrainingState")
        # トレーニングモード固有の初期化

    # SingleVersusGameStateを継承しているので、handle_escapeは同じ動作になる

class AutoTestState(SingleVersusGameState):
     """自動テストモードの状態"""
     def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: AutoTestState")
        # 自動テストモード固有の初期化（タイマー、時間設定など）
        self.game.test_timer = 0
        # TODO: 選択されたテスト時間に基づいてdurationを設定するロジックをGameから移動

     # SingleVersusGameStateを継承しているので、handle_escapeは同じ動作になる

     def draw(self, screen: pygame.Surface):
        """自動テストモード用の描画処理"""
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
        test_font = pygame.font.SysFont(self.game.font_name, 24)
        test_info = f"自動テスト中: {self.game.test_timer // 60}秒経過"
        test_text = test_font.render(test_info, True, (255, 255, 0))
        screen.blit(test_text, (self.game.width // 2 - test_text.get_width() // 2, 50))

class InstructionsState(BaseState):
    """操作説明画面の状態"""
    def __init__(self, game: 'Game', previous_state=None):
        super().__init__(game)
        print("State changed to: InstructionsState")
        self.previous_state = previous_state or TitleState(game)
        
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
        title_font = pygame.font.SysFont(self.game.font_name, 48)
        title = title_font.render("操作説明", True, (255, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title, title_rect)
        
        # 操作説明の内容
        font = pygame.font.SysFont(self.game.font_name, 24)
        
        # プレイヤー1の操作説明
        p1_title = font.render("プレイヤー1", True, (0, 255, 255))
        screen.blit(p1_title, (100, 150))
        
        # キー説明
        y_offset = 190
        for action, description in [
            ("移動", "W/A/S/D: 上/左/下/右"),
            ("武器A", "J: 豆腐投げ"),
            ("武器B", "K: 盾"),
            ("特殊", "L: ハイパーモード/ダッシュ")
        ]:
            text = font.render(f"{action}: {description}", True, (255, 255, 255))
            screen.blit(text, (120, y_offset))
            y_offset += 30
        
        # プレイヤー2の操作説明
        p2_title = font.render("プレイヤー2", True, (255, 100, 100))
        screen.blit(p2_title, (100, 320))
        
        # キー説明
        y_offset = 360
        for action, description in [
            ("移動", "↑/←/↓/→: 上/左/下/右"),
            ("武器A", "1: 豆腐投げ"),
            ("武器B", "2: 盾"),
            ("特殊", "3: ハイパーモード/ダッシュ")
        ]:
            text = font.render(f"{action}: {description}", True, (255, 255, 255))
            screen.blit(text, (120, y_offset))
            y_offset += 30
        
        # 戻る方法
        back_text = font.render("戻る: ESCキー または 決定ボタン", True, (200, 200, 200))
        back_rect = back_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        screen.blit(back_text, back_rect)


class OptionsState(BaseState):
    """オプション画面の状態"""
    def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: OptionsState")
        self.selected_item = 0
        self.menu_items = ["プレイヤー1設定", "プレイヤー2設定", "サウンド設定", "戻る"]
        self.previous_state = TitleState(game)  # デフォルトの前の状態はタイトル
    
    def handle_input(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            action = None
            if event.key in self.game.key_mapping_p1:
                action = self.game.key_mapping_p1[event.key]
            
            if action == "up":
                if "menu" in self.game.sounds: self.game.sounds["menu"].play()
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif action == "down":
                if "menu" in self.game.sounds: self.game.sounds["menu"].play()
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif action == "weapon_a" or event.key == pygame.K_z:  # 決定（K_zキーも直接チェック）
                if "special" in self.game.sounds: self.game.sounds["special"].play()
                selected_option = self.menu_items[self.selected_item]
                if selected_option == "プレイヤー1設定":
                    self.game.key_config_player = 1
                    self.game.key_config_selected_item = 0
                    self.game.waiting_for_key_input = False
                    self.game.change_state(KeyConfigState(self.game, self))  # 自身を前の状態として渡す
                elif selected_option == "プレイヤー2設定":
                    self.game.key_config_player = 2
                    self.game.key_config_selected_item = 0
                    self.game.waiting_for_key_input = False
                    self.game.change_state(KeyConfigState(self.game, self))  # 自身を前の状態として渡す
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
        title_font = pygame.font.SysFont(self.game.font_name, 48)
        title_text = title_font.render("オプション", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # メニュー項目
        font = pygame.font.SysFont(self.game.font_name, 36)
        for i, item in enumerate(self.menu_items):
            color = (0, 255, 255) if i == self.selected_item else (255, 255, 255)
            text = font.render(item, True, color)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 60))
            screen.blit(text, rect)

class KeyConfigState(BaseState):
    """キーコンフィグ画面の状態"""
    def __init__(self, game: 'Game', previous_state=None):
        super().__init__(game)
        print("State changed to: KeyConfigState")
        # Gameオブジェクトからキーコンフィグ関連の変数を初期化
        self.player = self.game.key_config_player
        self.selected_item = self.game.key_config_selected_item
        self.waiting_for_input = self.game.waiting_for_key_input
        self.config_items = self.game.key_config_items
        self.previous_state = previous_state or OptionsState(game)

    def handle_input(self, event: pygame.event.Event):
         if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.handle_escape()
                return

            if self.waiting_for_input:
                 # キー入力待ちの処理
                 self.game.assign_key(event.key) # Gameのメソッド呼び出し (仮)
                 self.waiting_for_input = False
                 # 次の項目へ自動で移動
                 self.selected_item = (self.selected_item + 1) % len(self.config_items)
                 # Game側の状態も更新しておく
                 self.game.waiting_for_key_input = self.waiting_for_input
                 self.game.key_config_selected_item = self.selected_item
            else:
                action = None
                if event.key in self.game.key_mapping_p1: # メニュー操作はP1キー
                    action = self.game.key_mapping_p1[event.key]

                if action == "up":
                    self.selected_item = (self.selected_item - 1) % len(self.config_items)
                elif action == "down":
                    self.selected_item = (self.selected_item + 1) % len(self.config_items)
                elif action == "left" or action == "right":
                    self.player = 1 if self.player == 2 else 2
                    # Game側の状態も更新
                    self.game.key_config_player = self.player
                elif action == "weapon_a": # 決定 -> キー入力待ちへ
                    self.waiting_for_input = True
                elif action == "weapon_b":  # 戻る
                    self.handle_escape()
                elif event.key == pygame.K_r: # リセット
                    self.game.reset_key_config() # リセット処理を呼び出す

                # Game側の状態も更新しておく (waiting以外)
                self.game.key_config_selected_item = self.selected_item
                self.game.waiting_for_key_input = self.waiting_for_input

    def handle_escape(self):
        """ESCキーで設定を保存して前の画面に戻る"""
        self.game.save_key_config() # 保存処理を呼び出す
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
        title_font = pygame.font.SysFont(self.game.font_name, 48)
        title_text = title_font.render("キー設定", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # プレイヤー選択表示
        player_text = f"プレイヤー {self.player}"
        player_font = pygame.font.SysFont(self.game.font_name, 36)
        player_label = player_font.render(player_text, True, WHITE)
        screen.blit(player_label, (SCREEN_WIDTH // 2 - player_label.get_width() // 2, 120))
        
        # 設定項目の表示
        y_pos = 180
        menu_font = pygame.font.SysFont(self.game.font_name, 28)
        
        for i, action in enumerate(self.config_items):
            action_color = YELLOW if i == self.selected_item else WHITE
            action_text = f"{ACTION_NAMES[action]}: "
            action_label = menu_font.render(action_text, True, action_color)
            
            # 現在のキー名を取得 (修正)
            key_mapping = self.game.key_mapping_p1 if self.player == 1 else self.game.key_mapping_p2
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
                
            key_label = menu_font.render(key_text, True, action_color)
            
            # 描画
            screen.blit(action_label, (SCREEN_WIDTH // 3, y_pos))
            screen.blit(key_label, (SCREEN_WIDTH // 3 + action_label.get_width() + 10, y_pos))
            y_pos += 40
            
        # 操作説明
        instructions = [
            "↑/↓: 項目選択",
            "ENTER: キー設定変更",
            "TAB: プレイヤー切替",
            "ESC: 戻る"
        ]
        
        y_pos = 480
        instruction_font = pygame.font.SysFont(self.game.font_name, 20)
        for instruction in instructions:
            inst_label = instruction_font.render(instruction, True, GRAY)
            screen.blit(inst_label, (SCREEN_WIDTH // 2 - inst_label.get_width() // 2, y_pos))
            y_pos += 30


class PauseState(BaseState):
    """ポーズ画面の状態"""

    def __init__(self, game, prev_state=None):
        super().__init__(game)
        print("State changed to: PauseState")
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
        if hasattr(self.game, 'player1') and hasattr(self.game, 'player2'):
            self.game.player1.key_states = {key: False for key in self.game.player1.key_states}
            self.game.player2.key_states = {key: False for key in self.game.player2.key_states}
        
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
    def __init__(self, game: 'Game'):
        super().__init__(game)
        print("State changed to: SplashScreenState")
        # スプラッシュ画面の表示時間 (ミリ秒)
        self.display_duration = 3000
        # フェードイン・アウトの時間 (ミリ秒)
        self.fade_duration = 500
        # 開始時間を記録
        self.start_time = pygame.time.get_ticks()
        # 前回の更新時間を記録（デバッグ用）
        self.last_update_time = self.start_time
        # 強制的な遷移用タイマー (ミリ秒) - より短く設定
        self.force_transition_after = 3000  # 3秒後に強制遷移
        # 遷移フラグ - 一度だけ遷移処理を行うため
        self.transition_started = False
        
        # フォントの初期化を修正（SysFontからFontに変更）
        try:
            self.font_large = pygame.font.Font(None, 72)  # デフォルトフォントを使用
            self.font_small = pygame.font.Font(None, 24)  # デフォルトフォントを使用
            print("フォント初期化成功")
        except Exception as e:
            print(f"フォント初期化エラー: {e}")
            # フォールバックとしてデフォルトフォントを使用
            self.font_large = pygame.font.Font(None, 72)
            self.font_small = pygame.font.Font(None, 24)
        
        # アルファ値の初期設定
        self.alpha = 0
        # フェード状態 (0: フェードイン, 1: 表示中, 2: フェードアウト, 3: 完了)
        self.fade_state = 0
        # ロゴ画像の代わりに描画するテキスト（日本語テキストを英語に置き換え）
        self.logo_text = "ACCELERATION OF TOFU"  # 日本語を英語に置き換え
        self.subtitle_text = "Enjoy the Game"
        self.credit_text = "Presented by Tofu Dev Team"
        
        # フェード効果のデバッグ用
        self.debug_fade_states = ["フェードイン", "表示中", "フェードアウト", "完了"]
        
        print(f"SplashScreenState初期化完了: start_time={self.start_time}")
        print(f"フェード設定: フェードイン={self.fade_duration}ms, 表示={self.display_duration-self.fade_duration*2}ms, フェードアウト={self.fade_duration}ms")

    def handle_input(self, event: pygame.event.Event):
        # スプラッシュ画面ではキー入力はタイトル画面への即時遷移を引き起こす
        if event.type == pygame.KEYDOWN:
            print(f"キー入力でスキップ: key={event.key}")
            self.skip_to_title()

    def skip_to_title(self):
        """即座にタイトル画面に遷移"""
        # 既に遷移処理が始まっている場合は何もしない
        if self.transition_started:
            print("遷移処理はすでに開始されています")
            return
            
        self.transition_started = True
        print("タイトル画面への遷移を実行します")
        try:
            next_state = TitleState(self.game)
            self.game.change_state(next_state)
            print("タイトル画面への遷移完了")
        except Exception as e:
            print(f"遷移中にエラーが発生: {e}")
            # エラーが発生した場合でも遷移フラグをリセット
            self.transition_started = False

    def update(self):
        """スプラッシュ画面の更新処理"""
        # 既に遷移処理が始まっている場合は何もしない
        if self.transition_started:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time
        
        # デバッグ情報（250ms毎にログ出力）
        time_since_last_update = current_time - self.last_update_time
        if time_since_last_update > 250:
            print(f"スプラッシュ更新: elapsed={elapsed_time}ms, state={self.fade_state}({self.debug_fade_states[self.fade_state]}), alpha={self.alpha}")
            self.last_update_time = current_time

        # 強制的な遷移チェック（3秒経過したら強制遷移）
        if elapsed_time >= self.force_transition_after:
            print(f"自動的にタイトル画面へ遷移します: time={elapsed_time}ms")
            self.skip_to_title()
            return

        # フェードインフェーズ
        if self.fade_state == 0:
            # フェードイン中
            if elapsed_time < self.fade_duration:
                # アルファ値を0から255に徐々に変化
                self.alpha = int(255 * (elapsed_time / self.fade_duration))
            else:
                # フェードイン完了
                self.alpha = 255
                self.fade_state = 1
                print(f"フェードイン完了: time={elapsed_time}ms, alpha={self.alpha}")
        
        # 表示中フェーズ
        elif self.fade_state == 1:
            if elapsed_time > self.display_duration - self.fade_duration:
                # フェードアウト開始
                self.fade_state = 2
                print(f"フェードアウト開始: time={elapsed_time}ms, alpha={self.alpha}")
        
        # フェードアウトフェーズ
        elif self.fade_state == 2:
            if elapsed_time > self.display_duration:
                # フェードアウト完了時の処理
                fade_progress = (elapsed_time - (self.display_duration - self.fade_duration)) / self.fade_duration
                self.alpha = int(255 * (1 - fade_progress))
                self.alpha = max(0, min(255, self.alpha))  # アルファ値を0-255の範囲に制限
                
                # フェードアウト完了判定
                if self.alpha <= 0:
                    self.fade_state = 3
                    print(f"フェードアウト完了、タイトルへ遷移: time={elapsed_time}ms, alpha={self.alpha}")
                    self.skip_to_title()
            else:
                # フェードアウト中の処理
                fade_progress = (elapsed_time - (self.display_duration - self.fade_duration)) / self.fade_duration
                self.alpha = int(255 * (1 - fade_progress))
                self.alpha = max(0, min(255, self.alpha))  # アルファ値を0-255の範囲に制限

    def draw(self, screen: pygame.Surface):
        """スプラッシュ画面の描画"""
        # 背景を青で塗りつぶし
        screen.fill((0, 0, 50))
        
        # フェードステートとアルファ値をデバッグ表示（画面四隅の赤い四角形）
        fade_color = (255, 0, 0)
        if self.fade_state == 0:  # フェードイン中
            fade_color = (0, 255, 0)  # 緑
        elif self.fade_state == 1:  # 表示中
            fade_color = (255, 255, 0)  # 黄
        elif self.fade_state == 2:  # フェードアウト中
            fade_color = (255, 0, 0)  # 赤
        
        pygame.draw.rect(screen, fade_color, (10, 10, 50, 50))
        pygame.draw.rect(screen, fade_color, (SCREEN_WIDTH - 60, 10, 50, 50))
        pygame.draw.rect(screen, fade_color, (10, SCREEN_HEIGHT - 60, 50, 50))
        pygame.draw.rect(screen, fade_color, (SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, 50, 50))
        
        # アルファ値によって白から透明に変化する四角形（フェード効果をより明確に表示）
        # 中央の大きな四角形
        alpha_rect = pygame.Surface((300, 150), pygame.SRCALPHA)
        alpha_rect.fill((255, 255, 255, self.alpha))
        screen.blit(alpha_rect, (SCREEN_WIDTH//2 - 150, 50))
        
        # テキスト描画をアルファ値に基づいて行う
        try:
            # ロゴテキスト - アルファ値に応じて描画
            logo_render = self.font_large.render(self.logo_text, True, (255, 255, 255))
            # アルファ値を適用
            logo_surface = pygame.Surface(logo_render.get_size(), pygame.SRCALPHA)
            logo_surface.fill((255, 255, 255, 0))  # 透明で初期化
            logo_surface.blit(logo_render, (0, 0))
            logo_surface.set_alpha(self.alpha)  # アルファ値を設定
            
            # サブタイトル - アルファ値に応じて描画
            subtitle_render = self.font_small.render(self.subtitle_text, True, (0, 255, 255))
            subtitle_surface = pygame.Surface(subtitle_render.get_size(), pygame.SRCALPHA)
            subtitle_surface.fill((255, 255, 255, 0))
            subtitle_surface.blit(subtitle_render, (0, 0))
            subtitle_surface.set_alpha(self.alpha)
            
            # クレジット - アルファ値に応じて描画
            credit_render = self.font_small.render(self.credit_text, True, (200, 200, 200))
            credit_surface = pygame.Surface(credit_render.get_size(), pygame.SRCALPHA)
            credit_surface.fill((255, 255, 255, 0))
            credit_surface.blit(credit_render, (0, 0))
            credit_surface.set_alpha(self.alpha)
            
            # 画面中央に配置
            screen.blit(logo_surface, (SCREEN_WIDTH//2 - logo_render.get_width()//2, SCREEN_HEIGHT//2 - 100))
            screen.blit(subtitle_surface, (SCREEN_WIDTH//2 - subtitle_render.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(credit_surface, (SCREEN_WIDTH//2 - credit_render.get_width()//2, SCREEN_HEIGHT//2 + 100))
            
            # アルファ値とフェードステート表示（デバッグ用）
            debug_text = f"Alpha: {self.alpha} State: {self.fade_state} ({self.debug_fade_states[self.fade_state]})"
            alpha_text = self.font_small.render(debug_text, True, (255, 255, 0))
            screen.blit(alpha_text, (20, SCREEN_HEIGHT - 30))
            
            # 経過時間表示（デバッグ用）
            elapsed = pygame.time.get_ticks() - self.start_time
            time_text = self.font_small.render(f"Time: {elapsed}ms", True, (255, 255, 0))
            screen.blit(time_text, (20, SCREEN_HEIGHT - 60))
            
        except Exception as e:
            # レンダリングエラーの場合はテキストの代わりに白い四角形を表示
            print(f"テキストレンダリングエラー: {e}")
            pygame.draw.rect(screen, (255, 255, 255), (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 40, 300, 80)) 