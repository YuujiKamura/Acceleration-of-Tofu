import os
import pygame
from game.constants import (
    SCREEN_WIDTH, JAPANESE_FONT_NAMES, DEFAULT_FONT, JP_FONT_PATH,
    WHITE, GRAY, GREEN, ORANGE, RED, YELLOW, CYAN,
    MAX_HEALTH, MAX_HEAT, MAX_HYPER
)
from game.i18n import tr

class HUD:
    """ゲームのHUD（ヘッドアップディスプレイ）を管理するクラス"""
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

        # 日本語フォント対応 (WASM 対応: 同梱 TTF を優先)
        self.font = self._make_font(20)
        self.font_large = self._make_font(24)

        # 点滅効果用のフレームカウンター
        self.frame_count = 0

    def _make_font(self, size):
        """pygbag 対応の日本語フォント生成。

        同梱 TTF があれば pygame.font.Font() で直接ロード。無い場合のみ
        SysFont によるシステムフォント検索にフォールバックする。
        """
        if os.path.exists(JP_FONT_PATH):
            return pygame.font.Font(JP_FONT_PATH, size)
        available = pygame.font.get_fonts()
        available_lower = [f.lower() for f in available]
        for name in JAPANESE_FONT_NAMES:
            if name.lower() in available_lower:
                return pygame.font.SysFont(available[available_lower.index(name.lower())], size)
        return pygame.font.SysFont(DEFAULT_FONT, size)
        
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
        heat_text = self.font.render(tr("hud.heat", value=int(player.heat)), True, WHITE)
        heat_text_rect = heat_text.get_rect()
        heat_text_rect.topleft = (heat_x + heat_width + 10, heat_y)
        screen.blit(heat_text, heat_text_rect)
        
        # OVERHEATテキスト表示（200%以上の場合）
        if is_overheat:
            # 点滅表示
            if self.frame_count % 30 < 15:
                overheat_text = self.font_large.render(tr("hud.overheat"), True, ORANGE)
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
        hyper_text = self.font.render(tr("hud.hyper", value=int(player.hyper_gauge)), True, WHITE)
        hyper_text_rect = hyper_text.get_rect()
        hyper_text_rect.topleft = (hyper_x + hyper_width + 10, hyper_y)
        screen.blit(hyper_text, hyper_text_rect)

        # 水分量ゲージ
        water_width = 150
        water_height = 15
        water_x = x
        water_y = y + 110
        water_percent = min(1.0, player.water_level / 100.0)

        # 背景
        pygame.draw.rect(screen, GRAY, (water_x, water_y, water_width, water_height))
        # 水分 (青)
        pygame.draw.rect(screen, (50, 150, 255), (water_x, water_y, water_width * water_percent, water_height))
        # 枠線
        pygame.draw.rect(screen, WHITE, (water_x, water_y, water_width, water_height), 2)

        # 水分テキスト
        water_text = self.font.render(tr("hud.water", value=int(player.water_level)), True, WHITE)
        water_text_rect = water_text.get_rect()
        water_text_rect.topleft = (water_x + water_width + 10, water_y)
        screen.blit(water_text, water_text_rect)

        # 豆量ゲージ (茶色系)
        bean_width = 150
        bean_height = 10
        bean_x = x
        bean_y = y + 135
        bean_percent = min(1.0, player.beans / 100.0)
        pygame.draw.rect(screen, GRAY, (bean_x, bean_y, bean_width, bean_height))
        pygame.draw.rect(screen, (139, 69, 19), (bean_x, bean_y, bean_width * bean_percent, bean_height))
        pygame.draw.rect(screen, WHITE, (bean_x, bean_y, bean_width, bean_height), 1)
        bean_text = self.font.render(tr("hud.bean", value=int(player.beans)), True, WHITE)
        screen.blit(bean_text, (bean_x + bean_width + 10, bean_y - 5))

        # 熟成度ゲージ (黄金色系)
        aging_width = 150
        aging_height = 10
        aging_x = x
        aging_y = y + 155
        aging_percent = min(1.0, player.aging / 100.0)
        pygame.draw.rect(screen, GRAY, (aging_x, aging_y, aging_width, aging_height))
        pygame.draw.rect(screen, (255, 215, 0), (aging_x, aging_y, aging_width * aging_percent, aging_height))
        pygame.draw.rect(screen, WHITE, (aging_x, aging_y, aging_width, aging_height), 1)
        aging_text = self.font.render(tr("hud.aging", value=int(player.aging)), True, WHITE)
        screen.blit(aging_text, (aging_x + aging_width + 10, aging_y - 5))
        
        # ハイパーモード中表示
        if hasattr(player, 'is_hyper_active') and player.is_hyper_active:
            status_text = self.font_large.render(tr("hud.hyper_active"), True, YELLOW)
            status_rect = status_text.get_rect()
            status_rect.topleft = (x, y + 180)
            screen.blit(status_text, status_rect)
 