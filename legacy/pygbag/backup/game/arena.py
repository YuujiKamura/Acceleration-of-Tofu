import pygame
import math
from game.constants import *

class Arena:
    """円形アリーナを管理するクラス"""
    def __init__(self):
        self.radius = ARENA_RADIUS
        self.warning_radius = ARENA_WARNING_RADIUS
        self.center_x = ARENA_CENTER_X
        self.center_y = ARENA_CENTER_Y
        
        # アリーナ境界の点滅用
        self.border_alpha = 255
        self.border_alpha_direction = -1
        self.border_alpha_speed = 5
        
    def update(self):
        """アリーナの状態を更新"""
        # 境界線のアルファ値を更新（点滅効果）
        self.border_alpha += self.border_alpha_direction * self.border_alpha_speed
        if self.border_alpha <= 100:
            self.border_alpha = 100
            self.border_alpha_direction = 1
        elif self.border_alpha >= 255:
            self.border_alpha = 255
            self.border_alpha_direction = -1
            
    def draw(self, screen):
        """アリーナを描画"""
        # 背景を描画
        pygame.draw.circle(screen, (20, 20, 40), (self.center_x, self.center_y), self.radius)
        
        # 警告リングを描画（点滅効果）
        # アルファ値の計算はRGBタプルにはできないので、明度を変更する方法を使用
        alpha_ratio = self.border_alpha / 255.0
        warning_color = (
            int(ORANGE[0] * alpha_ratio),
            int(ORANGE[1] * alpha_ratio),
            int(ORANGE[2] * alpha_ratio)
        )
        pygame.draw.circle(screen, warning_color, (self.center_x, self.center_y), self.warning_radius, 2)
        
        # 外側のリングを描画
        pygame.draw.rect(screen, RED, (self.center_x - self.radius, self.center_y - self.radius, self.radius * 2, self.radius * 2), 3, border_radius=self.radius)
        
    def is_inside(self, x, y):
        """座標がアリーナ内にあるかチェック"""
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance < self.radius
        
    def is_near_border(self, x, y):
        """座標がアリーナの警告リング内にあるかチェック"""
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return self.warning_radius <= distance < self.radius
        
    def constrain_position(self, x, y):
        """座標をアリーナ内に制約"""
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance >= self.radius:
            # 円の境界上に制約
            angle = math.atan2(dy, dx)
            x = self.center_x + math.cos(angle) * (self.radius - 1)
            y = self.center_y + math.sin(angle) * (self.radius - 1)
            
        return (x, y) 