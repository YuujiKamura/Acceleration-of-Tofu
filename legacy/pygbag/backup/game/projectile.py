import pygame
import math
from game.constants import *

class Projectile:
    """弾の基底クラス"""
    def __init__(self, x, y, angle, damage, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.owner = owner
        self.radius = 5
        self.speed = 0
        self.is_dead = False
        self.lifetime = 60  # デフォルトの寿命（フレーム数）
        self.homing = False  # ホーミング機能のフラグ
        self.homing_strength = 0.0  # ホーミングの強さ（0.0～1.0）
        
    def update(self):
        """弾の状態を更新"""
        # ホーミング処理（敵の方向へ少し曲がる）
        if self.homing and not self.owner.is_player1:
            self.home_towards(self.owner.game.player1)
        elif self.homing and self.owner.is_player1:
            self.home_towards(self.owner.game.player2)
            
        # 移動
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # 寿命チェック
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.is_dead = True
            
        # アリーナ外チェック
        distance = math.sqrt((self.x - ARENA_CENTER_X) ** 2 + (self.y - ARENA_CENTER_Y) ** 2)
        if distance > ARENA_RADIUS:
            self.is_dead = True
    
    def home_towards(self, target):
        """ターゲットに向かってホーミングする"""
        if target is None or self.is_dead:
            return
            
        # ターゲットへの方向を計算
        dx = target.x - self.x
        dy = target.y - self.y
        target_angle = math.atan2(dy, dx)
        
        # 角度の差を計算（-πからπの範囲）
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        
        # ホーミングの強さに応じて角度を変更
        self.angle += angle_diff * self.homing_strength
        
    def draw(self, screen):
        """弾を描画"""
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        
    def on_hit(self, target):
        """ヒット時の処理"""
        self.is_dead = True
        
    def reflect(self, reflector):
        """反射時の処理"""
        # 反射の基本処理
        # 角度を反転し、所有者を変更
        self.angle = (self.angle + math.pi) % (2 * math.pi)
        self.owner = reflector

class BeamProjectile(Projectile):
    """ビーム弾"""
    def __init__(self, x, y, angle, damage, owner):
        super().__init__(x, y, angle, damage, owner)
        self.speed = 15
        self.radius = 3
        self.length = 20
        self.color = CYAN if owner.is_player1 else MAGENTA
        # ビームは弱めのホーミング
        self.homing = True
        self.homing_strength = 0.02  # 2%の強さでホーミング
        
    def draw(self, screen):
        """ビームを描画"""
        # ビームの先端
        end_x = self.x + math.cos(self.angle) * self.length
        end_y = self.y + math.sin(self.angle) * self.length
        
        # ビームの本体
        pygame.draw.line(screen, self.color, (self.x, self.y), (end_x, end_y), 3)
        # ビームの先端
        pygame.draw.circle(screen, WHITE, (int(end_x), int(end_y)), 2)
        
    def on_hit(self, target):
        """ビームヒット時の処理"""
        super().on_hit(target)
        # ハイパーゲージが少し増加
        self.owner.hyper_gauge = min(MAX_HYPER, self.owner.hyper_gauge + 3)

class BallisticProjectile(Projectile):
    """弾丸"""
    def __init__(self, x, y, angle, damage, owner):
        super().__init__(x, y, angle, damage, owner)
        self.speed = 8
        self.radius = 6
        self.color = YELLOW if owner.is_player1 else ORANGE
        # 弾丸は中程度のホーミング
        self.homing = True
        self.homing_strength = 0.03  # 3%の強さでホーミング
        
    def draw(self, screen):
        """弾丸を描画"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
    def on_hit(self, target):
        """弾丸ヒット時の処理"""
        super().on_hit(target)
        # ハイパーゲージが中程度増加
        self.owner.hyper_gauge = min(MAX_HYPER, self.owner.hyper_gauge + 7)

class MeleeProjectile(Projectile):
    """近接攻撃"""
    def __init__(self, x, y, angle, damage, owner):
        super().__init__(x, y, angle, damage, owner)
        self.speed = 12
        self.radius = 15
        self.lifetime = 10  # 短い寿命
        self.color = GREEN if owner.is_player1 else RED
        # 自分の位置を少し進める
        self.x += math.cos(angle) * 20
        self.y += math.sin(angle) * 20
        # 近接攻撃はホーミングしない
        self.homing = False
        
    def update(self):
        """近接攻撃の状態を更新"""
        super().update()
        # 所有者と一緒に移動（追従）
        if not self.is_dead:
            offset_distance = 20
            self.x = self.owner.x + math.cos(self.angle) * offset_distance
            self.y = self.owner.y + math.sin(self.angle) * offset_distance
        
    def draw(self, screen):
        """近接攻撃を描画"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, 2)
        
    def on_hit(self, target):
        """近接攻撃ヒット時の処理"""
        super().on_hit(target)
        # ハイパーゲージが大きく増加
        self.owner.hyper_gauge = min(MAX_HYPER, self.owner.hyper_gauge + 15) 