import math
import pygame
import random
import time  # 時間管理のためにtimeモジュールを追加

from game.constants import (
    PLAYER_SPEED, PLAYER_DASH_SPEED, DASH_RING_DURATION, DASH_COOLDOWN,
    MAX_HEALTH, SHIELD_DURATION, HYPER_DURATION,
    MAX_HEAT, MAX_HYPER, HEAT_DECREASE_RATE, HYPER_DECREASE_RATE_AT_BORDER,
    HYPER_CONSUMPTION_RATE, HYPER_ACTIVATION_COST,  # 新しい定数を追加
    CYAN, MAGENTA, YELLOW, 
    NEGI_GREEN, BENI_RED, TOFU_WHITE,  # 新しい色をインポート
    WEAPON_TYPES
)
from game.weapon import Weapon
from game.projectile import BeamProjectile, BallisticProjectile, MeleeProjectile

# オーバーヒートクールダウン定数
OVERHEAT_COOLDOWN = 120  # オーバーヒート後のクールダウンフレーム数
# ハイパーゲージの最大値
MAX_HYPER_GAUGE = MAX_HYPER  # MAX_HYPERを使用

class DashRing:
    """ダッシュ時に残る軌跡のリング"""
    def __init__(self, x, y, duration, direction_x=0, direction_y=0):
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.start_radius = 10  # 初期半径を10に変更
        self.radius = self.start_radius
        self.max_radius = 40  # 最大半径を40に変更
        # 進行方向の保存
        self.direction_x = direction_x
        self.direction_y = direction_y
        # 進行方向が設定されていない場合は円形に
        if self.direction_x == 0 and self.direction_y == 0:
            self.direction_x = 1  # デフォルト
        
    def update(self):
        """リングの状態を更新"""
        self.duration -= 1
        # リングが徐々に広がる
        progress = 1.0 - (self.duration / self.max_duration)
        self.radius = self.start_radius + (self.max_radius - self.start_radius) * progress
        
    def draw(self, screen):
        """リングを描画 - 進行方向に潰れた楕円"""
        alpha = int(255 * (self.duration / self.max_duration))
        color = (100, 200, 255, alpha)
        
        # 進行方向ベクトルの正規化
        length = math.sqrt(self.direction_x**2 + self.direction_y**2)
        if length > 0:
            norm_dir_x = self.direction_x / length
            norm_dir_y = self.direction_y / length
        else:
            norm_dir_x = 1
            norm_dir_y = 0
        
        # 楕円の描画パラメータ計算 - 潰れる方向を逆に
        ellipse_width = int(self.radius * 0.8)  # 進行方向に潰れる (短い)
        ellipse_height = int(self.radius * 1.5)  # 垂直方向に長い
        
        # 進行方向の角度
        angle = math.degrees(math.atan2(norm_dir_y, norm_dir_x))
        
        # 楕円の中心
        center_x, center_y = int(self.x), int(self.y)
        
        # 描画対象の楕円の矩形
        pygame.Rect(
            center_x - ellipse_width // 2,
            center_y - ellipse_height // 2,
            ellipse_width,
            ellipse_height
        )
        
        # 回転した楕円を描画
        ellipse_surface = pygame.Surface((ellipse_width, ellipse_height), pygame.SRCALPHA)
        pygame.draw.ellipse(ellipse_surface, color, pygame.Rect(0, 0, ellipse_width, ellipse_height), 2)
        
        # 回転
        rotated_surface = pygame.transform.rotate(ellipse_surface, -angle)  # 時計回りに回転
        
        # 回転後の中心位置調整
        rotated_rect = rotated_surface.get_rect(center=(center_x, center_y))
        
        # 描画
        screen.blit(rotated_surface, rotated_rect.topleft)
        
    @property
    def is_dead(self):
        """リングが消えるべきかどうか"""
        return self.duration <= 0

# シールドエフェクトクラスを追加
class ShieldEffect:
    """シールド発動時のエフェクト"""
    def __init__(self, owner):
        self.owner = owner
        self.duration = SHIELD_DURATION
        self.max_duration = SHIELD_DURATION
        self.base_radius = owner.radius + 12
        self.ring_count = 3  # リングの数
        self.rings = []
        self.is_dead = False
        
        # 複数のリングを生成（異なる大きさと速度で）
        for i in range(self.ring_count):
            self.rings.append({
                'radius': self.base_radius * (0.8 + i * 0.2),  # リングごとに少しずつ大きく
                'speed': 0.5 + i * 0.2,  # リングごとに回転速度を変える
                'angle': random.random() * 2 * math.pi,  # ランダムな初期角度
                'width': 2 + i  # リングの太さ
            })
        
    def update(self):
        """エフェクトの状態を更新"""
        self.duration -= 1
        if self.duration <= 0:
            self.is_dead = True
        
        # 各リングの回転を更新
        for ring in self.rings:
            ring['angle'] = (ring['angle'] + ring['speed'] * 0.1) % (2 * math.pi)
        
    def draw(self, screen):
        """エフェクトを描画"""
        if self.is_dead:
            return
        
        # プレイヤーの位置に追従
        x, y = int(self.owner.x), int(self.owner.y)
        
        # リングのパルス効果用の係数（時間経過で変化）
        pulse_factor = 0.2 * math.sin(self.duration * 0.1) + 1.0
        
        # シールドの残り時間に応じた透明度
        alpha_factor = self.duration / self.max_duration
        
        # 各リングを描画
        for ring in self.rings:
            # 色を計算（青から水色の間で変化）
            time_factor = (self.duration / 20) % 1.0  # 0〜1の間で変化
            r = int(0 + time_factor * 100)
            g = int(150 + time_factor * 100)
            b = int(200 + time_factor * 55)
            color = (r, g, b)
            
            # リングの実際の半径（パルス効果を適用）
            actual_radius = ring['radius'] * pulse_factor
            
            # リングの太さ
            width = max(1, int(ring['width'] * alpha_factor * 1.5))
            
            # 回転エフェクト用の複数の点を描画
            segments = 12
            for i in range(segments):
                angle = ring['angle'] + i * (2 * math.pi / segments)
                # 各セグメントの開始点と終了点
                start_angle = angle - 0.2
                end_angle = angle + 0.2
                
                # 弧の始点と終点を計算
                x + math.cos(start_angle) * actual_radius
                y + math.sin(start_angle) * actual_radius
                x + math.cos(end_angle) * actual_radius
                y + math.sin(end_angle) * actual_radius
                
                # セグメント間を結ぶ弧を描画
                rect = pygame.Rect(
                    x - actual_radius, 
                    y - actual_radius,
                    actual_radius * 2,
                    actual_radius * 2
                )
                pygame.draw.arc(screen, color, rect, start_angle, end_angle, width)

class Player:
    """プレイヤークラス"""
    def __init__(self, x, y, is_player1=True, game=None):
        self.x = x
        self.y = y
        # 初期位置を保存（リセット用）
        self.initial_x = x
        self.initial_y = y
        self.radius = 15  # プレイヤーの当たり判定半径
        self.is_player1 = is_player1
        # 色を変更（プレイヤー1はネギ色、プレイヤー2は紅生姜色）
        self.color = NEGI_GREEN if is_player1 else BENI_RED
        # 四角形のサイズ（半径の2倍で正方形に）
        self.square_size = 30
        
        # ステータス
        self.health = MAX_HEALTH
        self.heat = 0
        self.hyper_gauge = 0
        self.hyper_duration = 0  # ハイパーモードの残り時間
        
        # 移動関連
        self.speed = PLAYER_SPEED
        self.dash_speed = PLAYER_DASH_SPEED
        self.is_dashing = False
        self.dash_cooldown = 0
        self.dash_cooldown_max = 30
        self.dash_rings = []
        # 前回の位置を保存（移動方向計算用）
        self.prev_x = x
        self.prev_y = y
        # ダッシュ方向を保存
        self.dash_direction_x = 0
        self.dash_direction_y = 0
        # ダッシュ中の旋回速度
        self.dash_turn_speed = 0.15  # 小さいほどゆるやかにカーブ
        # ダッシュリング生成用カウンター
        self.dash_ring_counter = 0
        self.dash_ring_interval = 4  # 8フレームから4フレームに変更（より頻繁にリングを生成）
        
        # 武器
        self.weapons = {
            "weapon_a": Weapon("ビームライフル", WEAPON_TYPES["BEAM"], 20, 30),
            "weapon_b": Weapon("バリスティック", WEAPON_TYPES["BALLISTIC"], 40, 60),
            "special_b": Weapon("スプレッド", WEAPON_TYPES["BEAM"], 10, 15),
        }
        
        # アクション関連
        self.is_shooting = False
        self.is_special = False
        self.is_shield_active = False
        self.is_hyper_active = False
        self.has_fired_hyper_laser = False  # 強力なハイパーレーザーを発射したかのフラグ
        self.shoot_cooldown = 0
        self.facing_angle = 0  # 相手の方向を向く角度
        
        # シールド関連
        self.shield_cooldown = 0  # シールド持続時間カウンター
        self.shield_duration_counter = 0  # シールド持続時間のカウンター（テスト用）
        self.shield_effect = None  # シールドエフェクト
        
        # オーバーヒート状態フラグ
        self.is_overheated = False
        self.overheat_cooldown = 0
        
        # 武器B用の連射関連変数
        self.weapon_b_burst_active = False  # 連射モードがアクティブかどうか
        self.weapon_b_burst_count = 0       # 現在の連射カウント
        self.weapon_b_burst_timer = 0       # 連射のタイマー
        self.weapon_b_burst_delay = 5       # 発射間隔（フレーム数）
        self.weapon_b_burst_total = 10      # 合計発射数
        self.weapon_b_base_angle = 0        # 基準角度
        self.weapon_b_target = None         # 照準の対象
        self.is_special_spread_active = False  # スペシャルスプレッド弾モードかどうか
        
        # ゲームインスタンスへの参照（後でセットする）
        self.game = game
        
        # デバッグログ用の変数
        self.last_debug_time = 0  # 最後にログを出力した時間
        self.debug_interval = 1.0  # ログ出力の間隔（秒、0.5秒から1.0秒に変更）
        self.debug_mode = False  # デバッグモードフラグ（デフォルトでオフ）
        
        # テスト用のキー状態を保持する辞書
        self.key_states = {
            "up": False, 
            "down": False, 
            "left": False, 
            "right": False,
            "weapon_a": False, 
            "weapon_b": False,
            "shield": False,
            "dash": False,
            "hyper": False,
            "special": False
        }
        
    def reset(self):
        """プレイヤーの状態をリセットする"""
        # 位置を初期値に戻す
        self.x = self.initial_x
        self.y = self.initial_y
        
        # 移動状態をリセット
        self.dx = 0
        self.dy = 0
        self.speed = PLAYER_SPEED
        self.is_dashing = False
        self.dash_cooldown = 0
        self.dash_direction_x = 0
        self.dash_direction_y = 0
        self.dash_ring_counter = 0
        self.dash_rings = []
        
        # 武器関連のクールダウンをリセット
        self.shoot_cooldown = 0
        
        # 各種ゲージをリセット
        self.health = MAX_HEALTH
        self.heat = 0
        self.is_overheated = False
        self.overheat_cooldown = OVERHEAT_COOLDOWN
        self.hyper_gauge = MAX_HYPER / 2  # 起動時は半分から始める (MAX_HYPER_GAUGEをMAX_HYPERに変更)
        self.is_hyper_active = False
        self.hyper_duration = 0
        
        # シールド関連の状態をリセット
        self.is_shield_active = False
        self.shield_cooldown = 0
        self.shield_duration_counter = 0
        self.shield_effect = None
        
        # 武器B連射モードの状態をリセット
        self.weapon_b_burst_active = False
        self.weapon_b_burst_count = 0
        self.weapon_b_burst_timer = 0
        
        # すべてのキー状態をリセット
        self.key_states = {key: False for key in self.key_states}
        
    def update(self, arena, opponent):
        """プレイヤーの状態を更新"""
        # デバッグログ (プレイヤー1のみ、1秒に1回)
        current_time = time.time()
        if self.is_player1 and self.debug_mode and (current_time - self.last_debug_time) >= self.debug_interval:
            active_keys = [k for k, v in self.key_states.items() if v]
            if active_keys:  # アクティブなキーがある場合のみ出力
                print(f"[DEBUG P1] active_keys={active_keys}")
            self.last_debug_time = current_time
        
        # 相手の方向を計算
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        self.facing_angle = math.atan2(dy, dx)
        
        # 移動前の位置を保存
        self.prev_x = self.x
        self.prev_y = self.y
        
        # 移動処理 (self.key_states を渡す)
        self.move(self.key_states, arena)
        
        # 移動距離を計算して速度ベースのヒート上昇を適用
        distance_moved = math.sqrt((self.x - self.prev_x)**2 + (self.y - self.prev_y)**2)
        
        # 通常移動速度よりも速い場合、速度に応じてヒートゲージを上昇
        if distance_moved > PLAYER_SPEED and not self.is_overheated:
            # 速度の超過分（通常速度との差）に比例してヒートを上昇
            speed_factor = (distance_moved - PLAYER_SPEED) / (PLAYER_DASH_SPEED - PLAYER_SPEED)
            heat_increase = speed_factor * 4.0  # 最大4.0%/フレーム - より急激な上昇
            self.heat = min(MAX_HEAT, self.heat + heat_increase)
        
        # ダッシュリングの更新
        for ring in self.dash_rings[:]:
            ring.update()
            if ring.is_dead:
                self.dash_rings.remove(ring)
        
        # クールダウンの更新
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        # 武器B連射モードの更新
        if self.weapon_b_burst_active:
            self.weapon_b_burst_timer -= 1
            
            # タイマーが0になったら次の弾を発射
            if self.weapon_b_burst_timer <= 0 and self.weapon_b_burst_count < self.weapon_b_burst_total:
                # スペシャルスプレッド弾とバリスティック弾を区別して処理
                if self.is_special_spread_active:
                    self._fire_special_spread_shot()
                else:
                    self._fire_weapon_b_burst_shot()
                
                self.weapon_b_burst_count += 1
                
                # まだ発射する弾があれば、タイマーをリセット
                if self.weapon_b_burst_count < self.weapon_b_burst_total:
                    self.weapon_b_burst_timer = self.weapon_b_burst_delay
                else:
                    self.weapon_b_burst_active = False  # すべて発射したら連射モード終了
                    self.is_special_spread_active = False  # スペシャルモードもリセット
            
        # ヒート減少（ダッシュ中は減少しない）
        if self.heat > 0 and not self.is_dashing:
            self.heat -= HEAT_DECREASE_RATE
            
            # オーバーヒート状態の更新
            if self.heat >= MAX_HEAT:
                self.is_overheated = True
            elif self.is_overheated and self.heat <= self.overheat_cooldown:
                self.is_overheated = False
            
        # ハイパーモードの更新
        if self.is_hyper_active:
            self.hyper_duration -= 1
            
            # ハイパーゲージを徐々に消費
            self.hyper_gauge -= HYPER_CONSUMPTION_RATE
            
            # ゲージがなくなるか、時間切れになったらハイパーモードを終了
            if self.hyper_gauge <= 0 or self.hyper_duration <= 0:
                self.is_hyper_active = False
                self.hyper_gauge = max(0, self.hyper_gauge)  # 0未満にならないように
            
        # アリーナ境界付近でのハイパーゲージ減少
        if arena.is_near_border(self.x, self.y) and self.is_dashing:
            if self.hyper_gauge > 0:
                self.hyper_gauge -= HYPER_DECREASE_RATE_AT_BORDER
                
        # シールド処理
        if self.key_states["shield"] and self.shield_cooldown <= 0 and self.hyper_gauge >= 100:
            # シールドボタンが押されたとき、持続時間カウンターを設定
            self.shield_cooldown = SHIELD_DURATION
            self.shield_duration_counter = SHIELD_DURATION
            self.is_shield_active = True
            # シールドエフェクトを作成
            self.shield_effect = ShieldEffect(self)
            # ハイパーゲージを100消費
            self.hyper_gauge -= 100
            
        # シールド持続時間の更新
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
            self.shield_duration_counter = self.shield_cooldown
            
            # シールドエフェクトの更新
            if self.shield_effect:
                self.shield_effect.update()
                
            # カウンターが0になったらシールドを無効化
            if self.shield_cooldown <= 0:
                self.is_shield_active = False
                self.shield_duration_counter = 0
                self.shield_effect = None
        
        # 武器処理 (self.key_states を渡す)
        self.handle_weapons(self.key_states, opponent)
        
    def move(self, key_states, arena):
        """移動処理"""
        dx = 0
        dy = 0
        
        # キー入力に応じて移動方向を決定 (key_states を参照)
        if key_states["up"]:
            dy -= 1
        if key_states["down"]:
            dy += 1
        if key_states["left"]:
            dx -= 1
        if key_states["right"]:
            dx += 1
            
        # 入力があったかどうか（カーブに使用）
        has_input = dx != 0 or dy != 0
        
        # デバッグ出力（移動方向）
        if self.is_player1 and self.debug_mode and has_input:
            # 移動方向を言葉で表現
            direction = ""
            if dy < 0 and dx == 0:
                direction = "上"
            elif dy < 0 and dx > 0:
                direction = "右上"
            elif dy == 0 and dx > 0:
                direction = "右"
            elif dy > 0 and dx > 0:
                direction = "右下"
            elif dy > 0 and dx == 0:
                direction = "下"
            elif dy > 0 and dx < 0:
                direction = "左下"
            elif dy == 0 and dx < 0:
                direction = "左"
            elif dy < 0 and dx < 0:
                direction = "左上"
            
            print(f"[DEBUG P1] 移動方向: {direction}")
        
        # 斜め移動時に速度が速くならないよう正規化
        if dx != 0 and dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx /= length
            dy /= length
            
        # ヒートゲージが最大に達したらダッシュ強制終了してオーバーヒート状態にする
        if self.heat >= MAX_HEAT:
            self.is_dashing = False
            self.is_overheated = True
            
        # ダッシュ処理 (key_states を参照)
        heat_ok_for_dash = self.heat < 200
        if key_states["dash"] and self.dash_cooldown <= 0 and not self.is_dashing and has_input and heat_ok_for_dash:
            # ダッシュ開始時の処理
            self.is_dashing = True
            # ダッシュ開始時の方向を保存
            self.dash_direction_x = dx
            self.dash_direction_y = dy
            # ダッシュ開始時にもヒート上昇（オーバーヒート状態でない場合のみ）
            if not self.is_overheated:
                self.heat = min(MAX_HEAT, self.heat + 20)
            # ダッシュリングを追加 - 移動方向を指定
            self.dash_rings.append(DashRing(self.x, self.y, DASH_RING_DURATION, dx, dy))
            # ダッシュリングカウンターをリセット
            self.dash_ring_counter = 0
        elif not key_states["dash"]:
            self.is_dashing = False
            
        # ダッシュ中の処理
        if self.is_dashing:
            # ヒートゲージの上昇はupdate()メソッドで速度ベースで行うため、ここでは行わない
            
            # ヒートゲージが最大に達したらダッシュ強制終了してオーバーヒート状態にする
            if self.heat >= MAX_HEAT:
                self.is_dashing = False
                self.is_overheated = True
            
            # 方向転換処理
            if has_input:
                # 現在のダッシュ方向と入力方向の差を計算
                if dx != 0 or dy != 0:
                    # 現在の方向をゆるやかに入力方向に近づける
                    self.dash_direction_x = self.dash_direction_x * (1 - self.dash_turn_speed) + dx * self.dash_turn_speed
                    self.dash_direction_y = self.dash_direction_y * (1 - self.dash_turn_speed) + dy * self.dash_turn_speed
                    
                    # 方向を正規化
                    length = math.sqrt(self.dash_direction_x**2 + self.dash_direction_y**2)
                    if length > 0:
                        self.dash_direction_x /= length
                        self.dash_direction_y /= length
                        
                    # ダッシュ中のリング生成（一定間隔）
                    self.dash_ring_counter += 1
                    if self.dash_ring_counter >= self.dash_ring_interval:
                        self.dash_rings.append(DashRing(self.x, self.y, DASH_RING_DURATION, self.dash_direction_x, self.dash_direction_y))
                        self.dash_ring_counter = 0
            
        # 速度を適用
        speed = self.dash_speed if self.is_dashing else self.speed
        if self.is_dashing:
            # ダッシュ中は保存した方向に移動
            move_x = self.dash_direction_x * speed
            move_y = self.dash_direction_y * speed
        else:
            # 通常移動はキー入力方向に移動
            move_x = dx * speed
            move_y = dy * speed
            
        self.x += move_x
        self.y += move_y
        
        # アリーナ内に位置を制約
        self.x, self.y = arena.constrain_position(self.x, self.y)
        
        # ダッシュクールダウンを設定
        if self.is_dashing:
            self.dash_cooldown = DASH_COOLDOWN
            
    def handle_weapons(self, key_states, opponent):
        """武器処理"""
        # シールド中は攻撃できない
        if self.is_shield_active:
            return
            
        # 武器A (key_states を参照)
        if key_states["weapon_a"] and self.shoot_cooldown <= 0:
            weapon = self.weapons["weapon_a"]
            projectile = self.create_projectile(weapon, opponent)
            if projectile and self.game:
                self.game.add_projectile(projectile)
            self.shoot_cooldown = weapon.cooldown
            
        # 武器B (key_states を参照)
        if key_states["weapon_b"] and self.shoot_cooldown <= 0 and not self.weapon_b_burst_active:
            weapon = self.weapons["weapon_b"]
            
            # 連射モードを開始
            self.weapon_b_burst_active = True
            self.weapon_b_burst_count = 0
            self.weapon_b_burst_timer = 0  # 最初の弾はすぐに発射
            
            # 照準の角度と対象を記録
            dx = opponent.x - self.x
            dy = opponent.y - self.y
            self.weapon_b_base_angle = math.atan2(dy, dx)
            self.weapon_b_target = opponent
            
            # 最初の弾を発射
            self._fire_weapon_b_burst_shot()
            self.weapon_b_burst_count += 1
            self.weapon_b_burst_timer = self.weapon_b_burst_delay
            
            # クールダウンを設定
            self.shoot_cooldown = weapon.cooldown
            
        # スペシャル+武器B (key_states を参照)
        if key_states["special"] and key_states["weapon_b"] and self.shoot_cooldown <= 0:
            # ハイパーゲージが100以上ある場合のみ発動
            if self.hyper_gauge >= 100:
                weapon = self.weapons["special_b"]
                # ハイパーゲージを100消費
                self.hyper_gauge -= 100
                
                # 連射モードを開始（武器Bと同様の処理）
                self.weapon_b_burst_active = True
                self.is_special_spread_active = True  # スペシャルモードをオン
                self.weapon_b_burst_count = 0
                self.weapon_b_burst_timer = 0  # 最初の弾はすぐに発射
                
                # 照準の角度と対象を記録
                dx = opponent.x - self.x
                dy = opponent.y - self.y
                self.weapon_b_base_angle = math.atan2(dy, dx)
                self.weapon_b_target = opponent
                
                # 最初の弾を発射（スペシャル版）
                self._fire_special_spread_shot()
                self.weapon_b_burst_count += 1
                self.weapon_b_burst_timer = self.weapon_b_burst_delay
                
                # 効果音を再生（もし存在すれば）
                if self.game and "special" in self.game.sounds:
                    self.game.sounds["special"].play()
                
                # クールダウンを設定
                self.shoot_cooldown = weapon.cooldown
            else:
                # ゲージ不足の場合は通常の攻撃
                weapon = self.weapons["weapon_b"]
                projectile = self.create_projectile(weapon, opponent)
                if projectile and self.game:
                    self.game.add_projectile(projectile)
                self.shoot_cooldown = weapon.cooldown
            
        # ハイパーモード発動 (key_states を参照)
        if key_states["hyper"] and not self.is_hyper_active and self.hyper_gauge >= HYPER_ACTIVATION_COST:
            self.activate_hyper()
            
        # ハイパーモード中のレーザー攻撃 (key_states を参照)
        if self.is_hyper_active and key_states["hyper"] and self.shoot_cooldown <= 0:
            if not self.has_fired_hyper_laser:
                # 最初の一発は強力なレーザー
                weapon = Weapon("ハイパーレーザー", WEAPON_TYPES["BEAM"], 50, 15)
                projectile = self.create_projectile(weapon, opponent)
                if projectile and self.game:
                    # レーザービームの特殊効果（通常の10倍の太さと長さ、半分の速度）
                    projectile.radius = 30  # 通常の10倍の太さ
                    projectile.length = 200  # 通常の10倍の長さ
                    projectile.speed = 7.5  # 通常の半分の速度
                    projectile.color = YELLOW if self.is_player1 else MAGENTA
                    self.game.add_projectile(projectile)
                self.shoot_cooldown = 40  # 長めのクールダウン
                self.has_fired_hyper_laser = True  # フラグをオンに
                # 発射時にハイパーゲージを追加で消費
                self.hyper_gauge -= 10
            else:
                # 2発目以降は通常のビームライフルと同じ性能
                weapon = self.weapons["weapon_a"]  # 通常のビームライフルを使用
                projectile = self.create_projectile(weapon, opponent)
                if projectile and self.game:
                    # 通常色で少し強化（ハイパーモード中なのでダメージは2倍になる）
                    projectile.color = CYAN if self.is_player1 else MAGENTA
                    self.game.add_projectile(projectile)
                self.shoot_cooldown = weapon.cooldown  # 通常のクールダウン
                # 通常の消費のみ（追加消費なし）
            
    def create_projectile_with_angle(self, weapon, angle):
        """指定した角度で弾を生成（放射状発射用）"""
        projectile = None
        
        # ハイパーモード中はダメージ2倍
        damage_multiplier = 2.0 if self.is_hyper_active else 1.0
        actual_damage = weapon.damage * damage_multiplier
        
        if weapon.type == WEAPON_TYPES["BEAM"]:
            projectile = BeamProjectile(self.x, self.y, angle, actual_damage, self)
        elif weapon.type == WEAPON_TYPES["BALLISTIC"]:
            projectile = BallisticProjectile(self.x, self.y, angle, actual_damage, self)
        elif weapon.type == WEAPON_TYPES["MELEE"]:
            projectile = MeleeProjectile(self.x, self.y, angle, actual_damage, self)
            
        # 弾生成後に少しヒートゲージが上昇（5から10に増加）
        self.heat = min(MAX_HEAT, self.heat + 10)
        
        # ハイパーゲージも上昇（7から15に増加）
        self.hyper_gauge = min(MAX_HYPER, self.hyper_gauge + 15)
        
        # プロジェクタイルを返す
        return projectile
            
    def create_projectile(self, weapon, opponent):
        """武器に応じた弾を生成"""
        # 相手の方向へ発射
        dx = opponent.x - self.x
        dy = opponent.y - self.y
        angle = math.atan2(dy, dx)
        
        return self.create_projectile_with_angle(weapon, angle)
            
    def activate_hyper(self):
        """ハイパーを発動"""
        # ハイパーモードの発動条件：50以上のゲージが必要
        if self.hyper_gauge >= HYPER_ACTIVATION_COST:
            self.is_hyper_active = True
            self.has_fired_hyper_laser = False  # ハイパーレーザーを発射していない状態にリセット
            self.hyper_gauge -= HYPER_ACTIVATION_COST  # 初期コストのみ消費
            
            # ハイパーの効果時間（フレーム数）
            self.hyper_duration = HYPER_DURATION
            
            # ハイパーエフェクトを追加
            if self.game:
                hyper_effect = HyperEffect(self.x, self.y, self, 120)
                self.game.add_effect(hyper_effect)
            
    def take_damage(self, amount):
        """ダメージを受ける"""
        # シールド中はダメージを受けない
        if not self.is_shield_active:
            self.health -= amount
            # ハイパーゲージが増加（amount/10からamount/5に増加）
            self.hyper_gauge = min(MAX_HYPER, self.hyper_gauge + amount / 5)
            
    def is_shielding(self):
        """シールド状態かどうか"""
        return self.is_shield_active
        
    def collides_with(self, projectile):
        """弾との衝突判定"""
        dx = self.x - projectile.x
        dy = self.y - projectile.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < (self.radius + projectile.radius)
        
    def draw(self, screen):
        """プレイヤーを描画"""
        # ダッシュリングを描画
        for ring in self.dash_rings:
            ring.draw(screen)
            
        # シールドエフェクトを描画
        if self.shield_effect:
            self.shield_effect.draw(screen)
            
        # ハイパーモード中は輝くエフェクト
        if self.is_hyper_active:
            glow_radius = self.radius + 5
            pulse = (self.hyper_duration % 20) / 20.0  # 脈動効果
            glow_color = (255, 255, 0, int(200 * pulse + 50))  # 黄色の輝き
            pygame.draw.circle(screen, glow_color, (int(self.x), int(self.y)), glow_radius + int(pulse * 3))
            
            # 輝く四角形のサイズ
            glow_size = self.square_size + 6
            glow_rect = pygame.Rect(
                int(self.x - glow_size/2),
                int(self.y - glow_size/2),
                glow_size,
                glow_size
            )
            pygame.draw.rect(screen, glow_color, glow_rect, 2)
            
        # プレイヤーを白い四角形として描画
        color = self.color
        if self.is_hyper_active:
            # ハイパーモード中は色が変わる
            color = MAGENTA if self.is_player1 else YELLOW
            
        # 白い四角形（豆腐）
        base_rect = pygame.Rect(
            int(self.x - self.square_size/2),
            int(self.y - self.square_size/2),
            self.square_size,
            self.square_size
        )
        pygame.draw.rect(screen, TOFU_WHITE, base_rect)
        
        # 四角形の上に色付きの線（ネギまたは紅生姜）
        border_rect = pygame.Rect(
            int(self.x - self.square_size/2),
            int(self.y - self.square_size/2),
            self.square_size,
            self.square_size
        )
        pygame.draw.rect(screen, color, border_rect, 2)
        
        # プレイヤーの向きを示す線（武器）を太く、長くする
        weapon_length = self.radius * 2.5  # 半径の2.5倍の長さ
        end_x = self.x + math.cos(self.facing_angle) * weapon_length
        end_y = self.y + math.sin(self.facing_angle) * weapon_length
        pygame.draw.line(screen, color, (self.x, self.y), (end_x, end_y), 3)  # 線の太さを3に変更

    def _fire_weapon_b_burst_shot(self):
        """武器Bの連射モードで1発発射する"""
        if not self.game:
            return
            
        weapon = self.weapons["weapon_b"]
        
        # 放射状の角度を計算（中央を基準に左右に広がる）
        spread_angle = math.pi / 8  # 22.5度
        angle_offset = (self.weapon_b_burst_count - 2) * spread_angle
        current_angle = self.weapon_b_base_angle + angle_offset
        
        # 弾を生成
        projectile = self.create_projectile_with_angle(weapon, current_angle)
        if projectile:
            # 弾速を半分に、色を灰色に変更
            projectile.speed /= 2
            projectile.color = (128, 128, 128)  # 灰色
            # 威力を半分に
            projectile.damage /= 2
            # 寿命を4倍に延長（既存の2倍をさらに2倍）
            projectile.lifetime *= 4
            self.game.add_projectile(projectile)
            
            # 効果音を再生（もし存在すれば）
            if self.game and "shot" in self.game.sounds:
                self.game.sounds["shot"].play()

    def _fire_special_spread_shot(self):
        """スペシャルスプレッド弾を発射する（武器Bの強化版）"""
        if not self.game:
            return
            
        weapon = self.weapons["special_b"]
        
        # スペシャルスプレッド弾は2つの角度で発射（通常の2倍の弾数）
        spread_angle = math.pi / 8  # 22.5度
        
        # 1つ目の角度（武器Bと同じ計算）
        angle_offset1 = (self.weapon_b_burst_count - 2) * spread_angle
        current_angle1 = self.weapon_b_base_angle + angle_offset1
        
        # 2つ目の角度（1つ目からさらに少しずらす）
        angle_offset2 = (self.weapon_b_burst_count - 2) * spread_angle + (math.pi / 16)  # さらに11.25度ずらす
        current_angle2 = self.weapon_b_base_angle + angle_offset2
        
        # 1つ目の弾を生成
        projectile1 = self.create_projectile_with_angle(weapon, current_angle1)
        if projectile1:
            # 弾速を半分に
            projectile1.speed /= 2
            # 特別な色に変更（青っぽい色）
            projectile1.color = (50, 100, 255)  # 青色
            # 寿命を4倍に延長
            projectile1.lifetime *= 4
            self.game.add_projectile(projectile1)
        
        # 2つ目の弾を生成
        projectile2 = self.create_projectile_with_angle(weapon, current_angle2)
        if projectile2:
            # 弾速を半分に
            projectile2.speed /= 2
            # 特別な色に変更（青っぽい色）
            projectile2.color = (50, 100, 255)  # 青色
            # 寿命を4倍に延長
            projectile2.lifetime *= 4
            self.game.add_projectile(projectile2)

    def handle_key_event(self, event):
        """キーイベントを処理する"""
        # イベントタイプに基づく処理
        key_map = self.game.key_mapping_p1 if self.is_player1 else self.game.key_mapping_p2

        if event.type == pygame.KEYDOWN:
            # キーが押された場合
            if event.key in key_map:
                action = key_map[event.key]
                if action in self.key_states:
                    self.key_states[action] = True
                    # デバッグログ
                    if self.is_player1 and self.debug_mode:
                        print(f"[DEBUG P1] キー押下: {pygame.key.name(event.key)} -> {action}")

            # ESCキーが押された場合（ポーズ処理など）
            if event.key == pygame.K_ESCAPE:
                # ESCキーの処理はGameStateで行うため、ここでは何もしない
                pass

        elif event.type == pygame.KEYUP:
            # キーが離された場合
            if event.key in key_map:
                action = key_map[event.key]
                if action in self.key_states:
                    self.key_states[action] = False
                    # デバッグログ
                    if self.is_player1 and self.debug_mode:
                        print(f"[DEBUG P1] キー解放: {pygame.key.name(event.key)} -> {action}")
        
        # 以下のブロックを上記の条件付きデバッグログに置き換えたため削除
        # デバッグログ (プレイヤー1のみ、0.5秒に1回)
        # current_time = time.time()
        # if self.is_player1 and (current_time - self.last_debug_time) >= self.debug_interval:
        #     active_keys = [k for k, v in self.key_states.items() if v]
        #     if active_keys:  # アクティブなキーがある場合のみ出力
        #         print(f"[DEBUG P1] Event: {pygame.event.event_name(event.type)}, Key: {pygame.key.name(event.key)}")
        #         print(f"[DEBUG P1] active_keys={active_keys}")
        #     self.last_debug_time = current_time

# ハイパーエフェクトクラスを追加
class HyperEffect:
    """ハイパーモード発動時のエフェクト"""
    def __init__(self, x, y, owner, duration):
        self.x = x
        self.y = y
        self.owner = owner
        self.duration = duration
        self.max_duration = duration
        self.radius = 10
        self.is_dead = False
        
    def update(self):
        """エフェクトの状態を更新"""
        self.duration -= 1
        if self.duration <= 0:
            self.is_dead = True
        # 所有者に追従
        self.x = self.owner.x
        self.y = self.owner.y
        
    def draw(self, screen):
        """エフェクトを描画"""
        if self.is_dead:
            return
            
        alpha = int(255 * (self.duration / self.max_duration))
        radius = self.radius + int((self.max_duration - self.duration) / 2)
        
        # 輝くリング
        color = (200, 200, 255, alpha)
        for r in range(radius - 5, radius + 6, 3):
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), r, 1) 