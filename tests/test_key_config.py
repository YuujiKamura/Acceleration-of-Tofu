#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import pygame
import sys
import time
from pygame.locals import *

# 必要なモジュールをインポート
from game.constants import (
    DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2,
    KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPING,
    ACTION_NAMES, KEY_NAMES
)

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("キーコンフィグテスト")
clock = pygame.time.Clock()

# テスト用のフォント
font = pygame.font.SysFont(None, 32)

# キーコンフィグの保存
def save_key_config():
    try:
        config = {
            "p1": {str(k): v for k, v in KEY_MAPPING_P1.items()},
            "p2": {str(k): v for k, v in KEY_MAPPING_P2.items()}
        }
        with open("test_key_config.json", "w") as f:
            json.dump(config, f)
        return True
    except Exception as e:
        print(f"設定の保存に失敗しました: {e}")
        return False

# キーコンフィグの読み込み
def load_key_config():
    try:
        if os.path.exists("test_key_config.json"):
            with open("test_key_config.json", "r") as f:
                config = json.load(f)
            
            # プレイヤー1の設定
            KEY_MAPPING_P1.clear()
            for k, v in config["p1"].items():
                KEY_MAPPING_P1[int(k)] = v
            
            # プレイヤー2の設定
            KEY_MAPPING_P2.clear()
            for k, v in config["p2"].items():
                KEY_MAPPING_P2[int(k)] = v
            
            # 互換性のために古いマッピングも更新
            KEY_MAPPING.clear()
            KEY_MAPPING.update(KEY_MAPPING_P1)
            return True
    except Exception as e:
        print(f"設定の読み込みに失敗しました: {e}")
        # エラー時はデフォルト設定に戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        return False

# テスト1: デフォルト設定の確認
def test_default_settings():
    print("テスト1: デフォルト設定のチェック")
    
    # デフォルト設定のコピーを作成
    original_p1 = DEFAULT_KEY_MAPPING_P1.copy()
    original_p2 = DEFAULT_KEY_MAPPING_P2.copy()
    
    # 現在の設定がデフォルトと同じか確認
    p1_match = all(KEY_MAPPING_P1.get(k) == v for k, v in original_p1.items())
    p2_match = all(KEY_MAPPING_P2.get(k) == v for k, v in original_p2.items())
    
    # 結果の表示
    print(f"プレイヤー1のキー設定がデフォルトと一致: {'OK' if p1_match else 'NG'}")
    print(f"プレイヤー2のキー設定がデフォルトと一致: {'OK' if p2_match else 'NG'}")
    
    if not p1_match or not p2_match:
        print("デフォルト設定に戻します。")
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
    
    return p1_match and p2_match

# テスト2: 設定の変更と保存
def test_save_config():
    print("\nテスト2: 設定の変更と保存")
    
    # 変更前の設定の一部を記録
    before_p1_up = None
    for k, v in KEY_MAPPING_P1.items():
        if v == "up":
            before_p1_up = k
            break
    
    # プレイヤー1の「上」を別のキーに変更
    test_key = pygame.K_t  # 'T'キーに変更
    
    # 既存の「上」の割り当てを削除
    for k, v in list(KEY_MAPPING_P1.items()):
        if v == "up":
            del KEY_MAPPING_P1[k]
    
    # 新しいキーを割り当て
    KEY_MAPPING_P1[test_key] = "up"
    
    # 互換性のために古いマッピングも更新
    KEY_MAPPING.clear()
    KEY_MAPPING.update(KEY_MAPPING_P1)
    
    # 設定を保存
    save_result = save_key_config()
    
    # 結果の表示
    print(f"設定の変更: {'OK' if test_key in KEY_MAPPING_P1 else 'NG'}")
    print(f"設定の保存: {'OK' if save_result else 'NG'}")
    
    # 変更した設定を表示
    for action, name in ACTION_NAMES.items():
        for k, v in KEY_MAPPING_P1.items():
            if v == action:
                key_name = KEY_NAMES.get(k, str(k))
                if action == "up":
                    print(f"プレイヤー1の「{name}」: {key_name} (変更後)")
                    break
    
    return save_result

# テスト3: 設定の読み込み
def test_load_config():
    print("\nテスト3: 設定の読み込み")
    
    # いったんデフォルトに戻す
    KEY_MAPPING_P1.clear()
    KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
    
    # 設定を読み込み
    load_result = load_key_config()
    
    # 変更したキー設定がきちんと読み込まれたか確認
    test_key = pygame.K_t
    key_loaded = False
    
    for k, v in KEY_MAPPING_P1.items():
        if k == test_key and v == "up":
            key_loaded = True
            break
    
    # 結果の表示
    print(f"設定の読み込み: {'OK' if load_result else 'NG'}")
    print(f"変更したキー設定の確認: {'OK' if key_loaded else 'NG'}")
    
    # 読み込んだ設定を表示
    for action, name in ACTION_NAMES.items():
        for k, v in KEY_MAPPING_P1.items():
            if v == action:
                key_name = KEY_NAMES.get(k, str(k))
                if action == "up":
                    print(f"プレイヤー1の「{name}」: {key_name} (読み込み後)")
                    break
    
    return load_result and key_loaded

# テスト4: プレイヤー2の設定が独立しているか
def test_player2_independence():
    print("\nテスト4: プレイヤー2の設定の独立性")
    
    # プレイヤー2の「上」キーを確認
    p2_up_key = None
    for k, v in KEY_MAPPING_P2.items():
        if v == "up":
            p2_up_key = k
            break
    
    # プレイヤー2の「上」を別のキーに変更
    test_key = pygame.K_y  # 'Y'キーに変更
    
    # 既存の「上」の割り当てを削除
    for k, v in list(KEY_MAPPING_P2.items()):
        if v == "up":
            del KEY_MAPPING_P2[k]
    
    # 新しいキーを割り当て
    KEY_MAPPING_P2[test_key] = "up"
    
    # 設定を保存
    save_result = save_key_config()
    
    # いったんデフォルトに戻す
    KEY_MAPPING_P1.clear()
    KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
    KEY_MAPPING_P2.clear()
    KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
    
    # 設定を読み込み
    load_result = load_key_config()
    
    # 変更したプレイヤー2のキー設定がきちんと読み込まれたか確認
    p2_key_loaded = False
    for k, v in KEY_MAPPING_P2.items():
        if k == test_key and v == "up":
            p2_key_loaded = True
            break
    
    # P1とP2が独立しているか確認
    p1_up_key = None
    for k, v in KEY_MAPPING_P1.items():
        if v == "up":
            p1_up_key = k
            break
    
    independence = p1_up_key != test_key
    
    # 結果の表示
    print(f"プレイヤー2の設定変更: {'OK' if save_result else 'NG'}")
    print(f"プレイヤー2の設定読み込み: {'OK' if p2_key_loaded else 'NG'}")
    print(f"プレイヤー1と2の設定が独立: {'OK' if independence else 'NG'}")
    
    # 読み込んだ設定を表示
    print("\nプレイヤー1のキー設定:")
    for action, name in ACTION_NAMES.items():
        for k, v in KEY_MAPPING_P1.items():
            if v == action:
                key_name = KEY_NAMES.get(k, str(k))
                print(f"  {name}: {key_name}")
                break
    
    print("\nプレイヤー2のキー設定:")
    for action, name in ACTION_NAMES.items():
        for k, v in KEY_MAPPING_P2.items():
            if v == action:
                key_name = KEY_NAMES.get(k, str(k))
                print(f"  {name}: {key_name}")
                break
    
    return p2_key_loaded and independence

# メインテスト実行
def run_tests():
    test1 = test_default_settings()
    test2 = test_save_config()
    test3 = test_load_config()
    test4 = test_player2_independence()
    
    print("\n===== テスト結果サマリー =====")
    print(f"テスト1 (デフォルト設定): {'成功' if test1 else '失敗'}")
    print(f"テスト2 (設定の変更と保存): {'成功' if test2 else '失敗'}")
    print(f"テスト3 (設定の読み込み): {'成功' if test3 else '失敗'}")
    print(f"テスト4 (プレイヤー2の独立性): {'成功' if test4 else '失敗'}")
    
    if test1 and test2 and test3 and test4:
        print("\n全てのテストが成功しました！")
    else:
        print("\n一部のテストが失敗しました。詳細を確認してください。")
    
    # 後片付け - テスト用の設定ファイルを削除
    if os.path.exists("test_key_config.json"):
        os.remove("test_key_config.json")
        print("\nテスト用設定ファイルを削除しました。")

# 対話モード - キー押下テスト
def interactive_test():
    print("\n===== 対話式キー押下テスト =====")
    print("各種キーを押して、正しく認識されるか確認します。")
    print("ESCキーで終了します。")
    
    running = True
    while running:
        screen.fill((0, 0, 0))
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                else:
                    print(f"キーが押されました: {event.key}")
                    
                    # P1の対応するアクション
                    p1_action = "なし"
                    if event.key in KEY_MAPPING_P1:
                        p1_action = ACTION_NAMES.get(KEY_MAPPING_P1[event.key], KEY_MAPPING_P1[event.key])
                    
                    # P2の対応するアクション
                    p2_action = "なし"
                    if event.key in KEY_MAPPING_P2:
                        p2_action = ACTION_NAMES.get(KEY_MAPPING_P2[event.key], KEY_MAPPING_P2[event.key])
                    
                    print(f"  プレイヤー1のアクション: {p1_action}")
                    print(f"  プレイヤー2のアクション: {p2_action}")
        
        # テキスト描画
        text1 = font.render("キーコンフィグテスト - 任意のキーを押してください", True, (255, 255, 255))
        text2 = font.render("ESCキーで終了", True, (255, 255, 255))
        screen.blit(text1, (50, 50))
        screen.blit(text2, (50, 100))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    run_tests()
    
    # テスト後に対話式テストを実行するか確認
    answer = input("\n対話式のキー押下テストを実行しますか？ (y/n): ")
    if answer.lower() == 'y':
        interactive_test()
    
    pygame.quit()
    sys.exit() 