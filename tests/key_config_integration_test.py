#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import time
import pygame
from pygame.locals import *
import shutil

# ゲームのモジュールをインポート
from game.constants import *
from game.game import Game

class KeyConfigIntegrationTest:
    """キーコンフィグのすべての機能を統合テストするクラス"""

    def __init__(self):
        """初期化"""
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
        
        # 元のキーマッピングを保存
        self.original_p1 = KEY_MAPPING_P1.copy()
        self.original_p2 = KEY_MAPPING_P2.copy()
        
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
        
        # キーマッピングの問題を検出・修正するためのフラグ
        self.need_key_mapping_fix = False
        
        print("キーコンフィグ統合テスト開始")
        print("=" * 60)

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
            self.need_key_mapping_fix = True
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
        
        # 元のキーマッピングに戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(self.original_p1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(self.original_p2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)

    def assert_equal(self, actual, expected, description):
        """値が一致するかテスト"""
        self.test_stats["total"] += 1
        result = actual == expected
        
        if result:
            self.test_stats["success"] += 1
            status = "成功"
        else:
            self.test_stats["failure"] += 1
            status = "失敗"
            
        self.test_results.append({
            "description": description,
            "status": status,
            "expected": str(expected),
            "actual": str(actual)
        })
        
        return result

    def assert_contains(self, container, item, description):
        """コンテナにアイテムが含まれるかテスト"""
        self.test_stats["total"] += 1
        result = item in container
        
        if result:
            self.test_stats["success"] += 1
            status = "成功"
        else:
            self.test_stats["failure"] += 1
            status = "失敗"
            
        self.test_results.append({
            "description": description,
            "status": status,
            "expected": f"'{item}' in container",
            "actual": f"{'True' if result else 'False'}"
        })
        
        return result

    def display_test_results(self):
        """テスト結果を表示"""
        print("\nテスト結果:")
        print("=" * 60)
        
        for idx, result in enumerate(self.test_results, 1):
            status_marker = "✓" if result["status"] == "成功" else "✗"
            print(f"{idx}. [{status_marker}] {result['description']}")
            if result["status"] == "失敗":
                print(f"   期待値: {result['expected']}")
                print(f"   実際値: {result['actual']}")
        
        print("=" * 60)
        print(f"合計: {self.test_stats['total']} テスト")
        print(f"成功: {self.test_stats['success']} テスト")
        print(f"失敗: {self.test_stats['failure']} テスト")
        
        success_rate = (self.test_stats["success"] / self.test_stats["total"]) * 100 if self.test_stats["total"] > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        print("=" * 60)

    def test_set_key_mapping(self):
        """キーマッピングの設定テスト"""
        print("\nテスト: すべてのアクションに対するキーマッピングの設定")
        
        # 現在のキーマッピングをデバッグ出力
        print("テスト前のKEY_MAPPING_P1:", {k: v for k, v in KEY_MAPPING_P1.items()})
        print("テスト前のKEY_MAPPING:", {k: v for k, v in KEY_MAPPING.items()})
        
        # プレイヤー1のすべてのアクションに対するテスト
        for action, key in self.test_keys["p1"].items():
            # 既存のマッピングをクリア
            for k, v in list(KEY_MAPPING_P1.items()):
                if v == action:
                    del KEY_MAPPING_P1[k]
            
            # 新しいキーを設定
            KEY_MAPPING_P1[key] = action
            
            # マッピングが正しく設定されたかテスト
            self.assert_equal(KEY_MAPPING_P1[key], action, f"P1: キー {key} に '{action}' アクションを設定")
        
        # プレイヤー2のすべてのアクションに対するテスト
        for action, key in self.test_keys["p2"].items():
            # 既存のマッピングをクリア
            for k, v in list(KEY_MAPPING_P2.items()):
                if v == action:
                    del KEY_MAPPING_P2[k]
            
            # 新しいキーを設定
            KEY_MAPPING_P2[key] = action
            
            # マッピングが正しく設定されたかテスト
            self.assert_equal(KEY_MAPPING_P2[key], action, f"P2: キー {key} に '{action}' アクションを設定")
        
        # 互換性のためのKEY_MAPPINGの更新 - ここが重要ポイント
        print("KEY_MAPPINGを更新中...")
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        # 更新後のキーマッピングをデバッグ出力
        print("更新後のKEY_MAPPING_P1:", {k: v for k, v in KEY_MAPPING_P1.items()})
        print("更新後のKEY_MAPPING:", {k: v for k, v in KEY_MAPPING.items()})
        
        # KEY_MAPPINGが更新されたかテスト
        for action, key in self.test_keys["p1"].items():
            if key in KEY_MAPPING:
                self.assert_equal(KEY_MAPPING[key], action, f"KEY_MAPPING: キー {key} に '{action}' アクションが設定されている")
            else:
                self.test_stats["total"] += 1
                self.test_stats["failure"] += 1
                self.test_results.append({
                    "description": f"KEY_MAPPING: キー {key} に '{action}' アクションが設定されている",
                    "status": "失敗",
                    "expected": f"KEY_MAPPING[{key}] == '{action}'",
                    "actual": f"キー {key} がKEY_MAPPINGに存在しない"
                })
                print(f"警告: キー {key} がKEY_MAPPINGに存在しません")
                
                # 修正を試みる
                print(f"- KEY_MAPPINGに {key} -> {action} を強制的に追加します")
                KEY_MAPPING[key] = action
                self.need_key_mapping_fix = True

    def test_save_config(self):
        """設定の保存のテスト"""
        print("\nテスト: 設定ファイルの保存")
        
        # 保存前のマッピングをデバッグ出力
        print("保存前のKEY_MAPPING_P1:", {k: v for k, v in KEY_MAPPING_P1.items()})
        print("保存前のKEY_MAPPING_P2:", {k: v for k, v in KEY_MAPPING_P2.items()})
        
        # 現在の設定を保存
        config = {
            "p1": {str(k): v for k, v in KEY_MAPPING_P1.items()},
            "p2": {str(k): v for k, v in KEY_MAPPING_P2.items()}
        }
        
        # 設定内容をデバッグ出力
        print("保存する設定:")
        print("P1:", config["p1"])
        print("P2:", config["p2"])
        
        try:
            with open("key_config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            # ファイルが存在するかテスト
            self.assert_equal(os.path.exists("key_config.json"), True, "設定ファイルが作成されている")
            
            # ファイルの内容を確認
            with open("key_config.json", "r") as f:
                saved_config = json.load(f)
            
            # 保存された設定をデバッグ出力
            print("保存された設定:")
            print("P1:", saved_config["p1"])
            print("P2:", saved_config["p2"])
            
            # P1の設定が正しいかテスト
            for action, key in self.test_keys["p1"].items():
                self.assert_contains(saved_config["p1"].values(), action, f"保存されたP1の設定に '{action}' が含まれている")
            
            # P2の設定が正しいかテスト
            for action, key in self.test_keys["p2"].items():
                self.assert_contains(saved_config["p2"].values(), action, f"保存されたP2の設定に '{action}' が含まれている")
            
            return True
        except Exception as e:
            print(f"設定の保存に失敗しました: {e}")
            self.test_stats["total"] += 1
            self.test_stats["failure"] += 1
            
            self.test_results.append({
                "description": "設定ファイルの保存",
                "status": "失敗",
                "expected": "エラーなし",
                "actual": str(e)
            })
            
            return False

    def test_load_config(self):
        """設定の読み込みのテスト"""
        print("\nテスト: 設定ファイルの読み込み")
        
        # 設定をデフォルトに戻す
        KEY_MAPPING_P1.clear()
        KEY_MAPPING_P1.update(DEFAULT_KEY_MAPPING_P1)
        KEY_MAPPING_P2.clear()
        KEY_MAPPING_P2.update(DEFAULT_KEY_MAPPING_P2)
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        try:
            # 設定ファイルを読み込む
            with open("key_config.json", "r") as f:
                config = json.load(f)
            
            print("読み込まれた設定:")
            print("P1:", config["p1"])
            print("P2:", config["p2"])
            
            # P1の設定を読み込む
            KEY_MAPPING_P1.clear()
            for k, v in config["p1"].items():
                KEY_MAPPING_P1[int(k)] = v
            
            # P2の設定を読み込む
            KEY_MAPPING_P2.clear()
            for k, v in config["p2"].items():
                KEY_MAPPING_P2[int(k)] = v
            
            # 互換性のためのKEY_MAPPINGの更新
            KEY_MAPPING.clear()
            KEY_MAPPING.update(KEY_MAPPING_P1)
            
            print("読み込み後のKEY_MAPPING_P1:", {k: v for k, v in KEY_MAPPING_P1.items()})
            print("読み込み後のKEY_MAPPING:", {k: v for k, v in KEY_MAPPING.items()})
            
            # 読み込みが正しく行われたかテスト
            # P1の設定が正しいかテスト
            for action, key in self.test_keys["p1"].items():
                try:
                    self.assert_equal(KEY_MAPPING_P1[key], action, f"読み込まれたP1の設定でキー {key} が '{action}' に設定されている")
                except KeyError:
                    self.test_stats["total"] += 1
                    self.test_stats["failure"] += 1
                    self.test_results.append({
                        "description": f"読み込まれたP1の設定でキー {key} が '{action}' に設定されている",
                        "status": "失敗",
                        "expected": f"KEY_MAPPING_P1[{key}] == '{action}'",
                        "actual": f"キー {key} がKEY_MAPPING_P1に存在しない"
                    })
                    print(f"警告: 読み込み後にキー {key} がKEY_MAPPING_P1に存在しません")
                    self.need_key_mapping_fix = True
            
            # P2の設定が正しいかテスト
            for action, key in self.test_keys["p2"].items():
                try:
                    self.assert_equal(KEY_MAPPING_P2[key], action, f"読み込まれたP2の設定でキー {key} が '{action}' に設定されている")
                except KeyError:
                    self.test_stats["total"] += 1
                    self.test_stats["failure"] += 1
                    self.test_results.append({
                        "description": f"読み込まれたP2の設定でキー {key} が '{action}' に設定されている",
                        "status": "失敗",
                        "expected": f"KEY_MAPPING_P2[{key}] == '{action}'",
                        "actual": f"キー {key} がKEY_MAPPING_P2に存在しない"
                    })
                    print(f"警告: 読み込み後にキー {key} がKEY_MAPPING_P2に存在しません")
                    self.need_key_mapping_fix = True
            
            # KEY_MAPPINGが更新されたかテスト
            for action, key in self.test_keys["p1"].items():
                try:
                    self.assert_equal(KEY_MAPPING[key], action, f"読み込み後のKEY_MAPPINGでキー {key} が '{action}' に設定されている")
                except KeyError:
                    self.test_stats["total"] += 1
                    self.test_stats["failure"] += 1
                    self.test_results.append({
                        "description": f"読み込み後のKEY_MAPPINGでキー {key} が '{action}' に設定されている",
                        "status": "失敗",
                        "expected": f"KEY_MAPPING[{key}] == '{action}'",
                        "actual": f"キー {key} がKEY_MAPPINGに存在しない"
                    })
                    print(f"警告: 読み込み後にキー {key} がKEY_MAPPINGに存在しません")
                    
                    # 修正を試みる
                    print(f"- KEY_MAPPINGに {key} -> {action} を強制的に追加します")
                    KEY_MAPPING[key] = action
                    self.need_key_mapping_fix = True
            
            return True
        except Exception as e:
            print(f"設定の読み込みに失敗しました: {e}")
            self.test_stats["total"] += 1
            self.test_stats["failure"] += 1
            
            self.test_results.append({
                "description": "設定ファイルの読み込み",
                "status": "失敗",
                "expected": "エラーなし",
                "actual": str(e)
            })
            
            return False

    def test_key_independence(self):
        """プレイヤー1と2のキー設定の独立性をテスト"""
        print("\nテスト: プレイヤー1と2のキー設定の独立性")
        
        # 共通のアクションでキーが異なることを確認
        for action in ACTION_NAMES.keys():
            p1_key = None
            p2_key = None
            
            for k, v in KEY_MAPPING_P1.items():
                if v == action:
                    p1_key = k
                    break
            
            for k, v in KEY_MAPPING_P2.items():
                if v == action:
                    p2_key = k
                    break
            
            if p1_key is not None and p2_key is not None:
                self.assert_equal(p1_key != p2_key, True, f"'{action}' アクションのP1とP2のキー設定が異なる")

    def test_game_key_handler(self):
        """ゲームのキーハンドラーのテスト"""
        print("\nテスト: ゲームのキーハンドラー")
        
        # ダミーの画面を作成
        screen = pygame.Surface((800, 600))
        
        # ゲームインスタンスを作成
        game = Game(screen)
        
        # P1のキーをテスト
        for action, key in self.test_keys["p1"].items():
            # キーが押された時の処理
            game.handle_keydown(key)
            self.assert_equal(game.keys_pressed[action], True, f"P1: キー {key} が押された時に '{action}' が有効になる")
            
            # キーが離された時の処理
            game.handle_keyup(key)
            self.assert_equal(game.keys_pressed[action], False, f"P1: キー {key} が離された時に '{action}' が無効になる")
        
        # P2のキーはゲームプレイでは使用されないため、そのテストは不要

    def try_fix_key_mapping(self):
        """キーマッピングの問題を修正しようとする"""
        if not self.need_key_mapping_fix:
            return False
        
        print("\n====== キーマッピングの修正を試みます ======")
        
        # プレイヤー1の設定を修正
        for action, key in self.test_keys["p1"].items():
            KEY_MAPPING_P1[key] = action
        
        # プレイヤー2の設定を修正
        for action, key in self.test_keys["p2"].items():
            KEY_MAPPING_P2[key] = action
        
        # KEY_MAPPINGを更新
        KEY_MAPPING.clear()
        KEY_MAPPING.update(KEY_MAPPING_P1)
        
        # 設定を保存
        config = {
            "p1": {str(k): v for k, v in KEY_MAPPING_P1.items()},
            "p2": {str(k): v for k, v in KEY_MAPPING_P2.items()}
        }
        
        try:
            with open("key_config.json", "w") as f:
                json.dump(config, f, indent=2)
            print("キーマッピングの修正を保存しました。")
            
            # ゲームのモジュールを修正するための提案
            print("\n以下の修正をゲームコードに実装することを推奨します:")
            print("1. game/game.py の load_key_config メソッドで、KEY_MAPPING_P1からKEY_MAPPINGへの更新を確実に行う")
            print("2. キーマッピングを変更する際に常にすべてのマッピング(KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPING)を同期する")
            
            # キーマッピングの読み込み問題に対する修正パッチを生成
            self.create_key_config_fix_patch()
            
            return True
        except Exception as e:
            print(f"修正の保存に失敗しました: {e}")
            return False
            
    def create_key_config_fix_patch(self):
        """キーコンフィグ読み込み問題を修正するためのパッチを作成"""
        print("\n====== キーコンフィグ修正パッチを作成します ======")
        
        # パッチスクリプトの内容
        with open("fix_key_config.py", "w") as f:
            f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import shutil
from game.constants import *

def fix_key_config():
    \"\"\"キーコンフィグの問題を修正\"\"\"
    print("キーコンフィグ修正ツール")
    print("=" * 50)
    
    # バックアップを作成
    if os.path.exists("key_config.json"):
        try:
            with open("key_config.json", "r") as f:
                config = json.load(f)
            
            shutil.copy("key_config.json", "key_config.json.backup")
            print("既存の設定ファイルをバックアップしました")
            
            print("\\n現在の設定:")
            if "p1" in config:
                print(f"P1: {config['p1']}")
            else:
                print("P1の設定がありません")
            
            if "p2" in config:
                print(f"P2: {config['p2']}")
            else:
                print("P2の設定がありません")
                
            # KEY_MAPPINGの状態を確認
            print("\\n現在のKEY_MAPPING:")
            print(f"KEY_MAPPING_P1: {KEY_MAPPING_P1}")
            print(f"KEY_MAPPING_P2: {KEY_MAPPING_P2}")
            print(f"KEY_MAPPING: {KEY_MAPPING}")
            
            # 設定ファイルを整理
            new_config = {"p1": {}, "p2": {}}
            
            # P1の設定をクリーンアップ
            if "p1" in config and config["p1"]:
                # 文字列のキーを整数に変換
                for k, v in config["p1"].items():
                    try:
                        key_int = int(k)
                        new_config["p1"][str(key_int)] = v
                    except ValueError:
                        print(f"警告: 不正なキー値 '{k}' をスキップします")
            else:
                # P1の設定がなければデフォルト値を設定
                for k, v in DEFAULT_KEY_MAPPING_P1.items():
                    new_config["p1"][str(k)] = v
                print("P1にデフォルト設定を使用します")
            
            # P2の設定をクリーンアップ
            if "p2" in config and config["p2"]:
                # 文字列のキーを整数に変換
                for k, v in config["p2"].items():
                    try:
                        key_int = int(k)
                        new_config["p2"][str(key_int)] = v
                    except ValueError:
                        print(f"警告: 不正なキー値 '{k}' をスキップします")
            else:
                # P2の設定がなければデフォルト値を設定
                for k, v in DEFAULT_KEY_MAPPING_P2.items():
                    new_config["p2"][str(k)] = v
                print("P2にデフォルト設定を使用します")
            
            # 必須アクションが設定されているか確認
            for player in ["p1", "p2"]:
                missing_actions = []
                for action in ACTION_NAMES:
                    if action not in new_config[player].values():
                        missing_actions.append(action)
                
                if missing_actions:
                    print(f"警告: {player}に{', '.join(missing_actions)}アクションが定義されていません")
                    # 不足しているアクションをデフォルト設定から補完
                    default_map = DEFAULT_KEY_MAPPING_P1 if player == "p1" else DEFAULT_KEY_MAPPING_P2
                    for action in missing_actions:
                        for k, v in default_map.items():
                            if v == action and str(k) not in new_config[player]:
                                new_config[player][str(k)] = action
                                break
            
            # 新しい設定を保存
            with open("key_config.json", "w") as f:
                json.dump(new_config, f, indent=2)
            print("\\n修正後の設定を保存しました。")
            
            # キーマッピングを更新
            # P1の設定
            KEY_MAPPING_P1.clear()
            for k, v in new_config["p1"].items():
                KEY_MAPPING_P1[int(k)] = v
            
            # P2の設定
            KEY_MAPPING_P2.clear()
            for k, v in new_config["p2"].items():
                KEY_MAPPING_P2[int(k)] = v
            
            # 互換性のために古いマッピングも更新
            KEY_MAPPING.clear()
            KEY_MAPPING.update(KEY_MAPPING_P1)
            
            print("\\n修正後のKEY_MAPPING:")
            print(f"KEY_MAPPING_P1: {KEY_MAPPING_P1}")
            print(f"KEY_MAPPING_P2: {KEY_MAPPING_P2}")
            print(f"KEY_MAPPING: {KEY_MAPPING}")
            
            print("\\nキーコンフィグの修正が完了しました。")
            
        except Exception as e:
            print(f"設定の修正に失敗しました: {e}")
            return False
    else:
        print("設定ファイルが見つかりません。新しい設定ファイルを作成します。")
        
        # デフォルト設定で新しい設定ファイルを作成
        new_config = {
            "p1": {str(k): v for k, v in DEFAULT_KEY_MAPPING_P1.items()},
            "p2": {str(k): v for k, v in DEFAULT_KEY_MAPPING_P2.items()}
        }
        
        try:
            with open("key_config.json", "w") as f:
                json.dump(new_config, f, indent=2)
            print("デフォルト設定ファイルを作成しました。")
            return True
        except Exception as e:
            print(f"設定ファイルの作成に失敗しました: {e}")
            return False

if __name__ == "__main__":
    fix_key_config()
""")
        
        print("キー設定修正スクリプト 'fix_key_config.py' を作成しました。")
        print("このスクリプトを実行すると、キーコンフィグの問題を修正できます。")

    def run_tests(self):
        """すべてのテストを実行"""
        try:
            # キーマッピングの設定テスト
            self.test_set_key_mapping()
            
            # 設定の保存テスト
            if self.test_save_config():
                # 設定の読み込みテスト
                self.test_load_config()
            
            # キー設定の独立性テスト
            self.test_key_independence()
            
            # ゲームのキーハンドラーテスト
            self.test_game_key_handler()
            
            # 修正が必要な場合
            if self.need_key_mapping_fix:
                self.try_fix_key_mapping()
            
            # テスト結果の表示
            self.display_test_results()
            
            # クリーンアップ
            self.cleanup()
            
            return self.test_stats["failure"] == 0
        except Exception as e:
            print(f"テスト実行中にエラーが発生しました: {e}")
            import traceback
            print(traceback.format_exc())
            self.cleanup()
            return False

    def cleanup(self):
        """テスト後のクリーンアップ"""
        # 設定ファイルを復元
        self.restore_config_file()
        
        # Pygameの終了
        pygame.quit()
        
        print("\nテスト完了。クリーンアップしました。")

if __name__ == "__main__":
    tester = KeyConfigIntegrationTest()
    success = tester.run_tests()
    sys.exit(0 if success else 1) 