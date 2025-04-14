import pygame
import random
import sys
import math
import json
import os
from game.constants import (
    ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS, KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPING, ACTION_NAMES,
    JAPANESE_FONT_NAMES, DEFAULT_FONT, YELLOW, 
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, CYAN, DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2,
    MAX_HEALTH, KEY_NAMES
)
from game.player import Player
from game.arena import Arena
from game.hud import HUD
from game.state import GameState

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = GameState.TITLE
        self.arena = Arena()
        self.player1 = Player(ARENA_CENTER_X - 100, ARENA_CENTER_Y, is_player1=True)
        self.player2 = Player(ARENA_CENTER_X + 100, ARENA_CENTER_Y, is_player1=False)
        
        # プレイヤーにゲームインスタンスをセット
        self.player1.game = self
        self.player2.game = self
        
        self.hud = HUD(self.player1, self.player2)
        
        # 日本語フォント設定
        self.font_name = self.hud.font_name  # HUDからフォント名を取得
        
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
        
        # メニュー関連
        self.menu_items = ["対戦モード", "トレーニングモード", "自動テスト", "操作説明", "オプション", "終了"]
        self.selected_item = 0
        
        # オプションメニュー項目
        self.option_menu_items = ["キーコンフィグ", "戻る"]
        self.option_selected_item = 0
        
        # キーコンフィグ関連
        self.key_config_player = 1  # 1=プレイヤー1、2=プレイヤー2
        self.key_config_items = list(ACTION_NAMES.keys())  # 操作名のリスト
        self.key_config_selected_item = 0
        self.waiting_for_key_input = False  # キー入力待ち状態かどうか
        
        # キー状態
        self.keys_pressed = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # 効果音とBGM
        pygame.mixer.init()
        self.sounds = {}
        self.init_sounds()  # 効果音の初期化を呼び出し
        
        # キーコンフィグ設定を読み込み
        self.load_key_config()

    def init_fonts(self):
        """日本語フォントの初期化"""
        # 利用可能なすべてのフォントをデバッグ出力
        available_fonts = pygame.font.get_fonts()
        print("利用可能なフォント一覧:")
        for f in available_fonts:
            if 'gothic' in f.lower() or 'mincho' in f.lower() or 'meiryo' in f.lower() or 'ipa' in f.lower() or 'ud' in f.lower():
                print(f"- {f}")
        
        # 日本語フォント名を小文字に変換して検索
        self.font_name = None
        available_fonts_lower = [f.lower() for f in available_fonts]
        
        for font_name in JAPANESE_FONT_NAMES:
            font_lower = font_name.lower()
            if font_lower in available_fonts_lower:
                index = available_fonts_lower.index(font_lower)
                self.font_name = available_fonts[index]  # 元のケースのフォント名を使用
                print(f"日本語フォントが見つかりました: {self.font_name}")
                break
        
        if not self.font_name:
            # 日本語フォントが見つからない場合はデフォルトを使用
            self.font_name = DEFAULT_FONT
            print(f"警告: 日本語フォントが見つかりませんでした。{DEFAULT_FONT}を使用します。")

    def init_sounds(self):
        # BGMとSEの読み込み
        self.sounds = {}
        
        # 効果音ファイルが存在するか確認して読み込む
        sound_files = {
            "shot": "assets/sounds/shot.wav",
            "special": "assets/sounds/special.wav",
            "hit": "assets/sounds/hit.wav",
            "shield": "assets/sounds/shield.wav",
            "hyper": "assets/sounds/hyper.wav",
            "menu": "assets/sounds/menu.wav"
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
                    print(f"効果音をロードしました: {sound_name}")
                except Exception as e:
                    print(f"効果音のロードに失敗しました: {sound_name} - {e}")
            else:
                print(f"効果音ファイルが見つかりません: {sound_path}")
    
    def handle_keydown(self, key):
        """キーが押された時の処理"""
        # キーコンフィグ画面でキー入力待ち状態の場合
        if self.state == GameState.KEY_CONFIG and self.waiting_for_key_input:
            self.waiting_for_key_input = False
            action = self.key_config_items[self.key_config_selected_item]
            
            # プレイヤー1のキーマッピング更新
            if self.key_config_player == 1:
                # 既に割り当てられているキーを削除
                for k, v in list(KEY_MAPPING_P1.items()):
                    if v == action:
                        del KEY_MAPPING_P1[k]
                # 新しいキーを割り当て
                KEY_MAPPING_P1[key] = action
                # 互換性のために古いマッピングも更新
                KEY_MAPPING.clear()
                KEY_MAPPING.update(KEY_MAPPING_P1)
                print(f"P1キーマッピング更新: {key} -> {action}")
                print(f"現在のKEY_MAPPING_P1: {KEY_MAPPING_P1}")
                print(f"現在のKEY_MAPPING: {KEY_MAPPING}")
            # プレイヤー2のキーマッピング更新
            elif self.key_config_player == 2:
                # 既に割り当てられているキーを削除
                for k, v in list(KEY_MAPPING_P2.items()):
                    if v == action:
                        del KEY_MAPPING_P2[k]
                # 新しいキーを割り当て
                KEY_MAPPING_P2[key] = action
                print(f"P2キーマッピング更新: {key} -> {action}")
                print(f"現在のKEY_MAPPING_P2: {KEY_MAPPING_P2}")
            
            # 次の項目に移動
            self.key_config_selected_item = (self.key_config_selected_item + 1) % len(self.key_config_items)
            return
            
        # 通常のキー処理
        # プレイヤー1のキー処理
        p1_action = None
        if key in KEY_MAPPING_P1:
            p1_action = KEY_MAPPING_P1[key]
            self.keys_pressed[p1_action] = True
            print(f"P1キー押下: {key} -> {p1_action}")
        
        # プレイヤー2のキー処理を追加（ゲーム画面の時のみ）
        p2_action = None
        if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
            if key in KEY_MAPPING_P2:
                # ゲーム中はトレーニングモードなどの時にプレイヤー2を操作可能にする
                # player2の更新は通常AIが行うが、キー入力があれば手動操作も可能
                p2_action = KEY_MAPPING_P2[key]
                print(f"P2キー押下: {key} -> {p2_action}")
        
        # タイトル画面やメニュー操作はプレイヤー1のキーで行う
        action = p1_action
            
        # タイトル画面の処理
        if self.state == GameState.TITLE:
            if action == "up" or action == "down":
                # メニュー移動音を再生
                if "menu" in self.sounds:
                    self.sounds["menu"].play()
                if action == "up":
                    self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                else:
                    self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif action == "left" and self.menu_items[self.selected_item] == "自動テスト":
                # メニュー移動音を再生
                if "menu" in self.sounds:
                    self.sounds["menu"].play()
                # 自動テストが選択されているときは左右キーでテスト時間を選択
                self.selected_test_time = (self.selected_test_time - 1) % len(self.test_time_options)
            elif action == "right" and self.menu_items[self.selected_item] == "自動テスト":
                # メニュー移動音を再生
                if "menu" in self.sounds:
                    self.sounds["menu"].play()
                # 自動テストが選択されているときは左右キーでテスト時間を選択
                self.selected_test_time = (self.selected_test_time + 1) % len(self.test_time_options)
            elif action == "weapon_a":  # 決定ボタン
                # 決定音を再生
                if "special" in self.sounds:
                    self.sounds["special"].play()
                if self.menu_items[self.selected_item] == "対戦モード":
                    self.state = GameState.GAME
                    # プレイヤーのリセット
                    self.reset_players()
                elif self.menu_items[self.selected_item] == "トレーニングモード":
                    self.state = GameState.TRAINING
                    # プレイヤーのリセット
                    self.reset_players()
                elif self.menu_items[self.selected_item] == "自動テスト":
                    self.state = GameState.AUTO_TEST
                    self.test_timer = 0  # タイマーリセット
                    
                    # 選択されたテスト時間に基づいてdurationを設定
                    if self.test_time_options[self.selected_test_time] == "5秒":
                        self.test_duration = 60 * 5
                    elif self.test_time_options[self.selected_test_time] == "30秒":
                        self.test_duration = 60 * 30
                    elif self.test_time_options[self.selected_test_time] == "勝負がつくまで":
                        self.test_duration = float('inf')  # 無限大を設定
                        
                    # プレイヤーのリセット
                    self.reset_players()
                elif self.menu_items[self.selected_item] == "操作説明":
                    self.state = GameState.CONTROLS
                elif self.menu_items[self.selected_item] == "オプション":
                    self.state = GameState.OPTIONS
                elif self.menu_items[self.selected_item] == "終了":
                    pygame.quit()
                    sys.exit()
        # 操作説明画面の処理
        elif self.state == GameState.CONTROLS:
            if action == "weapon_a" or action == "weapon_b":  # 決定または戻るボタン
                if hasattr(self, 'previous_state') and self.previous_state == GameState.PAUSE:
                    self.state = GameState.PAUSE
                else:
                    self.state = GameState.TITLE
        # ポーズメニューの処理
        elif self.state == GameState.PAUSE:
            if action == "up" or action == "down":
                # メニュー移動音を再生
                if "menu" in self.sounds:
                    self.sounds["menu"].play()
                if action == "up":
                    self.pause_selected_item = (self.pause_selected_item - 1) % len(self.pause_menu_items)
                else:
                    self.pause_selected_item = (self.pause_selected_item + 1) % len(self.pause_menu_items)
            elif action == "weapon_a":  # 決定ボタン
                # 決定音を再生
                if "special" in self.sounds:
                    self.sounds["special"].play()
                if self.pause_menu_items[self.pause_selected_item] == "ゲームに戻る":
                    self.state = self.previous_state
                elif self.pause_menu_items[self.pause_selected_item] == "操作説明":
                    self.state = GameState.CONTROLS
                elif self.pause_menu_items[self.pause_selected_item] == "タイトルに戻る":
                    self.state = GameState.TITLE
        
        # オプション画面の処理
        elif self.state == GameState.OPTIONS:
            if action == "up" or action == "down":
                # メニュー移動音を再生
                if "menu" in self.sounds:
                    self.sounds["menu"].play()
                if action == "up":
                    self.option_selected_item = (self.option_selected_item - 1) % len(self.option_menu_items)
                else:
                    self.option_selected_item = (self.option_selected_item + 1) % len(self.option_menu_items)
            elif action == "weapon_a":  # 決定ボタン
                # 決定音を再生
                if "special" in self.sounds:
                    self.sounds["special"].play()
                if self.option_menu_items[self.option_selected_item] == "キーコンフィグ":
                    self.state = GameState.KEY_CONFIG
                    self.key_config_player = 1
                    self.key_config_selected_item = 0
                    self.waiting_for_key_input = False
                elif self.option_menu_items[self.option_selected_item] == "戻る":
                    self.state = GameState.TITLE
            elif action == "weapon_b":  # 戻るボタン
                # 決定音を再生
                if "special" in self.sounds:
                    self.sounds["special"].play()
                self.state = GameState.TITLE
        
        # キーコンフィグ画面の処理
        elif self.state == GameState.KEY_CONFIG:
            if not self.waiting_for_key_input:
                if action == "up":
                    self.key_config_selected_item = (self.key_config_selected_item - 1) % len(self.key_config_items)
                elif action == "down":
                    self.key_config_selected_item = (self.key_config_selected_item + 1) % len(self.key_config_items)
                elif action == "left" or action == "right":
                    # プレイヤー切り替え
                    self.key_config_player = 1 if self.key_config_player == 2 else 2
                elif action == "weapon_a":  # 決定ボタン
                    self.waiting_for_key_input = True
                elif action == "weapon_b":  # 戻るボタン
                    self.state = GameState.OPTIONS
                    self.save_key_config()  # 設定保存
                
                # デフォルト設定に戻すキー (Rキー)
                if key == pygame.K_r:
                    self.reset_key_config()
        
        # ESCキーでポーズ
        if key == pygame.K_ESCAPE:
            if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
                self.previous_state = self.state
                self.state = GameState.PAUSE
                self.pause_menu_items = ["ゲームに戻る", "操作説明", "タイトルに戻る"]
                self.pause_selected_item = 0
            elif self.state == GameState.PAUSE:
                self.state = self.previous_state  # 前の状態に戻る
            elif self.state == GameState.CONTROLS and hasattr(self, 'previous_state') and self.previous_state == GameState.PAUSE:
                self.state = GameState.PAUSE
            elif self.state == GameState.OPTIONS or self.state == GameState.KEY_CONFIG:
                self.state = GameState.TITLE
    
    def handle_keyup(self, key):
        """キーが離された時の処理"""
        # プレイヤー1のキー処理
        if key in KEY_MAPPING_P1:
            action = KEY_MAPPING_P1[key]
            self.keys_pressed[action] = False
            print(f"P1キー離し: {key} -> {action}")
        
        # プレイヤー2のキー処理を追加（ゲーム画面の時のみ）
        if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
            if key in KEY_MAPPING_P2:
                # 今はプレイヤー2のキーは使わないが、将来的に使うかもしれないので残しておく
                action = KEY_MAPPING_P2[key]
                print(f"P2キー離し: {key} -> {action}")
    
    def update(self):
        """ゲーム状態の更新"""
        self.current_time += 1
        
        if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
            # 現在の状態を保存（ポーズから戻るため）
            self.previous_state = self.state
            
            # アリーナの更新
            self.arena.update()
            
            if self.state == GameState.AUTO_TEST:
                # 自動テストモードの場合
                self.test_timer += 1
                
                # 「勝負がつくまで」以外の場合は時間制限でチェック
                if self.test_duration != float('inf') and self.test_timer >= self.test_duration:
                    # テスト終了、タイトルに戻る
                    self.state = GameState.TITLE
                    return
                
                # 「勝負がつくまで」の場合、どちらかのHPが0になったらタイトルに戻る
                if self.test_duration == float('inf') and (self.player1.health <= 0 or self.player2.health <= 0):
                    self.state = GameState.RESULT
                    self.result_timer = 0
                    self.winner = 2 if self.player1.health <= 0 else 1
                    # 3秒後に自動的にタイトル画面に戻る
                    return
                
                # AIの移動タイマーを更新
                self.ai_move_timer1 += 1
                self.ai_move_timer2 += 1
                
                # 両方のプレイヤーをAIで操作
                player1_keys = self.auto_test_ai_control(self.player1, self.player2, is_player1=True)
                player2_keys = self.auto_test_ai_control(self.player2, self.player1, is_player1=False)
                
                self.player1.update(player1_keys, self.arena, self.player2)
                self.player2.update(player2_keys, self.arena, self.player1)
            else:
                # 通常の対戦モードまたはトレーニングモード
                # プレイヤーの更新
                self.player1.update(self.keys_pressed, self.arena, self.player2)
                
                # トレーニングモードでは相手は簡単に動く
                if self.state == GameState.GAME:
                    # AIによる操作（簡易版）
                    ai_keys = self.simple_ai_control()
                    self.player2.update(ai_keys, self.arena, self.player1)
            
            # 弾の更新
            for proj in self.projectiles[:]:
                proj.update()
                if proj.is_dead:
                    self.projectiles.remove(proj)
            
            # 効果の更新
            for effect in self.effects[:]:
                effect.update()
                if effect.is_dead:
                    self.effects.remove(effect)
                    
            # 当たり判定処理
            self.handle_collisions()
            
            # HPチェック - 勝利判定（自動テストの「勝負がつくまで」以外で使用）
            if (self.state != GameState.AUTO_TEST or self.test_duration != float('inf')) and (self.player1.health <= 0 or self.player2.health <= 0):
                self.state = GameState.RESULT
                self.result_timer = 0
                self.winner = 2 if self.player1.health <= 0 else 1
                
                # トレーニングモードではHPが0になっても回復する
                if self.state == GameState.TRAINING:
                    if self.player1.health <= 0:
                        self.player1.health = MAX_HEALTH
                    if self.player2.health <= 0:
                        self.player2.health = MAX_HEALTH
    
    def auto_test_ai_control(self, player, opponent, is_player1=True):
        """自動テスト用の高度なAI制御 - 移動は3秒間隔で行う"""
        ai_keys = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # プレイヤーによって異なるタイマーと方向を使用
        ai_timer = self.ai_move_timer1 if is_player1 else self.ai_move_timer2
        ai_direction = self.ai_move_direction1 if is_player1 else self.ai_move_direction2
        
        # 弾道予測による回避行動を優先
        projectile_data = self.predict_projectile_collision(player)
        if projectile_data:
            # 弾が当たりそうな場合、横方向にダッシュして回避
            proj, time_to_hit, hit_x, hit_y = projectile_data
            
            # 弾の進行方向に対して垂直方向に回避
            # 弾の方向ベクトル
            proj_dir_x = math.cos(proj.angle)
            proj_dir_y = math.sin(proj.angle)
            
            # 垂直方向ベクトル（左側）
            perp_x = -proj_dir_y
            perp_y = proj_dir_x
            
            # プレイヤーが中心から離れすぎている場合、中心に近い方向を選ぶ
            arena_dx = ARENA_CENTER_X - player.x
            arena_dy = ARENA_CENTER_Y - player.y
            arena_distance = (arena_dx**2 + arena_dy**2)**0.5
            
            if arena_distance > ARENA_RADIUS * 0.7:
                # アリーナ中心への方向ベクトル
                to_center_x = arena_dx / (arena_distance or 1)
                to_center_y = arena_dy / (arena_distance or 1)
                
                # 2つの垂直方向のうち、中心に近づく方を選ぶ
                dot_product = to_center_x * perp_x + to_center_y * perp_y
                if dot_product < 0:  # 左側の垂直ベクトルが中心から遠ざかる場合
                    perp_x = -perp_x
                    perp_y = -perp_y
            else:
                # アリーナの中央付近では、ランダムな方向に回避
                if random.random() < 0.5:
                    perp_x = -perp_x
                    perp_y = -perp_y
            
            # 回避方向を設定
            ai_keys["right"] = perp_x > 0
            ai_keys["left"] = perp_x < 0
            ai_keys["down"] = perp_y > 0
            ai_keys["up"] = perp_y < 0
                
            # ダッシュで素早く回避
            ai_keys["dash"] = True
            
            # 近すぎる場合はシールドも使用
            if time_to_hit < 15:  # 15フレーム以内なら
                ai_keys["shield"] = random.random() < 0.7  # 70%の確率でシールド
                
            # 弾道回避のため移動タイマーをリセット
            if is_player1:
                self.ai_move_timer1 = 0
                self.ai_move_direction1 = {
                    "up": ai_keys["up"],
                    "down": ai_keys["down"],
                    "left": ai_keys["left"],
                    "right": ai_keys["right"],
                    "dash": ai_keys["dash"]
                }
            else:
                self.ai_move_timer2 = 0
                self.ai_move_direction2 = {
                    "up": ai_keys["up"],
                    "down": ai_keys["down"],
                    "left": ai_keys["left"],
                    "right": ai_keys["right"],
                    "dash": ai_keys["dash"]
                }
                
            return ai_keys
            
        # 3秒ごとに移動方向を再決定
        if ai_timer >= self.ai_move_interval:
            # 移動スタイルをランダムに決定
            self.decide_movement_style(player, opponent, is_player1)
            
            # タイマーをリセット
            if is_player1:
                self.ai_move_timer1 = 0
            else:
                self.ai_move_timer2 = 0
        
        # 保存された移動方向を使用
        ai_keys["up"] = ai_direction["up"]
        ai_keys["down"] = ai_direction["down"]
        ai_keys["left"] = ai_direction["left"]
        ai_keys["right"] = ai_direction["right"]
        ai_keys["dash"] = ai_direction["dash"]
        
        # 攻撃
        if random.random() < 0.4:  # 40%の確率で攻撃A
            ai_keys["weapon_a"] = True
        if random.random() < 0.3:  # 30%の確率で攻撃B
            ai_keys["weapon_b"] = True
            
        # スペシャル
        if random.random() < 0.1:
            ai_keys["special"] = True
            
        # シールド - 敵の弾が近づいたらシールドを張る確率上昇
        shield_chance = 0.1  # 基本は10%
        if self.is_projectile_nearby(player, 70):
            shield_chance = 0.7  # 弾が近くにあれば70%
        ai_keys["shield"] = random.random() < shield_chance
            
        # ハイパー
        if player.hyper_gauge >= 100 and random.random() < 0.3:
            ai_keys["hyper"] = True
            
        return ai_keys
    
    def decide_movement_style(self, player, opponent, is_player1):
        """移動スタイルを決定する（3秒ごとに呼ばれる）"""
        # プレイヤーとの距離を計算
        dx = opponent.x - player.x
        dy = opponent.y - player.y
        distance = (dx**2 + dy**2)**0.5
        
        # アリーナの中心からの距離
        arena_dx = ARENA_CENTER_X - player.x
        arena_dy = ARENA_CENTER_Y - player.y
        (arena_dx**2 + arena_dy**2)**0.5
        
        # 移動方向の初期化
        movement = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "dash": random.random() < 0.4  # 40%の確率でダッシュを使用
        }
        
        move_style = random.randint(0, 10)  # 0-10の範囲で移動スタイルを決定
        
        if move_style <= 5:  # 50%の確率で相手との距離に基づいた動き
            if distance > 150:
                # 近づく
                movement["right"] = dx > 0
                movement["left"] = dx < 0
                movement["down"] = dy > 0
                movement["up"] = dy < 0
            else:
                # 距離を取る
                movement["left"] = dx > 0
                movement["right"] = dx < 0
                movement["up"] = dy > 0
                movement["down"] = dy < 0
        elif move_style <= 7:  # 20%の確率で円運動（相手の周りを回る）
            # 相手を中心に時計回りまたは反時計回りに動く
            clockwise = random.random() < 0.5
            
            if clockwise:
                movement["left"] = dy > 0
                movement["right"] = dy < 0
                movement["up"] = dx > 0
                movement["down"] = dx < 0
            else:
                movement["left"] = dy < 0
                movement["right"] = dy > 0
                movement["up"] = dx < 0
                movement["down"] = dx > 0
        elif move_style <= 8:  # 10%の確率でアリーナの中心に向かう
            movement["right"] = arena_dx > 0
            movement["left"] = arena_dx < 0
            movement["down"] = arena_dy > 0
            movement["up"] = arena_dy < 0
        else:  # 20%の確率で完全ランダムな動き
            # 単一方向への移動を確実にするために、上下と左右からそれぞれ1つの方向を選ぶ
            vertical = random.choice(["up", "down", "none"])
            horizontal = random.choice(["left", "right", "none"])
            
            if vertical != "none":
                movement[vertical] = True
            if horizontal != "none":
                movement[horizontal] = True
                
            # もし方向が一つも選ばれていなければ、ランダムに1つ選ぶ
            if not any([movement["up"], movement["down"], movement["left"], movement["right"]]):
                random_dir = random.choice(["up", "down", "left", "right"])
                movement[random_dir] = True
        
        # プレイヤーに応じた方向を保存
        if is_player1:
            self.ai_move_direction1 = movement
        else:
            self.ai_move_direction2 = movement
    
    def predict_projectile_collision(self, player):
        """プレイヤーと弾の衝突予測"""
        closest_hit_time = float('inf')
        closest_projectile = None
        hit_position = None
        
        for proj in self.projectiles:
            if proj.owner == player:  # 自分の弾は無視
                continue
                
            # 弾の速度ベクトル
            proj_vx = math.cos(proj.angle) * proj.speed
            proj_vy = math.sin(proj.angle) * proj.speed
            
            # 弾とプレイヤーの相対位置
            dx = player.x - proj.x
            dy = player.y - proj.y
            
            # 衝突までの時間を計算
            # |P + Vt - C| = r
            # ここでPは弾の位置、Vは弾の速度ベクトル、tは時間、Cはプレイヤーの位置、rは衝突半径
            # 簡略化のために線形予測を使用
            
            # 相対速度で計算（プレイヤーは静止していると仮定）
            a = proj_vx * proj_vx + proj_vy * proj_vy  # |V|²
            b = 2 * (proj_vx * dx + proj_vy * dy)      # 2V・(P-C)
            c = dx * dx + dy * dy - (player.radius + proj.radius) * (player.radius + proj.radius)  # |P-C|² - r²
            
            # 判別式
            discriminant = b * b - 4 * a * c
            
            if discriminant >= 0 and a > 0:
                # 衝突する
                t1 = (-b - math.sqrt(discriminant)) / (2 * a)
                t2 = (-b + math.sqrt(discriminant)) / (2 * a)
                
                # 最も早い正の衝突時間を見つける
                hit_time = None
                if t1 > 0:
                    hit_time = t1
                elif t2 > 0:
                    hit_time = t2
                
                if hit_time is not None and hit_time < closest_hit_time and hit_time < 60:  # 60フレーム以内の衝突のみ考慮
                    closest_hit_time = hit_time
                    closest_projectile = proj
                    # 衝突位置を計算
                    hit_x = proj.x + proj_vx * hit_time
                    hit_y = proj.y + proj_vy * hit_time
                    hit_position = (hit_x, hit_y)
        
        if closest_projectile and hit_position:
            return (closest_projectile, closest_hit_time, hit_position[0], hit_position[1])
        return None
    
    def is_projectile_nearby(self, player, distance_threshold):
        """プレイヤーの近くに弾があるかチェック"""
        for proj in self.projectiles:
            if proj.owner != player:  # 自分の弾ではない
                dx = player.x - proj.x
                dy = player.y - proj.y
                distance = (dx**2 + dy**2)**0.5
                if distance < distance_threshold:
                    return True
        return False
    
    def simple_ai_control(self):
        """簡易的なAI制御"""
        ai_keys = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # プレイヤーとの距離を計算
        dx = self.player1.x - self.player2.x
        dy = self.player1.y - self.player2.y
        distance = (dx**2 + dy**2)**0.5
        
        # 距離に応じた行動
        if distance > 150:
            # 近づく
            if dx > 0:
                ai_keys["right"] = True
            else:
                ai_keys["left"] = True
                
            if dy > 0:
                ai_keys["down"] = True
            else:
                ai_keys["up"] = True
                
            # たまに攻撃
            if self.current_time % 60 == 0:
                ai_keys["weapon_a"] = True
        else:
            # 距離を取る
            if dx > 0:
                ai_keys["left"] = True
            else:
                ai_keys["right"] = True
                
            if dy > 0:
                ai_keys["up"] = True
            else:
                ai_keys["down"] = True
                
            # 攻撃
            if self.current_time % 30 == 0:
                ai_keys["weapon_a"] = True
            if self.current_time % 90 == 0:
                ai_keys["weapon_b"] = True
                
            # たまにダッシュ
            if self.current_time % 120 == 0:
                ai_keys["dash"] = True
                
            # ハイパーゲージが溜まったら使用
            if self.player2.hyper_gauge >= 100 and self.current_time % 180 == 0:
                ai_keys["hyper"] = True
                
        return ai_keys
        
    def handle_collisions(self):
        """衝突判定処理"""
        # プレイヤーと弾の衝突判定
        for proj in self.projectiles[:]:
            # プレイヤー1との衝突
            if proj.owner != self.player1 and self.player1.collides_with(proj):
                damage = proj.damage
                # ヒートに応じてダメージ増加
                if not self.player1.is_shielding():
                    damage = damage * (1 + self.player1.heat / 100)
                    self.player1.take_damage(damage)
                    proj.on_hit(self.player1)
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                else:
                    # シールド中は弾を反射
                    proj.reflect(self.player1)
                    
            # プレイヤー2との衝突
            elif proj.owner != self.player2 and self.player2.collides_with(proj):
                damage = proj.damage
                # ヒートに応じてダメージ増加
                if not self.player2.is_shielding():
                    damage = damage * (1 + self.player2.heat / 100)
                    self.player2.take_damage(damage)
                    proj.on_hit(self.player2)
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                else:
                    # シールド中は弾を反射
                    proj.reflect(self.player2)
    
    def draw(self):
        """描画処理 - ズーム機能付き"""
        if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
            # プレイヤー間の距離を計算
            dx = self.player1.x - self.player2.x
            dy = self.player1.y - self.player2.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 距離に基づいてズーム率を計算
            min_distance = 150  # これ以下の距離では最大ズーム
            max_distance = 400  # これ以上の距離では最小ズーム
            max_zoom = 1.5      # 最大ズーム率
            min_zoom = 1.0      # 最小ズーム率（0.8から1.0に変更）
            
            # 目標ズーム率の計算
            if distance <= min_distance:
                self.target_zoom = max_zoom
            elif distance >= max_distance:
                self.target_zoom = min_zoom
            else:
                # 線形補間でズーム率を決定
                ratio = (distance - min_distance) / (max_distance - min_distance)
                self.target_zoom = max_zoom - ratio * (max_zoom - min_zoom)
            
            # 現在のズーム率を目標値に徐々に近づける（スムージング）
            self.current_zoom = self.current_zoom * 0.95 + self.target_zoom * 0.05
            
            # バックバッファを作成
            buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            buffer.fill((0, 0, 0))  # 黒で初期化
            
            # アリーナの描画（バッファに）
            self.arena.draw(buffer)
            
            # プレイヤーと弾、エフェクトの描画（バッファに）
            for proj in self.projectiles:
                proj.draw(buffer)
            
            self.player1.draw(buffer)
            self.player2.draw(buffer)
            
            for effect in self.effects:
                effect.draw(buffer)
            
            # プレイヤーの中間点を計算
            center_x = (self.player1.x + self.player2.x) / 2
            center_y = (self.player1.y + self.player2.y) / 2
            
            # ズーム後のサイズを計算
            int(SCREEN_WIDTH * self.current_zoom)
            int(SCREEN_HEIGHT * self.current_zoom)
            
            # ズーム中心点からの切り出し位置を計算
            clip_x = int(center_x - SCREEN_WIDTH / (2 * self.current_zoom))
            clip_y = int(center_y - SCREEN_HEIGHT / (2 * self.current_zoom))
            
            # 切り出し位置がスクリーン範囲内に収まるよう調整
            if clip_x < 0:
                clip_x = 0
            if clip_y < 0:
                clip_y = 0
            if clip_x + int(SCREEN_WIDTH / self.current_zoom) > SCREEN_WIDTH:
                clip_x = max(0, SCREEN_WIDTH - int(SCREEN_WIDTH / self.current_zoom))
            if clip_y + int(SCREEN_HEIGHT / self.current_zoom) > SCREEN_HEIGHT:
                clip_y = max(0, SCREEN_HEIGHT - int(SCREEN_HEIGHT / self.current_zoom))
            
            # 切り出しサイズがスクリーンを超えないよう調整
            clip_width = min(int(SCREEN_WIDTH / self.current_zoom), SCREEN_WIDTH - clip_x)
            clip_height = min(int(SCREEN_HEIGHT / self.current_zoom), SCREEN_HEIGHT - clip_y)
            
            # バッファから領域を切り出し
            try:
                clip_area = pygame.Rect(clip_x, clip_y, clip_width, clip_height)
                clipped_buffer = buffer.subsurface(clip_area)
                
                # 切り出した領域をズーム
                zoomed_width = int(clip_width * self.current_zoom)
                zoomed_height = int(clip_height * self.current_zoom)
                zoomed_buffer = pygame.transform.scale(clipped_buffer, (zoomed_width, zoomed_height))
                
                # メイン画面クリア
                self.screen.fill((0, 0, 0))
                
                # ズームした画像をスクリーンの中央に配置
                dest_x = int(SCREEN_WIDTH/2 - zoomed_width/2)
                dest_y = int(SCREEN_HEIGHT/2 - zoomed_height/2)
                self.screen.blit(zoomed_buffer, (dest_x, dest_y))
            except ValueError:
                # 切り出し範囲が不正な場合はバックアップとしてそのまま描画
                print("ズームエラー: 切り出し範囲が不正です。通常描画に切り替えます。")
                self.screen.blit(buffer, (0, 0))
            
            # HUDは通常通り描画（ズームの影響を受けない）
            self.hud.draw(self.screen)
            
            # 自動テストモードの情報表示
            if self.state == GameState.AUTO_TEST:
                test_font = pygame.font.SysFont(self.font_name, 24)
                
                if self.test_duration == float('inf'):
                    test_text = test_font.render("自動テスト中: 勝負がつくまで", True, YELLOW)
                else:
                    remaining_seconds = (self.test_duration - self.test_timer) // 60
                    test_text = test_font.render(f"自動テスト中: あと{remaining_seconds}秒", True, YELLOW)
                
                test_rect = test_text.get_rect(center=(SCREEN_WIDTH//2, 50))
                self.screen.blit(test_text, test_rect)
        elif self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.CONTROLS:
            self.draw_controls_screen()
        elif self.state == GameState.PAUSE:
            # ポーズ時のゲーム描画
            # ゲーム画面をバックグラウンドに描画
            self.arena.draw(self.screen)
            for proj in self.projectiles:
                proj.draw(self.screen)
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            for effect in self.effects:
                effect.draw(self.screen)
            self.hud.draw(self.screen)
            
            # 半透明のオーバーレイ
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # 半透明の黒
            self.screen.blit(overlay, (0, 0))
            
            # ポーズメニューを描画
            self.draw_pause_menu()
        elif self.state == GameState.RESULT:
            # リザルト画面
            # ゲーム画面を描画（バックグラウンド）
            self.arena.draw(self.screen)
            for proj in self.projectiles:
                proj.draw(self.screen)
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            for effect in self.effects:
                effect.draw(self.screen)
            self.hud.draw(self.screen)
            
            # 結果画面を描画
            self.draw_result_screen()
        elif self.state == GameState.OPTIONS:
            # オプション画面
            # タイトル
            title_font = pygame.font.SysFont(self.hud.font_name, 48)
            title_text = title_font.render("オプション", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(title_text, title_rect)
            
            # メニュー項目
            menu_font = pygame.font.SysFont(self.hud.font_name, 36)
            for i, item in enumerate(self.option_menu_items):
                color = YELLOW if i == self.option_selected_item else WHITE
                text = menu_font.render(item, True, color)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 60))
                self.screen.blit(text, rect)
        elif self.state == GameState.KEY_CONFIG:
            # キーコンフィグ画面
            # タイトル
            title_font = pygame.font.SysFont(self.font_name, 48)
            title_text = title_font.render(f"キーコンフィグ (プレイヤー{self.key_config_player})", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(title_text, title_rect)
            
            # 操作説明
            instruction_font = pygame.font.SysFont(self.font_name, 24)
            instruction_text = instruction_font.render("←→キーでプレイヤー切り替え、Zキーで設定、Xキーで戻る", True, WHITE)
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(instruction_text, instruction_rect)
            
            # リセット操作の説明
            reset_text = instruction_font.render("Rキーでデフォルト設定に戻す", True, YELLOW)
            reset_rect = reset_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
            self.screen.blit(reset_text, reset_rect)
            
            # キーマッピング一覧
            menu_font = pygame.font.SysFont(self.font_name, 30)
            current_mapping = KEY_MAPPING_P1 if self.key_config_player == 1 else KEY_MAPPING_P2
            
            for i, action in enumerate(self.key_config_items):
                # 操作名
                action_name = ACTION_NAMES[action]
                color = YELLOW if i == self.key_config_selected_item else WHITE
                
                # キー名を探す
                key_name = "未設定"
                for k, v in current_mapping.items():
                    if v == action:
                        key_name = KEY_NAMES.get(k, str(k))
                        
                # 入力待ち状態の表示
                if i == self.key_config_selected_item and self.waiting_for_key_input:
                    key_name = "キー入力待ち..."
                
                # 表示テキスト
                text = f"{action_name}: {key_name}"
                text_render = menu_font.render(text, True, color)
                rect = text_render.get_rect(midleft=(SCREEN_WIDTH // 4, 150 + i * 40))
                self.screen.blit(text_render, rect)
                
            # ナビゲーション
            nav_font = pygame.font.SysFont(self.font_name, 24)
            nav_text = nav_font.render("設定を保存するには戻るボタン(X)を押してください", True, GRAY)
            nav_rect = nav_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
            self.screen.blit(nav_text, nav_rect)
    
    def draw_title_screen(self):
        """タイトル画面の描画"""
        # タイトルテキスト
        title_font = pygame.font.SysFont(self.font_name, 64)
        title_text = title_font.render("アクセラレーションオブ豆腐", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title_text, title_rect)
        
        # メニューアイテム
        menu_font = pygame.font.SysFont(self.font_name, 36)
        for i, item in enumerate(self.menu_items):
            color = YELLOW if i == self.selected_item else WHITE
            item_text = menu_font.render(item, True, color)
            item_rect = item_text.get_rect(center=(SCREEN_WIDTH//2, 300 + i * 50))
            self.screen.blit(item_text, item_rect)
            
            # 自動テストが選択されているときはテスト時間も表示
            if item == "自動テスト" and i == self.selected_item:
                time_option = self.test_time_options[self.selected_test_time]
                option_font = pygame.font.SysFont(self.font_name, 24)
                option_text = option_font.render(f"◀ {time_option} ▶", True, CYAN)
                option_rect = option_text.get_rect(center=(SCREEN_WIDTH//2, 300 + i * 50 + 30))
                self.screen.blit(option_text, option_rect)
            
        # 操作ガイド
        guide_font = pygame.font.SysFont(self.font_name, 24)
        if self.selected_item == self.menu_items.index("自動テスト"):
            guide_text = guide_font.render("↑/↓: 選択  ←/→: 時間設定  Z: 決定", True, WHITE)
        else:
            guide_text = guide_font.render("↑/↓: 選択  Z: 決定", True, WHITE)
        guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        self.screen.blit(guide_text, guide_rect)
    
    def draw_controls_screen(self):
        """操作説明画面の描画"""
        # 背景
        self.screen.fill((30, 30, 50))
        
        # タイトル
        title_font = pygame.font.SysFont(self.font_name, 48)
        title_text = title_font.render("操作説明", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # キー説明
        key_font = pygame.font.SysFont(self.font_name, 28)
        key_explanations = [
            "移動: 矢印キー (↑↓←→)",
            "攻撃A: Z",
            "攻撃B: X",
            "ダッシュ: 左シフト",
            "ハイパーモード（レーザー）: スペース",
            "シールド: S",
            "スペシャル技: A + X (スプレッド弾)"
        ]
        
        for i, explanation in enumerate(key_explanations):
            text = key_font.render(explanation, True, WHITE)
            rect = text.get_rect(midleft=(SCREEN_WIDTH//3, 180 + i * 50))
            self.screen.blit(text, rect)
        
        # 戻る方法
        guide_font = pygame.font.SysFont(self.font_name, 24)
        guide_text = guide_font.render("Zキーまたはキーを押して戻る", True, YELLOW)
        guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        self.screen.blit(guide_text, guide_rect)
        
        # キーの動作説明
        action_font = pygame.font.SysFont(self.font_name, 24)
        action_texts = [
            "ダッシュ: 押している間、高速移動できます。連続使用不可（クールダウンあり）",
            "ハイパーモード: ゲージを消費して一時的に能力強化",
            "シールド: 押している間、攻撃を防御・反射します",
            "スペシャル技: A + X で広範囲攻撃（スプレッド弾）を放ちます"
        ]
        
        for i, action in enumerate(action_texts):
            text = action_font.render(action, True, CYAN)
            rect = text.get_rect(midleft=(SCREEN_WIDTH//6, 480 + i * 35))
            self.screen.blit(text, rect)
    
    def draw_pause_menu(self):
        """ポーズメニューの描画"""
        # ポーズテキスト
        pause_font = pygame.font.SysFont(self.font_name, 48)
        pause_text = pause_font.render("ポーズ", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(pause_text, pause_rect)
        
        # メニューアイテム
        menu_font = pygame.font.SysFont(self.font_name, 36)
        for i, item in enumerate(self.pause_menu_items):
            color = YELLOW if i == self.pause_selected_item else WHITE
            item_text = menu_font.render(item, True, color)
            item_rect = item_text.get_rect(center=(SCREEN_WIDTH//2, 300 + i * 50))
            self.screen.blit(item_text, item_rect)
            
        # 操作ガイド
        guide_font = pygame.font.SysFont(self.font_name, 24)
        guide_text = guide_font.render("↑/↓: 選択  Z: 決定  ESC: 戻る", True, WHITE)
        guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
        self.screen.blit(guide_text, guide_rect)
    
    def add_projectile(self, projectile):
        """弾を追加"""
        self.projectiles.append(projectile)
        
    def add_effect(self, effect):
        """エフェクトを追加"""
        self.effects.append(effect)
    
    def draw_result_screen(self):
        """結果画面を描画"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 半透明の黒
        self.screen.blit(overlay, (0, 0))
        
        # リザルトタイマーを更新
        self.result_timer += 1
        
        # 3秒後にタイトルに戻る
        if self.result_timer > 180:  # 3秒 = 180フレーム (60FPS)
            self.state = GameState.TITLE
            return
        
        # 勝者の表示
        result_font = pygame.font.SysFont(self.font_name, 72)
        winner_text = f"プレイヤー{self.winner}の勝利！"
        result_text = result_font.render(winner_text, True, YELLOW)
        result_rect = result_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(result_text, result_rect)
        
        # 時間のカウントダウン
        time_font = pygame.font.SysFont(self.font_name, 36)
        time_left = 3 - self.result_timer // 60
        time_text = time_font.render(f"{time_left+1}秒後にタイトルに戻ります...", True, WHITE)
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(time_text, time_rect)
    
    def reset_players(self):
        """プレイヤーの状態をリセット"""
        self.player1.health = MAX_HEALTH
        self.player1.heat = 0
        self.player1.hyper_gauge = 0
        self.player1.is_hyper_active = False
        self.player1.x = ARENA_CENTER_X - 100
        self.player1.y = ARENA_CENTER_Y
        
        self.player2.health = MAX_HEALTH
        self.player2.heat = 0
        self.player2.hyper_gauge = 0
        self.player2.is_hyper_active = False
        self.player2.x = ARENA_CENTER_X + 100
        self.player2.y = ARENA_CENTER_Y
        
        # 残っている弾や効果をクリア
        self.projectiles.clear()
        self.effects.clear()
        
        # AIの移動タイマーもリセット
        self.ai_move_timer1 = 0
        self.ai_move_timer2 = 0
        self.ai_move_direction1 = {"up": False, "down": False, "left": False, "right": False, "dash": False}
        self.ai_move_direction2 = {"up": False, "down": False, "left": False, "right": False, "dash": False} 
    
    def save_key_config(self):
        """キーコンフィグ設定を保存"""
        print("\n=== キーコンフィグ保存開始 ===")
        try:
            # 許可されているキーのみを保存
            p1_config = {}
            p2_config = {}
            
            for k, v in KEY_MAPPING_P1.items():
                p1_config[str(k)] = v
            
            for k, v in KEY_MAPPING_P2.items():
                p2_config[str(k)] = v
            
            config = {
                "p1": p1_config,
                "p2": p2_config
            }
            
            with open("key_config.json", "w") as f:
                json.dump(config, f, indent=4)
            
            print(f"キーコンフィグを保存しました: P1={len(p1_config)}個, P2={len(p2_config)}個")
            print("=== キーコンフィグ保存完了 ===\n")
            return True
        except Exception as e:
            print(f"設定の保存に失敗しました: {e}")
            import traceback
            print(traceback.format_exc())
            print("=== キーコンフィグ保存失敗 ===\n")
            return False
    
    def load_key_config(self):
        """キーコンフィグ設定を読み込み"""
        # ログ出力のヘッダー
        print("\n=== キーコンフィグ読み込み開始 ===")
        
        # 使用可能なキーのリスト（制限付き）
        ALLOWED_KEYS = [
            # 矢印キー
            pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
            
            # アルファベットキー（a-z）
            pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e, 
            pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j,
            pygame.K_k, pygame.K_l, pygame.K_m, pygame.K_n, pygame.K_o,
            pygame.K_p, pygame.K_q, pygame.K_r, pygame.K_s, pygame.K_t,
            pygame.K_u, pygame.K_v, pygame.K_w, pygame.K_x, pygame.K_y, pygame.K_z,
            
            # 数字キー（メインキーボード上部）
            pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
            
            # テンキー
            pygame.K_KP0, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4,
            pygame.K_KP5, pygame.K_KP6, pygame.K_KP7, pygame.K_KP8, pygame.K_KP9,
            pygame.K_KP_PLUS, pygame.K_KP_MINUS, pygame.K_KP_MULTIPLY, pygame.K_KP_DIVIDE,
            
            # スペース
            pygame.K_SPACE,
            
            # 必要最小限の特殊キー
            pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_TAB,
            
            # 修飾キー
            pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT
        ]
        
        # 特殊キーは削除（シフト、コントロール、オルト、ファンクションキーなど）
        # pygame.K_LSHIFT, pygame.K_LCTRL, pygame.K_LALT, pygame.K_F1などは含まない
        
        # デフォルト値を先に設定
        # これにより、設定ファイルが存在しない場合や読み込みに失敗した場合でも
        # 必ずデフォルト値が使われるようになる
        global KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPING
        
        # デフォルト値を強制的に確実に設定
        KEY_MAPPING_P1 = DEFAULT_KEY_MAPPING_P1.copy()
        KEY_MAPPING_P2 = DEFAULT_KEY_MAPPING_P2.copy()
        KEY_MAPPING = KEY_MAPPING_P1.copy()
        
        print(f"デフォルト値を設定しました: P1={len(KEY_MAPPING_P1)}個, P2={len(KEY_MAPPING_P2)}個, KEY_MAPPING={len(KEY_MAPPING)}個")
        
        try:
            if os.path.exists("key_config.json"):
                with open("key_config.json", "r") as f:
                    config = json.load(f)
                
                print("設定ファイルを読み込みます...")
                
                # 有効な設定かチェック
                valid_config = True
                if "p1" not in config or not config["p1"]:
                    print("警告: p1の設定がないか空です。デフォルト設定を使用します。")
                    valid_config = False
                
                if "p2" not in config or not config["p2"]:
                    print("警告: p2の設定がないか空です。デフォルト設定を使用します。")
                    valid_config = False
                
                if valid_config:
                    # 一時変数に設定を読み込み
                    p1_settings = {}
                    p2_settings = {}
                    
                    # P1の設定読み込み
                    error_count = 0
                    for k, v in config["p1"].items():
                        try:
                            key_int = int(k)
                            # キーが許可リストに含まれているか確認
                            if key_int in ALLOWED_KEYS:
                                p1_settings[key_int] = v
                            else:
                                print(f"警告: キー {key_int} は許可されていないためスキップします")
                                error_count += 1
                        except (ValueError, TypeError) as e:
                            error_count += 1
                            if error_count <= 3:  # 最初の3つのエラーのみ表示
                                print(f"警告: 不正なキー値 '{k}' をスキップします: {e}")
                    
                    # P2の設定読み込み
                    error_count = 0
                    for k, v in config["p2"].items():
                        try:
                            key_int = int(k)
                            # キーが許可リストに含まれているか確認
                            if key_int in ALLOWED_KEYS:
                                p2_settings[key_int] = v
                            else:
                                print(f"警告: キー {key_int} は許可されていないためスキップします")
                                error_count += 1
                        except (ValueError, TypeError) as e:
                            error_count += 1
                            if error_count <= 3:
                                print(f"警告: 不正なキー値 '{k}' をスキップします: {e}")
                    
                    # 設定の検証 - 必要な全アクションが含まれているか
                    all_actions = set(ACTION_NAMES.keys())
                    
                    p1_actions = set(p1_settings.values())
                    p2_actions = set(p2_settings.values())
                    
                    missing_p1 = all_actions - p1_actions
                    missing_p2 = all_actions - p2_actions
                    
                    if missing_p1:
                        print(f"警告: P1の設定に{', '.join(missing_p1)}アクションがありません。デフォルト設定で補完します。")
                        for action in missing_p1:
                            for k, v in DEFAULT_KEY_MAPPING_P1.items():
                                if v == action and k not in p1_settings and k in ALLOWED_KEYS:
                                    p1_settings[k] = action
                                    break
                    
                    if missing_p2:
                        print(f"警告: P2の設定に{', '.join(missing_p2)}アクションがありません。デフォルト設定で補完します。")
                        for action in missing_p2:
                            for k, v in DEFAULT_KEY_MAPPING_P2.items():
                                if v == action and k not in p2_settings and k in ALLOWED_KEYS:
                                    p2_settings[k] = action
                                    break
                    
                    # 設定が有効ならグローバル変数を更新
                    if p1_settings:
                        KEY_MAPPING_P1.clear()
                        KEY_MAPPING_P1.update(p1_settings)
                        print(f"P1の設定を{len(KEY_MAPPING_P1)}個読み込みました")
                    
                    if p2_settings:
                        KEY_MAPPING_P2.clear()
                        KEY_MAPPING_P2.update(p2_settings)
                        print(f"P2の設定を{len(KEY_MAPPING_P2)}個読み込みました")
                    
                    # 互換性のためのKEY_MAPPINGを更新（重要: ここでP1の設定をコピー）
                    KEY_MAPPING.clear()  
                    KEY_MAPPING.update(KEY_MAPPING_P1)  # P1の設定をコピー
                    
                    # 確認
                    if len(KEY_MAPPING) > 0:
                        print(f"KEY_MAPPINGを{len(KEY_MAPPING)}個の設定で更新しました")
                    else:
                        print("警告: KEY_MAPPINGが空です")
                        # 空の場合は再度コピーを試みる
                        KEY_MAPPING = KEY_MAPPING_P1.copy()
                        print(f"KEY_MAPPINGを再度更新: {len(KEY_MAPPING)}個")
                
                print("キーコンフィグを読み込みました")
            else:
                print("設定ファイルが存在しません。デフォルト設定を使用します。")
        except Exception as e:
            print(f"設定の読み込みに失敗しました: {e}")
            print("デフォルト設定を使用します。")
            import traceback
            print(traceback.format_exc())
            
            # エラー時はデフォルト値に戻す（念のため）
            KEY_MAPPING_P1 = DEFAULT_KEY_MAPPING_P1.copy()
            KEY_MAPPING_P2 = DEFAULT_KEY_MAPPING_P2.copy()
            KEY_MAPPING = KEY_MAPPING_P1.copy()
        
        # 最終確認 - 重要なキーマッピングの状態をデバッグ出力
        print(f"最終的なキーマッピング: P1={len(KEY_MAPPING_P1)}個, P2={len(KEY_MAPPING_P2)}個, KEY_MAPPING={len(KEY_MAPPING)}個")
        
        # もし最終的にも空なら強制的にデフォルト値に戻す
        if len(KEY_MAPPING_P1) == 0:
            print("警告: P1のキーマッピングが空のままです。デフォルト値を強制適用します。")
            KEY_MAPPING_P1 = DEFAULT_KEY_MAPPING_P1.copy()
            
        if len(KEY_MAPPING) == 0:
            print("警告: KEY_MAPPINGが空のままです。P1の設定を強制適用します。")
            KEY_MAPPING = KEY_MAPPING_P1.copy()
            
        print("=== キーコンフィグ読み込み完了 ===\n") 

    def reset_key_config(self):
        """キー設定をデフォルトに戻す"""
        print("キーコンフィグをデフォルト設定に戻します")
        
        if self.key_config_player == 1:
            # プレイヤー1の設定をリセット
            KEY_MAPPING_P1.clear()
            KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
            # 互換性のためKEY_MAPPINGも更新
            KEY_MAPPING.clear()
            KEY_MAPPING.update(KEY_MAPPING_P1)
            print("プレイヤー1のキー設定をデフォルトに戻しました")
        else:
            # プレイヤー2の設定をリセット
            KEY_MAPPING_P2.clear()
            KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
            print("プレイヤー2のキー設定をデフォルトに戻しました")
        
        # 設定を保存
        self.save_key_config() 
    
    def draw_to_surface(self, surface):
        """指定されたサーフェスにゲーム画面を描画する
        これは背景として使用するためのメソッド"""
        if self.state == GameState.GAME or self.state == GameState.TRAINING or self.state == GameState.AUTO_TEST:
            # プレイヤー間の距離を計算
            dx = self.player1.x - self.player2.x
            dy = self.player1.y - self.player2.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 距離に基づいてズーム率を計算
            min_distance = 150  # これ以下の距離では最大ズーム
            max_distance = 400  # これ以上の距離では最小ズーム
            max_zoom = 1.5      # 最大ズーム率
            min_zoom = 1.0      # 最小ズーム率
            
            # 目標ズーム率の計算
            if distance <= min_distance:
                target_zoom = max_zoom
            elif distance >= max_distance:
                target_zoom = min_zoom
            else:
                # 線形補間でズーム率を決定
                ratio = (distance - min_distance) / (max_distance - min_distance)
                target_zoom = max_zoom - ratio * (max_zoom - min_zoom)
            
            # スムージングなしでターゲットズームを直接使用（背景用）
            current_zoom = target_zoom
            
            # バックバッファを作成
            buffer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            buffer.fill((0, 0, 0))  # 黒で初期化
            
            # アリーナの描画（バッファに）
            self.arena.draw(buffer)
            
            # プレイヤーと弾、エフェクトの描画（バッファに）
            for proj in self.projectiles:
                proj.draw(buffer)
            
            self.player1.draw(buffer)
            self.player2.draw(buffer)
            
            for effect in self.effects:
                effect.draw(buffer)
            
            # プレイヤーの中間点を計算
            center_x = (self.player1.x + self.player2.x) / 2
            center_y = (self.player1.y + self.player2.y) / 2
            
            # ズーム後のサイズを計算
            int(SCREEN_WIDTH * current_zoom)
            int(SCREEN_HEIGHT * current_zoom)
            
            # ズーム中心点からの切り出し位置を計算
            clip_x = int(center_x - SCREEN_WIDTH / (2 * current_zoom))
            clip_y = int(center_y - SCREEN_HEIGHT / (2 * current_zoom))
            
            # 切り出し位置がスクリーン範囲内に収まるよう調整
            if clip_x < 0:
                clip_x = 0
            if clip_y < 0:
                clip_y = 0
            if clip_x + int(SCREEN_WIDTH / current_zoom) > SCREEN_WIDTH:
                clip_x = max(0, SCREEN_WIDTH - int(SCREEN_WIDTH / current_zoom))
            if clip_y + int(SCREEN_HEIGHT / current_zoom) > SCREEN_HEIGHT:
                clip_y = max(0, SCREEN_HEIGHT - int(SCREEN_HEIGHT / current_zoom))
            
            # 切り出しサイズがスクリーンを超えないよう調整
            clip_width = min(int(SCREEN_WIDTH / current_zoom), SCREEN_WIDTH - clip_x)
            clip_height = min(int(SCREEN_HEIGHT / current_zoom), SCREEN_HEIGHT - clip_y)
            
            # バッファから領域を切り出し
            try:
                clip_area = pygame.Rect(clip_x, clip_y, clip_width, clip_height)
                clipped_buffer = buffer.subsurface(clip_area)
                
                # 切り出した領域をズーム
                zoomed_width = int(clip_width * current_zoom)
                zoomed_height = int(clip_height * current_zoom)
                zoomed_buffer = pygame.transform.scale(clipped_buffer, (zoomed_width, zoomed_height))
                
                # 指定されたサーフェスに描画
                surface.fill((0, 0, 0))  # サーフェスをクリア
                
                # ズームした画像をサーフェスの中央に配置
                dest_x = int(SCREEN_WIDTH/2 - zoomed_width/2)
                dest_y = int(SCREEN_HEIGHT/2 - zoomed_height/2)
                surface.blit(zoomed_buffer, (dest_x, dest_y))
            except ValueError:
                # 切り出し範囲が不正な場合はバックアップとしてそのまま描画
                print("ズームエラー: 切り出し範囲が不正です。通常描画に切り替えます。")
                surface.blit(buffer, (0, 0))
        
            # HUDは描画しない（背景としての利用のため）
            # 自動テストモードの情報表示も描画しない