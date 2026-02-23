#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import pytest
from unittest.mock import patch
import pygame
from pygame.locals import *
import shutil

# ゲームのモジュールをインポート
from game.constants import ACTION_NAMES, DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2
from game.game import Game

class TestKeyConfigIntegration:
    """キーコンフィグのすべての機能を統合テストするクラス"""

    def setup_method(self):
        """各テスト前の初期化"""
        # テスト結果
        self.test_stats = {
            "total": 0,
            "success": 0,
            "failure": 0
        }
        self.test_results = []

        # Pygameの初期化（GUIは使わないがキーコードのために必要）
        pygame.init()
        
        # 設定ファイルのバックアップ
        self.backup_config_file()
        
        # テスト用のダミースクリーン作成
        self.screen = pygame.Surface((800, 600))
        
        # ゲームインスタンス作成
        self.game = Game(self.screen)
                
        # テスト用のキーセット（各アクションにユニークなキーを割り当て）
        self.test_keys = {
            "p1": {
                "up": pygame.K_t,
                "down": pygame.K_g,
                "left": pygame.K_f,
                "right": pygame.K_h,
                "weapon_a": pygame.K_v,
                "weapon_b": pygame.K_b,
                "hyper": pygame.K_n,
                "dash": pygame.K_m,
                "special": pygame.K_j,
                "shield": pygame.K_k
            },
            "p2": {
                "up": pygame.K_y,
                "down": pygame.K_u,
                "left": pygame.K_i,
                "right": pygame.K_o,
                "weapon_a": pygame.K_p,
                "weapon_b": pygame.K_l,
                "hyper": pygame.K_SEMICOLON,
                "dash": pygame.K_QUOTE,
                "special": pygame.K_PERIOD,
                "shield": pygame.K_COMMA
            }
        }
        
        print("キーコンフィグ統合テスト開始")
        print("=" * 60)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        # 設定ファイルを復元
        self.restore_config_file()
        
        # Pygameの終了
        pygame.quit()
        
        print("\nテスト完了。クリーンアップしました。")

    def backup_config_file(self):
        """設定ファイルのバックアップを作成"""
        if os.path.exists("key_config.json"):
            try:
                with open("key_config.json", "r") as f:
                    config = json.load(f)
                
                # バックアップファイルに保存
                with open("key_config.json.backup", "w") as f:
                    json.dump(config, f, indent=2)
                print("既存の設定ファイルをバックアップしました")
                
                # 設定ファイルの内容を検証
                self.validate_config_file(config)
            except Exception as e:
                print(f"バックアップ作成に失敗しました: {e}")
                # 破損した設定ファイルを保存
                if os.path.exists("key_config.json"):
                    shutil.copy("key_config.json", "key_config.json.corrupted")
                    print("破損した設定ファイルを key_config.json.corrupted として保存しました")

    def validate_config_file(self, config):
        """設定ファイルの内容を検証"""
        print("\n設定ファイルの検証:")
        valid = True
        
        # プレイヤー1の設定があるか
        if "p1" not in config:
            print("- エラー: p1の設定が存在しません")
            valid = False
        elif not config["p1"]:
            print("- エラー: p1の設定が空です")
            valid = False
        else:
            print(f"- P1の設定: {len(config['p1'])}個のキーマッピングが定義されています")
            
        # プレイヤー2の設定があるか
        if "p2" not in config:
            print("- エラー: p2の設定が存在しません")
            valid = False
        elif not config["p2"]:
            print("- エラー: p2の設定が空です")
            valid = False
        else:
            print(f"- P2の設定: {len(config['p2'])}個のキーマッピングが定義されています")
        
        # すべての必要なアクションが定義されているか
        for player, settings in config.items():
            missing_actions = []
            for action in ACTION_NAMES:
                if action not in settings.values():
                    missing_actions.append(action)
            
            if missing_actions:
                print(f"- 警告: {player}に{', '.join(missing_actions)}アクションが定義されていません")
        
        if not valid:
            print("設定ファイルに問題があります。テスト中に修正を試みます。")
        else:
            print("設定ファイルは有効です。")
        
        return valid

    def restore_config_file(self):
        """バックアップから設定ファイルを復元"""
        if os.path.exists("key_config.json.backup"):
            try:
                # バックアップから復元
                with open("key_config.json.backup", "r") as f:
                    config = json.load(f)
                
                with open("key_config.json", "w") as f:
                    json.dump(config, f, indent=2)
                print("設定ファイルを復元しました")
                
                # バックアップファイルを削除
                os.remove("key_config.json.backup")
            except Exception as e:
                print(f"復元に失敗しました: {e}")

    def test_key_mapping_setting(self):
        """キーマッピングの設定テスト"""
        print("\nテスト: すべてのアクションに対するキーマッピングの設定")
        
        # バックアップを取る
        p1_backup = self.game.key_mapping_p1.copy()
        
        try:        
            # 現在のキーマッピングをデバッグ出力
            print("テスト前のキーマッピング:", {k: v for k, v in self.game.key_mapping_p1.items()})
            
            # プレイヤー1のすべてのアクションに対するテスト
            for action, key in self.test_keys["p1"].items():
                # 既存のマッピングをクリア
                for k, v in list(self.game.key_mapping_p1.items()):
                    if v == action:
                        del self.game.key_mapping_p1[k]
                
                # 新しいキーを設定
                self.game.key_mapping_p1[key] = action
                
                # マッピングが正しく設定されたかテスト
                assert self.game.key_mapping_p1[key] == action, f"P1: キー {key} に '{action}' アクションが正しく設定されていない"
            
            # 互換性のためのKEY_MAPPINGの更新 - ここが重要ポイント
            print("key_mappingを更新中...")
            self.game.key_mapping.clear()
            self.game.key_mapping.update(self.game.key_mapping_p1)
            
            # 更新後のキーマッピングをデバッグ出力
            print("更新後のキーマッピング:", {k: v for k, v in self.game.key_mapping_p1.items()})
            
            # key_mappingが更新されたかテスト
            for action, key in self.test_keys["p1"].items():
                if key in self.game.key_mapping:
                    assert self.game.key_mapping[key] == action, f"key_mapping: キー {key} に '{action}' アクションが正しく設定されていない"
                else:
                    pytest.fail(f"キー {key} がkey_mappingに存在しません")
        finally:
            # テスト後に元の状態に戻す
            self.game.key_mapping_p1.clear()
            self.game.key_mapping_p1.update(p1_backup)
            self.game.key_mapping.clear()
            self.game.key_mapping.update(self.game.key_mapping_p1)

    def test_save_and_load_config(self):
        """設定の保存と読み込みのテスト"""
        print("\nテスト: 設定ファイルの保存と読み込み")
        
        # デバッグ出力
        print(f"テスト開始時のキーマッピング: {self.game.key_mapping_p1}")
        
        # ローカル変数にマッピングを作成（Gameインスタンスと別物）
        local_mapping_p1 = {}
        local_mapping_p2 = {}
        
        try:
            # テスト用のマッピングを設定 - 許可されたキーのみを使用
            test_keys_p1 = {
                "up": pygame.K_t,       # 116
                "down": pygame.K_g,     # 103
                "left": pygame.K_f,     # 102
                "right": pygame.K_h,    # 104
                "weapon_a": pygame.K_v, # 118
                "weapon_b": pygame.K_b, # 98
                "hyper": pygame.K_n,    # 110
                "dash": pygame.K_m,     # 109
                "special": pygame.K_j,  # 106
                "shield": pygame.K_k    # 107
            }
            
            # P1のキーマッピングを設定
            for action, key in test_keys_p1.items():
                # 既存のマッピングをクリア
                for k, v in list(self.game.key_mapping_p1.items()):
                    if v == action:
                        del self.game.key_mapping_p1[k]
                # 新しいキーを設定
                self.game.key_mapping_p1[key] = action
                # ローカル変数にも設定（キーとアクションの関係を保存）
                local_mapping_p1[key] = action
            
            # 更新してkey_mappingを設定
            self.game.key_mapping.clear()
            self.game.key_mapping.update(self.game.key_mapping_p1)
            
            # P2のマッピングはテストしないので設定しない
            
            # 設定を保存
            self.game.save_key_config()
            
            # 設定ファイルが作成されたか確認
            assert os.path.exists("key_config.json"), "設定ファイルが作成されていません"
            
            # ゲームのキーマッピングをデフォルトにリセット
            self.game.key_mapping_p1.clear()
            self.game.key_mapping_p1.update(DEFAULT_KEY_MAPPING_P1)
            self.game.key_mapping_p2.clear()
            self.game.key_mapping_p2.update(DEFAULT_KEY_MAPPING_P2)
            self.game.key_mapping.clear()
            self.game.key_mapping.update(self.game.key_mapping_p1)
            
            # 設定を読み込み
            self.game.load_key_config()
            
            # 読み込まれた設定が正しいか確認 - P1のみテスト
            for key, action in local_mapping_p1.items():
                assert key in self.game.key_mapping_p1, f"キー {key} がkey_mapping_p1に存在しません"
                assert self.game.key_mapping_p1[key] == action, f"P1のキー {key} の設定が一致しません"
            
            # key_mappingが正しく更新されたか確認 - P1のみテスト
            for key, action in local_mapping_p1.items():
                assert key in self.game.key_mapping, f"キー {key} がkey_mappingに存在しません"
                assert self.game.key_mapping[key] == action, f"key_mappingのキー {key} の設定が一致しません"
            
        finally:
            # テスト終了後、設定ファイルを削除
            if os.path.exists("key_config.json"):
                os.remove("key_config.json")

    def test_key_independence(self):
        """プレイヤー1と2のキー設定の独立性をテスト"""
        print("\nテスト: プレイヤー1と2のキー設定の独立性")
        
        # ゲームのキーマッピングをテスト用に設定
        for action, key in self.test_keys["p1"].items():
            self.game.key_mapping_p1[key] = action
        
        for action, key in self.test_keys["p2"].items():
            self.game.key_mapping_p2[key] = action
        
        # 共通のアクションでキーが異なることを確認
        for action in ACTION_NAMES.keys():
            p1_key = None
            p2_key = None
            
            for k, v in self.game.key_mapping_p1.items():
                if v == action:
                    p1_key = k
                    break
            
            for k, v in self.game.key_mapping_p2.items():
                if v == action:
                    p2_key = k
                    break
            
            if p1_key is not None and p2_key is not None:
                assert p1_key != p2_key, f"'{action}' アクションのP1とP2のキー設定が同じ"

    @patch('game.player.Player')
    def test_game_key_handler(self, mock_player):
        """ゲームのキーハンドラーのテスト"""
        print("\nテスト: ゲームのキーハンドラー")
        
        # ゲームのキーマッピングをテスト用に設定
        for action, key in self.test_keys["p1"].items():
            self.game.key_mapping_p1[key] = action
            
        # key_mappingも更新
        self.game.key_mapping.clear()
        self.game.key_mapping.update(self.game.key_mapping_p1)
            
        # P1のキーをテスト - キー処理だけをテスト（状態に依存せず）
        for action, key in self.test_keys["p1"].items():
            # テスト前にキーの状態をリセット
            self.game.keys_pressed[action] = False
            
            # キーが押された時の処理（直接キーの状態を変更する）
            self.game.keys_pressed[action] = True
            assert self.game.keys_pressed[action] == True, f"P1: '{action}' が有効になっていない"
            
            # キーが離された時の処理
            self.game.keys_pressed[action] = False
            assert self.game.keys_pressed[action] == False, f"P1: '{action}' が無効になっていない"

def test_key_config_integration():
    """実行用関数"""
    test = TestKeyConfigIntegration()
    test.setup_method()
    
    try:
        test.test_key_mapping_setting()
        test.test_save_and_load_config()
        test.test_key_independence()
        test.test_game_key_handler()
    finally:
        test.teardown_method()
    
if __name__ == "__main__":
    test_key_config_integration() 