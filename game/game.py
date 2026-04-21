import pygame
import math
import json
import os
import random
from game.constants import (
    ARENA_CENTER_X, ARENA_CENTER_Y, ACTION_NAMES,
    SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2,
    MAX_HEALTH, JAPANESE_FONT_NAMES, DEFAULT_FONT, JP_FONT_PATH,
    TOFU_WHITE, YELLOW, MAGENTA, CYAN,
    SHIELD_DURATION, DASH_COOLDOWN, PLAYER_SPEED, PLAYER_DASH_SPEED,
    MAX_HEAT, MAX_HYPER,
    HYPER_CONSUMPTION_RATE, HYPER_DECREASE_RATE_AT_BORDER, HYPER_ACTIVATION_COST,
    HYPER_DURATION, DASH_RING_DURATION, HEAT_DECREASE_RATE,
    WEAPON_TYPES
)
from game.player import Player
from game.arena import Arena
from game.hud import HUD
from game.ai import AIController
from game.states import TitleState
from game.weapon import Weapon
from game.projectile import BeamProjectile, BallisticProjectile, MeleeProjectile

class Game:
    def __init__(self, screen, debug=False, enable_audio=True, enable_title_background=True):
        self.screen = screen
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.enable_audio = enable_audio
        self.enable_title_background = enable_title_background
        self.arena = Arena()
        self.player1 = Player(ARENA_CENTER_X - 100, ARENA_CENTER_Y, is_player1=True, game=self)
        self.player2 = Player(ARENA_CENTER_X + 100, ARENA_CENTER_Y, is_player1=False, game=self)
        
        # プレイヤーのデバッグモードを設定
        self.debug_mode = debug
        self.player1.debug_mode = debug
        self.player2.debug_mode = False  # プレイヤー2は常にデバッグログを出力しない
        
        self.hud = HUD(self.player1, self.player2)
        
        # 日本語フォント設定
        self.font_name = DEFAULT_FONT  # デフォルトフォント名を設定
        self.font_path = None  # フォントパスも設定
        self.init_fonts()  # フォント初期化を呼び出し
        
        self.projectiles = []
        self.effects = []
        self.current_time = 0
        
        # ズーム関連の属性
        self.current_zoom = 1.0  # 現在のズーム率
        self.target_zoom = 1.0   # 目標ズーム率
        
        # 自動テスト用タイマー
        self.test_timer = 0
        self.test_duration = 60 * 10  # 10秒間のテスト（60FPS）
        
        # 自動テストの時間オプション
        self.test_time_options = ["5秒", "30秒", "勝負がつくまで"]
        self.selected_test_time = 1  # デフォルトで30秒を選択
        
        # AIの移動制御用変数
        self.ai_move_timer1 = 0
        self.ai_move_timer2 = 0
        self.ai_move_interval = 60 * 1  # 1秒間隔（60FPS）
        self.ai_move_direction1 = {"up": False, "down": False, "left": False, "right": False, "dash": False}
        self.ai_move_direction2 = {"up": False, "down": False, "left": False, "right": False, "dash": False}
        self.ai_controller = AIController(self)
        
        # メニュー関連 (状態クラスから参照される可能性あり)
        self.menu_items = ["シングル対戦モード", "トレーニングモード", "自動テスト", "操作説明", "オプション", "終了"]
        self.selected_item = 0 # TitleStateが主に使うが、初期値として残す
        
        # オプションメニュー項目 (状態クラスから参照される可能性あり)
        self.option_menu_items = ["キーコンフィグ", "戻る"]
        self.option_selected_item = 0 # OptionsStateが主に使うが、初期値として残す

        # ポーズメニュー項目 (PauseState内で定義)
        # self.pause_menu_items = ["ゲームに戻る", "操作説明", "タイトルに戻る"]
        self.pause_selected_item = 0 # PauseStateが主に使うが、初期値として残す
        
        # キーコンフィグ関連 (状態クラスから参照される可能性あり)
        self.key_config_player = 1  # 1=プレイヤー1、2=プレイヤー2
        self.key_config_items = list(ACTION_NAMES.keys())  # 操作名のリスト
        self.key_config_selected_item = 0
        self.waiting_for_key_input = False  # キー入力待ち状態かどうか
        
        # キー状態 (GameStateなどが使う)
        self.keys_pressed = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # 効果音とBGM
        self.title_bgm = None
        self.title_bgm_playing = False
        if self.enable_audio and not pygame.mixer.get_init():
            pygame.mixer.init()
        self.sounds = {}
        self.init_sounds()  # 効果音の初期化を呼び出し
        self.init_title_bgm()
        
        # キーマッピングを constants.py で定義されているデフォルト値で初期化
        self.key_mapping_p1 = DEFAULT_KEY_MAPPING_P1.copy()
        self.key_mapping_p2 = DEFAULT_KEY_MAPPING_P2.copy()
        self.key_mapping = DEFAULT_KEY_MAPPING_P1.copy()  # 汎用マッピング（P1と同じ）
        
        # キーコンフィグ設定を読み込み（コメントアウト - デフォルトのマッピングを使用）
        # self.load_key_config()

        # 状態管理
        self.current_state = None
        self.previous_state = None
        self.change_state(TitleState(self))

    # ---- 状態パターンのためのメソッド ----
    def change_state(self, new_state, previous_state=None):
        """状態遷移を行う"""
        if self.current_state and hasattr(self.current_state, "exit"):
            self.current_state.exit()
        self.current_state = new_state
        if previous_state:
            self.previous_state = previous_state
        if self.current_state and hasattr(self.current_state, "enter"):
            self.current_state.enter()
    # ---------------------------------

    def init_fonts(self):
        """日本語フォントの初期化。

        同梱TTF (assets/fonts/MPLUS1p-Regular.ttf) が存在すればそれを優先する。
        pygbag/WASM では SysFont 経由のシステムフォント検索が機能しないため、
        バンドル済み TTF を pygame.font.Font() でロードするのが唯一の確実な経路。
        存在しない場合のみレガシーな SysFont 検索にフォールバック。
        """
        if os.path.exists(JP_FONT_PATH):
            self.font_path = JP_FONT_PATH
            self.font_name = JP_FONT_PATH  # states.py等の既存コード互換用
            return

        self.font_path = None
        available_fonts = pygame.font.get_fonts()
        self.font_name = None
        available_fonts_lower = [f.lower() for f in available_fonts]

        for font_name in JAPANESE_FONT_NAMES:
            font_lower = font_name.lower()
            if font_lower in available_fonts_lower:
                index = available_fonts_lower.index(font_lower)
                self.font_name = available_fonts[index]
                break

        if not self.font_name:
            self.font_name = DEFAULT_FONT

    def make_font(self, size):
        """日本語対応フォントをサイズ指定で生成する統一ヘルパ。

        font_path が設定されていれば TTF 直ロード (pygbag 対応)、
        そうでなければ SysFont にフォールバック。
        """
        if self.font_path and os.path.exists(self.font_path):
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont(self.font_name, size)

    def init_sounds(self):
        # BGMとSEの読み込み
        self.sounds = {}
        if not self.enable_audio:
            return
        
        # 効果音ファイルが存在するか確認して読み込む
        sound_files = {
            "shot": "assets/sounds/shot.ogg",
            "special": "assets/sounds/special.ogg",
            "hit": "assets/sounds/hit.ogg",
            "shield": "assets/sounds/shield.ogg",
            "hyper": "assets/sounds/hyper.ogg",
            "menu": "assets/sounds/menu.ogg"
        }
        
        # サウンドディレクトリの存在確認
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
        os.makedirs(sound_dir, exist_ok=True)
        
        # 存在するサウンドファイルのみロード
        for sound_name, sound_path in sound_files.items():
            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), sound_path)
            if os.path.exists(full_path):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(full_path)
                except Exception:
                    pass

    def init_title_bgm(self):
        if not self.enable_audio:
            return
        try:
            self.title_bgm = pygame.mixer.Sound("assets/sounds/rockman_title.ogg")
            # 起動直後にいきなり鳴っても驚かない音量に抑える。
            self.title_bgm.set_volume(0.3)
        except Exception:
            self.title_bgm = None

    def play_title_bgm(self):
        if self.title_bgm and not self.title_bgm_playing:
            self.title_bgm.play(-1)
            self.title_bgm_playing = True

    def stop_title_bgm(self):
        if self.title_bgm and self.title_bgm_playing:
            self.title_bgm.stop()
            self.title_bgm_playing = False
    
    def handle_keydown(self, key):
        """
        キー入力をハンドリングし、現在の状態に応じて処理する
        全てのキー入力は current_state を通して処理される
        
        Args:
            key (int): 押されたキーのpygame定義定数
        """
        # ESCキーの特別処理をStatesクラスのhandle_inputに移行
        # 現在の状態にキー入力イベントを渡す
        event = pygame.event.Event(pygame.KEYDOWN, {"key": key})
        self.current_state.handle_input(event)
    
    def handle_keyup(self, key):
        """
        キーリリースをハンドリングし、現在の状態に応じて処理する
        
        Args:
            key (int): 離されたキーのpygame定義定数
        """
        # 現在の状態にキーリリースイベントを渡す
        event = pygame.event.Event(pygame.KEYUP, {"key": key})
        self.current_state.handle_input(event)
    
    def update(self):
        """ゲーム状態の更新"""
        self.current_time += 1
        if self.current_state.needs_game_update():
            self.previous_state = self.current_state
        self.current_state.update()
    
    def update_gameplay_elements(self, use_simple_ai=False):
        """対戦/トレーニング共通の更新処理。"""
        self.arena.update()
        self.player1.update(self.arena, self.player2)

        if use_simple_ai:
            self.player2.key_states = self.ai_controller.simple_ai_control()
        self.player2.update(self.arena, self.player1)

        # 粘り（糸）の物理引き寄せロジック
        # プレイヤー1が発酵中ならプレイヤー2を引き寄せる
        if self.player1.is_fermented:
            self._apply_sticky_tether(self.player1, self.player2)
        # プレイヤー2が発酵中ならプレイヤー1を引き寄せる
        if self.player2.is_fermented:
            self._apply_sticky_tether(self.player2, self.player1)

        for proj in self.projectiles[:]:
            proj.update()
            if proj.is_expired:
                self.projectiles.remove(proj)

        for effect in self.effects[:]:
            effect.update()
            if effect.is_dead:
                self.effects.remove(effect)

        self.handle_collisions()
        self._handle_match_end()

    def update_auto_test_mode(self):
        """自動テストモードの更新。"""
        self.test_timer += 1
        if self.test_duration != float("inf") and self.test_timer >= self.test_duration:
            self.change_state(TitleState(self))
            return

        if self.test_duration == float("inf") and (
            self.player1.health <= 0 or self.player2.health <= 0
        ):
            self.winner = 2 if self.player1.health <= 0 else 1
            self.result_timer = 0
            self.change_state(TitleState(self))
            return

        self.ai_move_timer1 += 1
        self.ai_move_timer2 += 1

        self.player1.key_states = self.ai_controller.auto_test_ai_control(
            self.player1, self.player2, is_player1=True
        )
        self.player2.key_states = self.ai_controller.auto_test_ai_control(
            self.player2, self.player1, is_player1=False
        )
        self.update_gameplay_elements(use_simple_ai=False)

    def _handle_match_end(self):
        state = self.current_state
        if (not state.is_auto_test_mode() or self.test_duration != float("inf")) and (
            self.player1.health <= 0 or self.player2.health <= 0
        ):
            self.result_timer = 0
            self.winner = 2 if self.player1.health <= 0 else 1
            if state.resets_health_on_zero():
                if self.player1.health <= 0:
                    self.player1.health = MAX_HEALTH
                if self.player2.health <= 0:
                    self.player2.health = MAX_HEALTH
            self.change_state(TitleState(self))

    # Backward-compatible wrappers while AI implementation lives in AIController.
    def auto_test_ai_control(self, player, opponent, is_player1=True):
        return self.ai_controller.auto_test_ai_control(player, opponent, is_player1)

    def decide_movement_style(self, player, opponent, is_player1):
        return self.ai_controller.decide_movement_style(player, opponent, is_player1)

    def predict_projectile_collision(self, player):
        return self.ai_controller.predict_projectile_collision(player)

    def is_projectile_nearby(self, player, distance_threshold):
        return self.ai_controller.is_projectile_nearby(player, distance_threshold)

    def simple_ai_control(self):
        return self.ai_controller.simple_ai_control()
        
    def _apply_sticky_tether(self, fermented_player, opponent):
        """発酵（粘り）オーラによる引き寄せ物理を適用"""
        dx = fermented_player.x - opponent.x
        dy = fermented_player.y - opponent.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 100 and distance > 5: # 100ピクセル以内かつ重なりすぎていない
            # 引き寄せ強度（距離が近いほど強く、最大で1フレームあたり1.0ピクセル移動）
            strength = (1.0 - (distance / 100.0)) * 1.5
            angle = math.atan2(dy, dx)
            
            # 相手の位置を強制的に微移動（引き寄せ）
            opponent.x += math.cos(angle) * strength
            opponent.y += math.sin(angle) * strength

    def handle_collisions(self):
        """衝突判定処理"""
        # プレイヤー同士の衝突判定
        dx = self.player1.x - self.player2.x
        dy = self.player1.y - self.player2.y
        distance = math.sqrt(dx*dx + dy*dy)
        min_dist = self.player1.radius + self.player2.radius
        
        if distance < min_dist:
            # 押し戻し処理
            if distance == 0:
                # 完全に重なっている場合はランダムな方向に
                angle = random.uniform(0, 2 * math.pi)
                overlap = min_dist
            else:
                angle = math.atan2(dy, dx)
                overlap = min_dist - distance
            
            # 半分ずつ押し戻す基本ロジックを、水分量（重さ）に応じて調整
            w1 = 0.5 + (self.player1.water_level / 100.0) * 0.5
            w2 = 0.5 + (self.player2.water_level / 100.0) * 0.5
            
            total_w = w1 + w2
            ratio1 = w2 / total_w
            ratio2 = w1 / total_w
            
            self.player1.x += math.cos(angle) * (overlap * ratio1)
            self.player1.y += math.sin(angle) * (overlap * ratio1)
            self.player2.x -= math.cos(angle) * (overlap * ratio2)
            self.player2.y -= math.sin(angle) * (overlap * ratio2)

        # プレイヤーと弾の衝突判定
        from game.projectile import SoybeanCollectible
        for proj in self.projectiles[:]:
            # 豆（コレクタブル）の回収判定
            if isinstance(proj, SoybeanCollectible):
                # プレイヤー1の回収
                dist1 = math.sqrt((self.player1.x - proj.x)**2 + (self.player1.y - proj.y)**2)
                if dist1 < (self.player1.radius + proj.radius + 10):
                    self.player1.beans = min(100.0, self.player1.beans + 5.0)
                    proj.is_dead = True
                    continue
                # プレイヤー2の回収
                dist2 = math.sqrt((self.player2.x - proj.x)**2 + (self.player2.y - proj.y)**2)
                if dist2 < (self.player2.radius + proj.radius + 10):
                    self.player2.beans = min(100.0, self.player2.beans + 5.0)
                    proj.is_dead = True
                    continue
                continue

            # プレイヤー1との衝突
            if proj.owner != self.player1 and self.player1.collides_with(proj):
                damage = proj.damage
                if not self.player1.is_shielding():
                    damage = damage * (1 + self.player1.heat / 100)
                    self.player1.take_damage(damage)
                    # 豆をドロップ
                    self.spawn_beans(self.player1.x, self.player1.y, 3)
                    proj.on_hit(self.player1)
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                else:
                    proj.reflect(self.player1)
                    
            # プレイヤー2との衝突
            elif proj.owner != self.player2 and self.player2.collides_with(proj):
                damage = proj.damage
                if not self.player2.is_shielding():
                    damage = damage * (1 + self.player2.heat / 100)
                    self.player2.take_damage(damage)
                    # 豆をドロップ
                    self.spawn_beans(self.player2.x, self.player2.y, 3)
                    proj.on_hit(self.player2)
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                else:
                    proj.reflect(self.player2)
    
    def draw(self):
        """現在の状態に応じた描画処理"""
        self.current_state.draw(self.screen)
    
    def draw_to_surface(self, surface):
        """サーフェスにゲーム画面を描画（アドバタイズモード用）"""
        # バックバッファは毎フレーム再生成せずインスタンスにキャッシュする
        buffer = getattr(self, "_advert_buffer", None)
        if buffer is None:
            buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._advert_buffer = buffer
        buffer.fill((0, 0, 0))

        dx = self.player1.x - self.player2.x
        dy = self.player1.y - self.player2.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        min_distance = 150
        max_distance = 400
        max_zoom = 1.5
        min_zoom = 1.0
        
        if distance <= min_distance:
            current_zoom = max_zoom
        elif distance >= max_distance:
            current_zoom = min_zoom
        else:
            ratio = (distance - min_distance) / (max_distance - min_distance)
            current_zoom = max_zoom - ratio * (max_zoom - min_zoom)
        
        self.arena.draw(buffer)
        for proj in self.projectiles:
            proj.draw(buffer)
        self.player1.draw(buffer)
        self.player2.draw(buffer)
        for effect in self.effects:
            effect.draw(buffer)
        
        center_x = (self.player1.x + self.player2.x) / 2
        center_y = (self.player1.y + self.player2.y) / 2
        
        clip_x = int(center_x - SCREEN_WIDTH / (2 * current_zoom))
        clip_y = int(center_y - SCREEN_HEIGHT / (2 * current_zoom))
        
        if clip_x < 0: clip_x = 0
        if clip_y < 0: clip_y = 0
        if clip_x + int(SCREEN_WIDTH / current_zoom) > SCREEN_WIDTH:
            clip_x = max(0, SCREEN_WIDTH - int(SCREEN_WIDTH / current_zoom))
        if clip_y + int(SCREEN_HEIGHT / current_zoom) > SCREEN_HEIGHT:
            clip_y = max(0, SCREEN_HEIGHT - int(SCREEN_HEIGHT / current_zoom))
        
        clip_width = min(int(SCREEN_WIDTH / current_zoom), SCREEN_WIDTH - clip_x)
        clip_height = min(int(SCREEN_HEIGHT / current_zoom), SCREEN_HEIGHT - clip_y)
        
        try:
            clip_area = pygame.Rect(clip_x, clip_y, clip_width, clip_height)
            clipped_buffer = buffer.subsurface(clip_area)
            zoomed_width = int(clip_width * current_zoom)
            zoomed_height = int(clip_height * current_zoom)
            zoomed_buffer = pygame.transform.scale(clipped_buffer, (zoomed_width, zoomed_height))
            surface.fill((0, 0, 0))
            dest_x = int(SCREEN_WIDTH/2 - zoomed_width/2)
            dest_y = int(SCREEN_HEIGHT/2 - zoomed_height/2)
            surface.blit(zoomed_buffer, (dest_x, dest_y))
        except ValueError:
            surface.blit(buffer, (0, 0))
    
    def add_projectile(self, projectile):
        """弾を追加"""
        self.projectiles.append(projectile)
        
    def add_effect(self, effect):
        """エフェクトを追加"""
        self.effects.append(effect)
    
    def spawn_beans(self, x, y, count):
        """指定した場所に豆をドロップする"""
        from game.projectile import SoybeanCollectible
        for _ in range(count):
            bx = x + random.uniform(-20, 20)
            by = y + random.uniform(-20, 20)
            self.projectiles.append(SoybeanCollectible(bx, by))
    
    def reset_players(self):
        """プレイヤーの状態をリセット"""
        self.player1.reset()
        self.player2.reset()
        self.projectiles.clear()
        self.effects.clear()
        self.current_time = 0
    
    def save_key_config(self):
        """キーコンフィグ設定を保存"""
        try:
            p1_config = {str(k): v for k, v in self.key_mapping_p1.items()}
            p2_config = {str(k): v for k, v in self.key_mapping_p2.items()}
            config = {"p1": p1_config, "p2": p2_config}
            with open("key_config.json", "w") as f:
                json.dump(config, f, indent=4)
            return True
        except Exception:
            return False
    
    def reset_key_config(self):
        """キー設定をデフォルトに戻す"""
        if self.key_config_player == 1:
            self.key_mapping_p1.clear()
            self.key_mapping_p1.update(DEFAULT_KEY_MAPPING_P1)
            self.key_mapping.clear()
            self.key_mapping.update(self.key_mapping_p1)
        else:
            self.key_mapping_p2.clear()
            self.key_mapping_p2.update(DEFAULT_KEY_MAPPING_P2)
        self.save_key_config()
    
    def load_key_config(self):
        """キーコンフィグ設定を読み込み"""
        ALLOWED_KEYS = [
            pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
            pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e,
            pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j,
            pygame.K_k, pygame.K_l, pygame.K_m, pygame.K_n, pygame.K_o,
            pygame.K_p, pygame.K_q, pygame.K_r, pygame.K_s, pygame.K_t,
            pygame.K_u, pygame.K_v, pygame.K_w, pygame.K_x, pygame.K_y, pygame.K_z,
            pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
            pygame.K_KP0, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4,
            pygame.K_KP5, pygame.K_KP6, pygame.K_KP7, pygame.K_KP8, pygame.K_KP9,
            pygame.K_KP_PLUS, pygame.K_KP_MINUS, pygame.K_KP_MULTIPLY, pygame.K_KP_DIVIDE,
            pygame.K_SPACE,
            pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_TAB,
            pygame.K_LSHIFT, pygame.K_RSHIFT,
            pygame.K_SEMICOLON,
            pygame.K_QUOTE,
            pygame.K_PERIOD,
            pygame.K_COMMA,
            pygame.K_MINUS,
            pygame.K_EQUALS,
            pygame.K_BACKSLASH,
            pygame.K_SLASH,
            pygame.K_BACKQUOTE,
            pygame.K_LEFTBRACKET,
            pygame.K_RIGHTBRACKET,
        ]

        self.key_mapping_p1 = DEFAULT_KEY_MAPPING_P1.copy()
        self.key_mapping_p2 = DEFAULT_KEY_MAPPING_P2.copy()
        self.key_mapping = DEFAULT_KEY_MAPPING_P1.copy()

        try:
            if not os.path.exists("key_config.json"):
                return

            with open("key_config.json", "r") as f:
                config = json.load(f)

            p1_cfg = config.get("p1", {})
            p2_cfg = config.get("p2", {})
            if not p1_cfg or not p2_cfg:
                return

            p1_settings = {}
            p2_settings = {}
            for k, v in p1_cfg.items():
                try:
                    key_int = int(k)
                    if key_int in ALLOWED_KEYS:
                        p1_settings[key_int] = v
                except (TypeError, ValueError):
                    continue
            for k, v in p2_cfg.items():
                try:
                    key_int = int(k)
                    if key_int in ALLOWED_KEYS:
                        p2_settings[key_int] = v
                except (TypeError, ValueError):
                    continue

            all_actions = set(ACTION_NAMES.keys())
            missing_p1 = all_actions - set(p1_settings.values())
            missing_p2 = all_actions - set(p2_settings.values())
            for action in missing_p1:
                for k, v in DEFAULT_KEY_MAPPING_P1.items():
                    if v == action and k not in p1_settings and k in ALLOWED_KEYS:
                        p1_settings[k] = action
                        break
            for action in missing_p2:
                for k, v in DEFAULT_KEY_MAPPING_P2.items():
                    if v == action and k not in p2_settings and k in ALLOWED_KEYS:
                        p2_settings[k] = action
                        break

            if p1_settings:
                self.key_mapping_p1 = p1_settings
            if p2_settings:
                self.key_mapping_p2 = p2_settings
            self.key_mapping = self.key_mapping_p1.copy()
        except Exception:
            self.key_mapping_p1 = DEFAULT_KEY_MAPPING_P1.copy()
            self.key_mapping_p2 = DEFAULT_KEY_MAPPING_P2.copy()
            self.key_mapping = DEFAULT_KEY_MAPPING_P1.copy()

    def assign_key(self, key):
        """キーコンフィグ画面でキーを割り当てる"""
        action = self.key_config_items[self.key_config_selected_item]
        current_mapping = self.key_mapping_p1 if self.key_config_player == 1 else self.key_mapping_p2
        for k in list(current_mapping.keys()):
            if current_mapping[k] == action:
                del current_mapping[k]
        current_mapping[key] = action
        if self.key_config_player == 1:
            for k in list(self.key_mapping.keys()):
                if self.key_mapping[k] == action:
                    del self.key_mapping[k]
            self.key_mapping[key] = action

    def draw_background(self, screen):
        """ゲーム背景を描画する"""
        if not isinstance(screen, pygame.Surface):
            return
        # 画面を黒で塗りつぶす
        screen.fill((0, 0, 0))
        
        # アリーナを描画
        self.arena.draw(screen)

    def toggle_debug_mode(self):
        """デバッグモードの切り替え"""
        self.debug_mode = not self.debug_mode
        self.player1.debug_mode = self.debug_mode
        self.player2.debug_mode = False
