#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import sys
import time
import traceback
from pathlib import Path
import json
from game.game import Game
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.states import AutoTestState, SplashScreenState, TitleState, InstructionsState, OptionsState  # SplashScreenStateをインポート

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
    
    # 自動テストフラグと状態追跡
    auto_test_transitions = True  # 自動テスト有効化
    test_state_sequence = ["SplashScreenState", "TitleState", "InstructionsState", 
                          "TitleState", "OptionsState", "TitleState"]
    current_test_state_index = 0
    next_transition_time = time.time() + 5  # 5秒後に最初の遷移
    
    # フェード効果のデバッグ情報
    fade_debug = {
        "enabled": True,  # フェードデバッグ有効化
        "last_alpha": 0,
        "fade_type": "none",  # "in", "out", "none"
        "start_time": time.time(),
        "duration": 0
    }
    
    # ゲームインスタンスの作成
    main_game = Game(screen)  # メインのゲームインスタンス
    
    # 初期状態をSplashScreenStateに設定
    main_game.change_state(SplashScreenState(main_game))
    print("===== スプラッシュ画面表示開始 =====")
    print("フェード効果の説明:")
    print("1. フェードイン: 透明(alpha=0)から不透明(alpha=255)へ徐々に変化")
    print("2. 表示: 完全不透明(alpha=255)で一定時間表示")
    print("3. フェードアウト: 不透明(alpha=255)から透明(alpha=0)へ徐々に変化")
    print("===============================")
    
    # 背景用のゲームインスタンスは後で初期化するために初期値はNoneに設定
    background_game = None
    background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    hud_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    background_test_start_time = time.time()
    
    # スプラッシュ画面表示用のフラグとタイマー
    splash_complete = False
    splash_start_time = time.time()
    splash_debug_last_time = time.time()
    
    # メインループ
    frame_count = 0
    start_time = time.time()
    
    while True:
        try:
            # 現在の時刻を記録
            current_tick = pygame.time.get_ticks()
            current_time = time.time()
            frame_count += 1
            
            # フレームレートのデバッグ（10秒ごと）
            if current_time - splash_debug_last_time > 10.0:
                elapsed = current_time - splash_debug_last_time
                fps = frame_count / elapsed
                print(f"フレームレート: {fps:.2f} FPS (frames={frame_count}, elapsed={elapsed:.2f}s)")
                frame_count = 0
                splash_debug_last_time = current_time
            
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    # 自動テスト時に'T'キーで次の状態に遷移
                    if event.key == pygame.K_t and auto_test_transitions:
                        next_transition_time = current_time  # 即時遷移
                        print("テスト: 'T'キーによる即時遷移トリガー")
                    # Escapeキーの特別処理を削除し、全てのキーを同様に処理
                    main_game.handle_keydown(event.key)
                    # タイトル画面でBGMを停止
                    if main_game.current_state.__class__.__name__ != "TitleState" and title_bgm_playing:
                        title_bgm.stop()
                        title_bgm_playing = False
                elif event.type == pygame.KEYUP:
                    main_game.handle_keyup(event.key)
            
            # 現在の状態を取得
            current_state_name = main_game.current_state.__class__.__name__
            
            # フェード効果のデバッグ - SplashScreenStateのみ
            if current_state_name == "SplashScreenState" and fade_debug["enabled"]:
                # フェード状態を確認（SplashScreenStateからアルファ値を取得）
                if hasattr(main_game.current_state, "alpha"):
                    alpha = main_game.current_state.alpha
                    # アルファ値が変化したときのみログを出力
                    if alpha != fade_debug["last_alpha"]:
                        # フェードタイプを判定
                        if alpha > fade_debug["last_alpha"]:
                            if fade_debug["fade_type"] != "in":
                                fade_debug["fade_type"] = "in"
                                fade_debug["start_time"] = current_time
                                print(f"フェードイン開始: time={current_time-start_time:.2f}s")
                        elif alpha < fade_debug["last_alpha"]:
                            if fade_debug["fade_type"] != "out":
                                fade_debug["fade_type"] = "out"
                                fade_debug["start_time"] = current_time
                                print(f"フェードアウト開始: time={current_time-start_time:.2f}s")
                        
                        # 20%刻みでログを表示
                        if alpha % 50 < 5 or alpha == 255 or alpha == 0:
                            fade_percentage = (alpha / 255) * 100
                            print(f"フェード状態: {fade_debug['fade_type']}, alpha={alpha}, 不透明度={fade_percentage:.1f}%")
                        
                        fade_debug["last_alpha"] = alpha
            
            # 自動テスト遷移処理
            if auto_test_transitions and current_time >= next_transition_time:
                if current_test_state_index < len(test_state_sequence):
                    target_state = test_state_sequence[current_test_state_index]
                    if current_state_name != target_state:
                        print(f"テスト: {current_state_name} -> {target_state} へ自動遷移します")
                        
                        if target_state == "SplashScreenState":
                            main_game.change_state(SplashScreenState(main_game))
                        elif target_state == "TitleState":
                            main_game.change_state(TitleState(main_game))
                        elif target_state == "InstructionsState":
                            main_game.change_state(InstructionsState(main_game))
                        elif target_state == "OptionsState":
                            main_game.change_state(OptionsState(main_game))
                        
                        current_test_state_index += 1
                        next_transition_time = current_time + 5  # 次の遷移までの時間
                        print(f"テスト: 次の遷移は {next_transition_time - current_time:.1f}秒後")
                        
                    elif current_test_state_index == 0 and target_state == "SplashScreenState":
                        # 最初のSplashScreenStateは自動遷移するのを待つ
                        print(f"テスト: SplashScreenState -> TitleState への自動遷移を待機中...")
                        # スプラッシュの次の状態に進む
                        current_test_state_index += 1
            
            # スプラッシュ関連のデバッグ出力（1秒ごと）
            if current_state_name == "SplashScreenState" and current_time - splash_start_time > 1.0:
                splash_start_time = current_time
                elapsed_from_start = current_time - start_time
                print(f"スプラッシュ画面表示中: 経過時間={elapsed_from_start:.2f}s, tick={current_tick}, frames={frame_count}")
            
            # スプラッシュ画面からタイトル画面への遷移があった場合
            if current_state_name == "TitleState" and not splash_complete:
                splash_complete = True
                elapsed_from_start = current_time - start_time
                print(f"スプラッシュ完了、タイトル画面に遷移しました: 経過時間={elapsed_from_start:.2f}s")
                
                # 背景ゲームが初期化されていなければ初期化
                if not background_game:
                    print("背景ゲーム初期化")
                    # 背景用の自動テスト用ゲームインスタンスを初期化
                    background_game = Game(screen)
                    background_game.change_state(AutoTestState(background_game))
            
            # タイトル画面での処理
            if current_state_name == "TitleState":
                # タイトルBGM再生
                if not title_bgm_playing:
                    title_bgm.play(-1)  # -1でループ再生
                    title_bgm_playing = True
                    print("タイトルBGM再生開始")

                # 背景ゲームが初期化されていれば更新
                if background_game:
                    # === 背景ゲームの更新とリセットをここに移す ===
                    # 定期的にテストをリセット（10秒ごと）
                    if current_time - background_test_start_time > 10:
                        background_game = Game(screen)
                        background_game.change_state(AutoTestState(background_game))
                        background_test_start_time = current_time
                        print("背景ゲームリセット")

                    # 背景ゲームの状態更新
                    background_game.update()
            
            # スプラッシュ画面での処理 - BGMは再生しない
            elif current_state_name == "SplashScreenState":
                # スプラッシュ画面では背景も特殊効果も再生しない
                pass
            else: # その他の画面
                 # BGM停止 (main_game.handle_keydown 内の処理と重複する可能性があるので注意)
                 # if title_bgm_playing:
                 #    title_bgm.stop()
                 #    title_bgm_playing = False
                 pass # 特に何もしない、または他の状態での共通処理

            # メインゲームの状態更新 (常に実行)
            main_game.update()
            
            # 描画処理
            screen.fill((0, 0, 0))  # 画面クリア
            
            # スプラッシュ画面の場合は背景処理を行わない
            if current_state_name != "SplashScreenState":
                # 背景サーフェスをクリア
                background_surface.fill((0, 0, 0, 0))
                
                # HUDサーフェスをクリア
                hud_surface.fill((0, 0, 0, 0))
                
                # 背景ゲームを一旦サーフェスに描画（タイトル画面かつ背景ゲームが初期化されている場合のみ）
                if current_state_name == "TitleState" and background_game:
                    # タイトル画面の時のみ背景に自動テストを表示
                    try:
                        background_game.draw_to_surface(background_surface)
                    except Exception as e:
                        print(f"背景描画エラー: {e}")
                        # エラー時は単色背景に切り替え
                        background_surface.fill((20, 20, 40))
                    
                    # 半透明オーバーレイを適用
                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 100))  # 半透明の黒（透明度100/255、より透明に）
                    background_surface.blit(overlay, (0, 0))
                    
                    # 背景を画面に描画
                    screen.blit(background_surface, (0, 0))
            
            # メインゲームの描画（常に実行）
            main_game.draw()
            
            pygame.display.flip()
            
            # フレームレート維持
            clock.tick(FPS)
            
        except Exception as e:
            # エラーの詳細を出力
            print(f"致命的なエラーが発生しました: {e}")
            print(traceback.format_exc())
            pygame.quit()
            sys.exit(1)

if __name__ == "__main__":
    main() 