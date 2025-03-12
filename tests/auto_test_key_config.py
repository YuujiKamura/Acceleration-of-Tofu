#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import sys
import os
import json
import time
from pygame.locals import *

# ゲームのモジュールをインポート
from game.constants import *
from game.state import GameState
from game.game import Game

class KeyConfigTester:
    def __init__(self):
        # Pygameの初期化
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("キーコンフィグ自動テスト")
        self.clock = pygame.time.Clock()
        
        # ゲームの初期化
        self.game = Game(self.screen)
        
        # ログファイル
        self.log_file = open("key_config_test.log", "w", encoding="utf-8")
        
        # キー設定のバックアップ
        self.backup_key_mappings()
        
        # テストフラグ
        self.test_results = {
            "save_load": False,
            "p1_config": False,
            "p2_config": False,
            "key_input": False
        }
        
        # テスト用のキー
        self.test_keys = {
            "p1_up": pygame.K_t,      # Tキー
            "p1_down": pygame.K_g,    # Gキー
            "p2_up": pygame.K_y,      # Yキー
            "p2_down": pygame.K_h     # Hキー
        }
        
        self.log("キーコンフィグ自動テスト開始")
    
    def log(self, message):
        """ログメッセージを出力"""
        print(message)
        self.log_file.write(f"{message}\n")
        self.log_file.flush()
    
    def backup_key_mappings(self):
        """現在のキー設定をバックアップ"""
        self.backup_p1 = KEY_MAPPING_P1.copy()
        self.backup_p2 = KEY_MAPPING_P2.copy()
        self.log("現在のキー設定をバックアップしました")
    
    def restore_key_mappings(self):
        """バックアップしたキー設定を復元"""
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(self.backup_p1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(self.backup_p2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        self.log("キー設定を元に戻しました")
    
    def test_save_load(self):
        """設定の保存と読み込みをテスト"""
        self.log("\n=== テスト1: 設定の保存と読み込み ===")
        
        # 元の設定を退避
        original_p1 = KEY_MAPPING_P1.copy()
        original_p2 = KEY_MAPPING_P2.copy()
        
        # テスト用の設定に変更
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1[self.test_keys["p1_up"]] = "up"
        KEY_MAPPING_P1[self.test_keys["p1_down"]] = "down"
        
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2[self.test_keys["p2_up"]] = "up"
        KEY_MAPPING_P2[self.test_keys["p2_down"]] = "down"
        
        # 互換性のために古いマッピングも更新
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        self.log("テスト用のキー設定に変更しました")
        self.log(f"P1のキー: up={self.test_keys['p1_up']}, down={self.test_keys['p1_down']}")
        self.log(f"P2のキー: up={self.test_keys['p2_up']}, down={self.test_keys['p2_down']}")
        
        # 設定を保存
        self.game.save_key_config()
        self.log("設定を保存しました")
        
        # 設定をデフォルトに戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        self.log("設定をデフォルトに戻しました")
        
        # 設定を読み込み
        self.game.load_key_config()
        self.log("設定を読み込みました")
        
        # テスト用の設定が正しく読み込まれたか確認
        p1_up_ok = self.test_keys["p1_up"] in KEY_MAPPING_P1 and KEY_MAPPING_P1[self.test_keys["p1_up"]] == "up"
        p1_down_ok = self.test_keys["p1_down"] in KEY_MAPPING_P1 and KEY_MAPPING_P1[self.test_keys["p1_down"]] == "down"
        p2_up_ok = self.test_keys["p2_up"] in KEY_MAPPING_P2 and KEY_MAPPING_P2[self.test_keys["p2_up"]] == "up"
        p2_down_ok = self.test_keys["p2_down"] in KEY_MAPPING_P2 and KEY_MAPPING_P2[self.test_keys["p2_down"]] == "down"
        
        # 結果を表示
        self.log(f"P1のup設定が正しく読み込まれた: {'OK' if p1_up_ok else 'NG'}")
        self.log(f"P1のdown設定が正しく読み込まれた: {'OK' if p1_down_ok else 'NG'}")
        self.log(f"P2のup設定が正しく読み込まれた: {'OK' if p2_up_ok else 'NG'}")
        self.log(f"P2のdown設定が正しく読み込まれた: {'OK' if p2_down_ok else 'NG'}")
        
        # KEY_MAPPING（古いマッピング）が更新されたか確認
        mapping_updated = self.test_keys["p1_up"] in KEY_MAPPING and KEY_MAPPING[self.test_keys["p1_up"]] == "up"
        self.log(f"古いキーマッピングも更新された: {'OK' if mapping_updated else 'NG'}")
        
        # 元の設定に戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(original_p1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(original_p2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        # テスト結果
        test_success = p1_up_ok and p1_down_ok and p2_up_ok and p2_down_ok and mapping_updated
        self.test_results["save_load"] = test_success
        self.log(f"設定の保存と読み込みテスト: {'成功' if test_success else '失敗'}")
        
        return test_success
    
    def test_key_config_screen(self):
        """キーコンフィグ画面の動作をシミュレート"""
        self.log("\n=== テスト2: キーコンフィグ画面の動作 ===")
        
        # 元の設定を退避
        original_p1 = KEY_MAPPING_P1.copy()
        original_p2 = KEY_MAPPING_P2.copy()
        
        # キーコンフィグ状態をセット
        self.game.state = GameState.KEY_CONFIG
        self.game.key_config_player = 1
        self.game.key_config_selected_item = 0  # "up"を選択
        self.game.waiting_for_key_input = False
        
        self.log("P1のキーコンフィグ画面に移動")
        
        # 決定キーを押してキー入力待ち状態にする
        self.log("決定キーを押してキー入力待ち状態に")
        self.game.handle_keydown(pygame.K_z)  # Zキー（決定）を押す
        
        # キー入力待ち状態になったか確認
        p1_waiting = self.game.waiting_for_key_input
        self.log(f"P1のキー入力待ち状態: {'OK' if p1_waiting else 'NG'}")
        
        # テスト用のキーを押す
        self.log(f"テスト用のキー（{self.test_keys['p1_up']}）を押す")
        self.game.handle_keydown(self.test_keys["p1_up"])
        
        # キー設定が変更されたか確認
        p1_key_changed = self.test_keys["p1_up"] in KEY_MAPPING_P1 and KEY_MAPPING_P1[self.test_keys["p1_up"]] == "up"
        self.log(f"P1のキー設定が変更された: {'OK' if p1_key_changed else 'NG'}")
        
        # P2に切り替え
        self.log("P2のキーコンフィグに切り替え")
        self.game.handle_keydown(pygame.K_RIGHT)  # 右キーでP2に切り替え
        
        # P2になったか確認
        p2_selected = self.game.key_config_player == 2
        self.log(f"P2に切り替わった: {'OK' if p2_selected else 'NG'}")
        
        # P2の決定キーを押してキー入力待ち状態にする
        self.log("P2の決定キーを押してキー入力待ち状態に")
        self.game.handle_keydown(pygame.K_z)  # Zキー（決定）を押す
        
        # キー入力待ち状態になったか確認
        p2_waiting = self.game.waiting_for_key_input
        self.log(f"P2のキー入力待ち状態: {'OK' if p2_waiting else 'NG'}")
        
        # テスト用のキーを押す
        self.log(f"テスト用のキー（{self.test_keys['p2_up']}）を押す")
        self.game.handle_keydown(self.test_keys["p2_up"])
        
        # キー設定が変更されたか確認
        p2_key_changed = self.test_keys["p2_up"] in KEY_MAPPING_P2 and KEY_MAPPING_P2[self.test_keys["p2_up"]] == "up"
        self.log(f"P2のキー設定が変更された: {'OK' if p2_key_changed else 'NG'}")
        
        # 戻るキーを押して設定を保存
        self.log("戻るキーを押して設定を保存")
        self.game.handle_keydown(pygame.K_x)  # Xキー（戻る）を押す
        
        # 設定ファイルが作成されたか確認
        config_file_exists = os.path.exists("key_config.json")
        self.log(f"設定ファイルが作成された: {'OK' if config_file_exists else 'NG'}")
        
        # 元の設定に戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(original_p1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(original_p2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        # ゲーム状態をタイトルに戻す
        self.game.state = GameState.TITLE
        
        # テスト結果
        test_success = p1_waiting and p1_key_changed and p2_selected and p2_waiting and p2_key_changed and config_file_exists
        self.test_results["p1_config"] = p1_waiting and p1_key_changed
        self.test_results["p2_config"] = p2_selected and p2_waiting and p2_key_changed
        self.log(f"キーコンフィグ画面テスト: {'成功' if test_success else '失敗'}")
        
        return test_success
    
    def test_key_input(self):
        """キー入力の処理をテスト"""
        self.log("\n=== テスト3: キー入力処理 ===")
        
        # 元の設定を退避
        original_p1 = KEY_MAPPING_P1.copy()
        original_p2 = KEY_MAPPING_P2.copy()
        
        # テスト用の設定に変更
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1[self.test_keys["p1_up"]] = "up"
        KEY_MAPPING_P1[self.test_keys["p1_down"]] = "down"
        
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2[self.test_keys["p2_up"]] = "up"
        KEY_MAPPING_P2[self.test_keys["p2_down"]] = "down"
        
        # 互換性のために古いマッピングも更新
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        self.log("テスト用のキー設定に変更しました")
        
        # ゲームモードに切り替え
        self.game.state = GameState.GAME
        self.log("ゲームモードに切り替え")
        
        # P1のキーを押す
        self.log(f"P1のupキー（{self.test_keys['p1_up']}）を押す")
        self.game.handle_keydown(self.test_keys["p1_up"])
        
        # キー状態が更新されたか確認
        p1_key_registered = self.game.keys_pressed["up"]
        self.log(f"P1のupキーが認識された: {'OK' if p1_key_registered else 'NG'}")
        
        # キーを離す
        self.game.handle_keyup(self.test_keys["p1_up"])
        
        # キー状態が更新されたか確認
        p1_key_released = not self.game.keys_pressed["up"]
        self.log(f"P1のupキーが解除された: {'OK' if p1_key_released else 'NG'}")
        
        # P2のキーは影響しないことを確認
        self.log(f"P2のupキー（{self.test_keys['p2_up']}）を押す")
        self.game.handle_keydown(self.test_keys["p2_up"])
        
        # P1のキー設定には影響しないはず
        p2_key_independent = not self.game.keys_pressed["up"]
        self.log(f"P2のキーがP1に影響しない: {'OK' if p2_key_independent else 'NG'}")
        
        # キーを離す
        self.game.handle_keyup(self.test_keys["p2_up"])
        
        # 元の設定に戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(original_p1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(original_p2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        # ゲーム状態をタイトルに戻す
        self.game.state = GameState.TITLE
        
        # テスト結果
        test_success = p1_key_registered and p1_key_released and p2_key_independent
        self.test_results["key_input"] = test_success
        self.log(f"キー入力処理テスト: {'成功' if test_success else '失敗'}")
        
        return test_success
    
    def check_configuration_file(self):
        """設定ファイルの内容を確認"""
        self.log("\n=== 設定ファイルの内容確認 ===")
        
        if not os.path.exists("key_config.json"):
            self.log("設定ファイルが存在しません")
            return False
        
        try:
            with open("key_config.json", "r") as f:
                config = json.load(f)
            
            self.log("設定ファイルの内容:")
            self.log(json.dumps(config, indent=2))
            
            # P1とP2の設定が含まれているか確認
            if "p1" not in config or "p2" not in config:
                self.log("P1またはP2の設定が含まれていません")
                return False
            
            # 各プレイヤーに必要な設定が含まれているか確認
            p1_actions = set()
            p2_actions = set()
            
            for k, v in config["p1"].items():
                p1_actions.add(v)
            
            for k, v in config["p2"].items():
                p2_actions.add(v)
            
            required_actions = {"up", "down", "left", "right", "weapon_a", "weapon_b"}
            p1_complete = required_actions.issubset(p1_actions)
            p2_complete = required_actions.issubset(p2_actions)
            
            self.log(f"P1の必要な設定が全て含まれている: {'OK' if p1_complete else 'NG'}")
            self.log(f"P2の必要な設定が全て含まれている: {'OK' if p2_complete else 'NG'}")
            
            return p1_complete and p2_complete
            
        except Exception as e:
            self.log(f"設定ファイルの読み込みに失敗しました: {e}")
            return False
    
    def run_tests(self):
        """全てのテストを実行"""
        self.log("\n===== キーコンフィグ機能の自動テスト開始 =====")
        
        # テスト1: 設定の保存と読み込み
        self.test_save_load()
        
        # テスト2: キーコンフィグ画面の動作
        self.test_key_config_screen()
        
        # テスト3: キー入力の処理
        self.test_key_input()
        
        # 設定ファイルの内容確認
        self.check_configuration_file()
        
        # テスト結果のサマリーを表示
        self.log("\n===== テスト結果サマリー =====")
        self.log(f"1. 設定の保存と読み込み: {'成功' if self.test_results['save_load'] else '失敗'}")
        self.log(f"2. P1のキーコンフィグ: {'成功' if self.test_results['p1_config'] else '失敗'}")
        self.log(f"3. P2のキーコンフィグ: {'成功' if self.test_results['p2_config'] else '失敗'}")
        self.log(f"4. キー入力処理: {'成功' if self.test_results['key_input'] else '失敗'}")
        
        all_success = all(self.test_results.values())
        self.log(f"\n総合結果: {'全てのテストが成功しました！' if all_success else '一部のテストが失敗しました。'}")
        
        if not all_success:
            self.log("\n問題のある部分:")
            if not self.test_results["save_load"]:
                self.log("- 設定の保存と読み込みに問題があります。save_key_configとload_key_config関数を確認してください。")
            if not self.test_results["p1_config"]:
                self.log("- P1のキーコンフィグ処理に問題があります。handle_keydown関数のKEY_CONFIG状態の処理を確認してください。")
            if not self.test_results["p2_config"]:
                self.log("- P2のキーコンフィグ処理に問題があります。プレイヤー切り替えとKEY_MAPPING_P2の更新を確認してください。")
            if not self.test_results["key_input"]:
                self.log("- キー入力処理に問題があります。handle_keydownとhandle_keyup関数を確認してください。")
        
        # 元の設定に戻す
        self.restore_key_mappings()
        
        # ログを閉じる
        self.log_file.close()
        
        return all_success
    
    def run_interactive_test(self):
        """対話的なキー入力テスト"""
        self.log("\n===== 対話的なキー入力テスト =====")
        self.log("各種キーを押して、正しく認識されるかを確認します。ESCキーで終了します。")
        
        # フォント
        font = pygame.font.SysFont(None, 24)
        
        running = True
        while running:
            # キー入力
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    else:
                        # キー情報を表示
                        key_name = pygame.key.name(event.key)
                        self.log(f"キー押下: {event.key} ({key_name})")
                        
                        # P1のマッピング
                        p1_action = "なし"
                        if event.key in KEY_MAPPING_P1:
                            p1_action = KEY_MAPPING_P1[event.key]
                            p1_action_name = ACTION_NAMES.get(p1_action, p1_action)
                            self.log(f"  P1のアクション: {p1_action} ({p1_action_name})")
                        else:
                            self.log("  P1のアクション: なし")
                        
                        # P2のマッピング
                        p2_action = "なし"
                        if event.key in KEY_MAPPING_P2:
                            p2_action = KEY_MAPPING_P2[event.key]
                            p2_action_name = ACTION_NAMES.get(p2_action, p2_action)
                            self.log(f"  P2のアクション: {p2_action} ({p2_action_name})")
                        else:
                            self.log("  P2のアクション: なし")
                        
                        # 古いマッピング
                        old_action = "なし"
                        if event.key in KEY_MAPPING:
                            old_action = KEY_MAPPING[event.key]
                            old_action_name = ACTION_NAMES.get(old_action, old_action)
                            self.log(f"  旧マッピング: {old_action} ({old_action_name})")
                        else:
                            self.log("  旧マッピング: なし")
            
            # 画面クリア
            self.screen.fill((0, 0, 0))
            
            # 現在のキーマッピングを表示
            title_text = font.render("キーコンフィグテスト - 任意のキーを押してください (ESCで終了)", True, (255, 255, 255))
            self.screen.blit(title_text, (20, 20))
            
            y = 50
            self.screen.blit(font.render("プレイヤー1のキーマッピング:", True, (255, 255, 0)), (20, y))
            y += 25
            
            for action, name in ACTION_NAMES.items():
                key_name = "未設定"
                for k, v in KEY_MAPPING_P1.items():
                    if v == action:
                        key_name = pygame.key.name(k)
                        break
                
                text = font.render(f"{name}: {key_name}", True, (255, 255, 255))
                self.screen.blit(text, (40, y))
                y += 20
            
            y += 20
            self.screen.blit(font.render("プレイヤー2のキーマッピング:", True, (255, 255, 0)), (20, y))
            y += 25
            
            for action, name in ACTION_NAMES.items():
                key_name = "未設定"
                for k, v in KEY_MAPPING_P2.items():
                    if v == action:
                        key_name = pygame.key.name(k)
                        break
                
                text = font.render(f"{name}: {key_name}", True, (255, 255, 255))
                self.screen.blit(text, (40, y))
                y += 20
            
            # 画面更新
            pygame.display.flip()
            self.clock.tick(30)
        
        self.log("対話的なテストを終了しました")

if __name__ == "__main__":
    tester = KeyConfigTester()
    
    try:
        tester.run_tests()
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
    finally:
        pygame.quit()
        sys.exit() 