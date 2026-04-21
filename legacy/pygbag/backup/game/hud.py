import pygame
from game.constants import *

class HUD:
    """ゲームのHUD（ヘッドアップディスプレイ）を管理するクラス"""
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        
        # 日本語フォント対応
        self.font_name = self.find_japanese_font()
        self.font = pygame.font.SysFont(self.font_name, 20)
        
        # 点滅効果用のフレームカウンター
        self.frame_count = 0
    
    def find_japanese_font(self):
        """システムで利用可能な日本語フォントを検索"""
        available_fonts = pygame.font.get_fonts()
        available_fonts_lower = [f.lower() for f in available_fonts]
        
        for font_name in JAPANESE_FONT_NAMES:
            font_lower = font_name.lower()
            if font_lower in available_fonts_lower:
                index = available_fonts_lower.index(font_lower)
                return available_fonts[index]  # 元のケースのフォント名を使用
                
        # 日本語フォントが見つからない場合はデフォルトを使用
        return DEFAULT_FONT
        
    def draw(self, screen):
        """HUDを描画"""
        # フレームカウンターを更新
        self.frame_count = (self.frame_count + 1) % 60  # 1秒ごとにリセット
        
        # 左側（プレイヤー1のHUD）
        self.draw_player_hud(screen, self.player1, 20, 20, True)
        
        # 右側（プレイヤー2のHUD）
        self.draw_player_hud(screen, self.player2, SCREEN_WIDTH - 220, 20, False)
        
        # タイマー（中央上部）
        # このゲームではタイマーを実装しないため、省略
        
    def draw_player_hud(self, screen, player, x, y, is_left):
        """個別プレイヤーのHUDを描画"""
        # プレイヤー名
        name = "プレイヤー1" if player.is_player1 else "プレイヤー2"
        name_text = self.font.render(name, True, WHITE)
        name_rect = name_text.get_rect()
        name_rect.topleft = (x, y)
        screen.blit(name_text, name_rect)
        
        # 体力バー
        health_width = 200
        health_height = 20
        health_x = x
        health_y = y + 30
        health_percent = max(0, player.health / MAX_HEALTH)
        
        # 背景
        pygame.draw.rect(screen, GRAY, (health_x, health_y, health_width, health_height))
        # 体力
        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_width * health_percent, health_height))
        # 枠線
        pygame.draw.rect(screen, WHITE, (health_x, health_y, health_width, health_height), 2)
        
        # ヒートゲージ
        heat_width = 150
        heat_height = 15
        heat_x = x
        heat_y = y + 60
        heat_percent = min(1.0, player.heat / MAX_HEAT)
        
        # 背景
        pygame.draw.rect(screen, GRAY, (heat_x, heat_y, heat_width, heat_height))
        
        # ヒート
        # OVERHEATの場合（200%以上）は点滅表示
        is_overheat = player.heat >= 200
        if is_overheat:
            # 0.5秒ごとに点滅（30フレーム）
            if self.frame_count % 30 < 15:
                pygame.draw.rect(screen, ORANGE, (heat_x, heat_y, heat_width * heat_percent, heat_height))
            else:
                pygame.draw.rect(screen, RED, (heat_x, heat_y, heat_width * heat_percent, heat_height))
        else:
            pygame.draw.rect(screen, RED, (heat_x, heat_y, heat_width * heat_percent, heat_height))
            
        # 枠線
        pygame.draw.rect(screen, WHITE, (heat_x, heat_y, heat_width, heat_height), 2)
        
        # ヒートテキスト
        heat_text = self.font.render(f"ヒート: {int(player.heat)}%", True, WHITE)
        heat_text_rect = heat_text.get_rect()
        heat_text_rect.topleft = (heat_x + heat_width + 10, heat_y)
        screen.blit(heat_text, heat_text_rect)
        
        # OVERHEATテキスト表示（200%以上の場合）
        if is_overheat:
            overheat_font = pygame.font.SysFont(self.font_name, 24)
            # 点滅表示
            if self.frame_count % 30 < 15:
                overheat_text = overheat_font.render("OVERHEAT", True, ORANGE)
                overheat_rect = overheat_text.get_rect()
                overheat_rect.midtop = (heat_x + heat_width // 2, heat_y - 30)
                screen.blit(overheat_text, overheat_rect)
        
        # ハイパーゲージ
        hyper_width = 150
        hyper_height = 15
        hyper_x = x
        hyper_y = y + 85
        hyper_percent = min(1.0, player.hyper_gauge / MAX_HYPER)
        
        # 背景
        pygame.draw.rect(screen, GRAY, (hyper_x, hyper_y, hyper_width, hyper_height))
        
        # ハイパー
        is_hyper_ready = player.hyper_gauge >= 100
        if is_hyper_ready:
            # ハイパーゲージが100%以上の場合は点滅
            if self.frame_count % 30 < 15:
                hyper_color = YELLOW
            else:
                hyper_color = CYAN
        else:
            hyper_color = CYAN
            
        pygame.draw.rect(screen, hyper_color, (hyper_x, hyper_y, hyper_width * hyper_percent, hyper_height))
        
        # 枠線
        pygame.draw.rect(screen, WHITE, (hyper_x, hyper_y, hyper_width, hyper_height), 2)
        
        # ハイパーテキスト
        hyper_text = self.font.render(f"ハイパー: {int(player.hyper_gauge)}%", True, WHITE)
        hyper_text_rect = hyper_text.get_rect()
        hyper_text_rect.topleft = (hyper_x + hyper_width + 10, hyper_y)
        screen.blit(hyper_text, hyper_text_rect)
        
        # ハイパーモード中表示
        if hasattr(player, 'is_hyper_active') and player.is_hyper_active:
            status_font = pygame.font.SysFont(self.font_name, 24)
            status_text = status_font.render("ハイパーモード発動中! (ダメージ2倍)", True, YELLOW)
            status_rect = status_text.get_rect()
            status_rect.topleft = (x, y + 115)
            screen.blit(status_text, status_rect) 