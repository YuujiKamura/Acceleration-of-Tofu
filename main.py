#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import sys
import time
from pathlib import Path
import json
from game.game import Game
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.state import GameState

# BGMパターンの読み込み
def load_bgm_pattern():
    try:
        bgm_file = Path("bgm/current_pattern.json")
        if bgm_file.exists():
            with open(bgm_file, "r") as f:
                data = json.load(f)
            return data["pattern"], data["tempo"]
    except Exception as e:
        print(f"BGM読み込みエラー: {e}")
    return None, None

# BGM再生用の関数
def play_bgm_pattern(pattern, tempo, drum_sounds, drum_types):
    if not pattern:
        return
    
    current_time = time.time()
    beat_interval = 60.0 / float(tempo) / 4.0  # より正確な浮動小数点計算
    
    # 現在のビート位置を計算（より正確なタイミング計算）
    elapsed_beats = (current_time * float(tempo) / 60.0 * 4.0)
    current_beat = int(elapsed_beats % 16)
    
    # 前回の再生から十分な時間が経過したかチェック
    if elapsed_beats - int(elapsed_beats) < 0.1:  # ビートの開始時のみ音を再生
        # アクティブなセルの音を再生
        for row in range(len(pattern)):
            if row < len(drum_types) and pattern[row][current_beat]:
                sound_type = drum_types[row]
                if sound_type in drum_sounds and drum_sounds[sound_type]:
                    sound = drum_sounds[sound_type]
                    sound.set_volume(0.5)
                    sound.play()

def main():
    # Pygameの初期化
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)  # オーディオ設定を明示的に指定
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # タイトルBGMの読み込み
    title_bgm = pygame.mixer.Sound("assets/sounds/rockman_title.wav")
    title_bgm.set_volume(0.5)  # 音量を50%に設定
    title_bgm_playing = False
    
    # BGMパターンの読み込み
    bgm_pattern, bgm_tempo = load_bgm_pattern()
    
    # ゲームインスタンスの作成
    main_game = Game(screen)  # メインのゲームインスタンス
    
    # 背景用の自動テスト用ゲームインスタンス
    background_game = Game(screen)
    background_game.state = GameState.AUTO_TEST  # 自動テストモードに設定
    
    # 背景用のレンダリング用サーフェス
    background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # HUD用の半透明サーフェス
    hud_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # 背景テスト開始時刻
    background_test_start_time = time.time()
    
    # メインループ
    while True:
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                main_game.handle_keydown(event.key)
                # タイトル画面でBGMを停止
                if main_game.state != GameState.TITLE and title_bgm_playing:
                    title_bgm.stop()
                    title_bgm_playing = False
            elif event.type == pygame.KEYUP:
                main_game.handle_keyup(event.key)
        
        # タイトル画面でBGMを再生
        if main_game.state == GameState.TITLE and not title_bgm_playing:
            title_bgm.play(-1)  # -1でループ再生
            title_bgm_playing = True
        
        # 背景の自動テストを更新
        # 定期的にテストをリセット（10秒ごと）
        if time.time() - background_test_start_time > 10:
            background_game = Game(screen)
            background_game.state = GameState.AUTO_TEST
            background_test_start_time = time.time()
        
        # 背景ゲームの状態更新
        background_game.update()
        
        # メインゲームの状態更新
        main_game.update()
        

        # 描画処理
        screen.fill((0, 0, 0))  # 画面クリア
        
        # 背景サーフェスをクリア
        background_surface.fill((0, 0, 0, 0))
        
        # HUDサーフェスをクリア
        hud_surface.fill((0, 0, 0, 0))
        
        # 背景ゲームを一旦サーフェスに描画
        if main_game.state == GameState.TITLE:
            # タイトル画面の時のみ背景に自動テストを表示
            background_game.draw_to_surface(background_surface)
            
            # 半透明オーバーレイを適用
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # 半透明の黒（透明度100/255、より透明に）
            background_surface.blit(overlay, (0, 0))
            
            # 背景を画面に描画
            screen.blit(background_surface, (0, 0))
            
            # タイトル画面の描画（HUDなし）
            main_game.draw()
        else:
            # ゲームプレイ時は通常通りHUDを含めて描画
            main_game.draw()
        
        pygame.display.flip()
        
        # フレームレート維持
        clock.tick(FPS)

if __name__ == "__main__":
    main() 