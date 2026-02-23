import pytest
import pygame
import sys
import os
import math
from unittest.mock import MagicMock

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.player import Player
from game.arena import Arena
from game.constants import PLAYER_SPEED, PLAYER_DASH_SPEED, MAX_HEALTH, MAX_HEAT, MAX_HYPER, HEAT_DECREASE_RATE


class TestPlayerIntegration:
    """プレイヤーと他のコンポーネントの統合テスト"""
    
    @pytest.fixture
    def setup_game_and_players(self):
        """ゲームとプレイヤーのセットアップ"""
        pygame.init()
        screen = pygame.Surface((800, 600))
        game = Game(screen)
        
        # テスト用に音声を無効化
        game.sounds = {}
        
        # アリーナを作成
        arena = Arena()
        
        # プレイヤーの初期位置と状態を確認
        assert game.player1.x == 640 - 100  # ARENA_CENTER_X - 100
        assert game.player1.y == 360  # ARENA_CENTER_Y
        assert game.player1.health == MAX_HEALTH
        assert game.player1.heat == 0
        assert game.player1.hyper_gauge == 0
        
        return {
            'game': game,
            'player1': game.player1,
            'player2': game.player2,
            'arena': arena
        }
    
    def test_player_movement(self, setup_game_and_players):
        """プレイヤーの移動テスト"""
        data = setup_game_and_players
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # 初期位置を記録
        initial_x = player.x
        initial_y = player.y
        
        # 右に移動
        keys = {
            "up": False, "down": False, "left": False, "right": True,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # プレイヤーを更新
        player.update(keys, arena, opponent)
        
        # 右に移動したことを確認
        assert player.x > initial_x
        assert player.y == initial_y
        assert player.x - initial_x == PLAYER_SPEED
        
        # 斜め移動（右下）
        keys["down"] = True
        initial_x = player.x
        initial_y = player.y
        
        player.update(keys, arena, opponent)
        
        # 斜め移動は速度が正規化されるため、距離は直接比較できない
        # sqrt(2)/2 * PLAYER_SPEED に近い値になるはず
        expected_diagonal_distance = PLAYER_SPEED / math.sqrt(2)
        actual_x_distance = player.x - initial_x
        actual_y_distance = player.y - initial_y
        
        # 浮動小数点誤差を考慮して近似値を確認
        assert abs(actual_x_distance - expected_diagonal_distance) < 0.1
        assert abs(actual_y_distance - expected_diagonal_distance) < 0.1
    
    def test_player_dash(self, setup_game_and_players):
        """プレイヤーのダッシュテスト"""
        data = setup_game_and_players
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # 初期位置を記録
        initial_x = player.x
        
        # 右にダッシュ
        keys = {
            "up": False, "down": False, "left": False, "right": True,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": True, "special": False, "shield": False
        }
        
        # ダッシュ前の状態を確認
        assert player.is_dashing == False
        assert player.heat == 0
        
        # プレイヤーを更新
        player.update(keys, arena, opponent)
        
        # ダッシュ状態になっていることを確認
        assert player.is_dashing == True
        
        # ダッシュによる移動距離を確認
        assert player.x - initial_x == PLAYER_DASH_SPEED
        
        # ヒートゲージが上昇していることを確認
        assert player.heat > 0
    
    def test_player_weapon_fire(self, setup_game_and_players):
        """プレイヤーの武器発射テスト"""
        data = setup_game_and_players
        game = data['game']
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # 初期状態を確認
        assert len(game.projectiles) == 0
        
        # 武器Aを発射
        keys = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": True, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # プレイヤーを更新
        player.update(keys, arena, opponent)
        
        # 弾が発射されていることを確認
        assert len(game.projectiles) == 1
        assert game.projectiles[0].owner == player
    
    def test_player_hyper_mode(self, setup_game_and_players):
        """プレイヤーのハイパーモードテスト"""
        data = setup_game_and_players
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # ハイパーゲージをテスト用に設定
        player.hyper_gauge = 100
        
        # ハイパーモードを有効化
        keys = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": True, 
            "dash": False, "special": False, "shield": False
        }
        
        # ハイパーモード前の状態を確認
        assert player.is_hyper_active == False
        
        # プレイヤーを更新
        player.update(keys, arena, opponent)
        
        # ハイパーモードが有効になっていることを確認
        assert player.is_hyper_active == True
        
        # ハイパーゲージが消費されていることを確認
        assert player.hyper_gauge < 100
    
    def test_player_shield(self, setup_game_and_players):
        """プレイヤーのシールドテスト"""
        data = setup_game_and_players
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # ハイパーゲージをテスト用に設定
        player.hyper_gauge = 100
        
        # シールドを有効化
        keys = {
            "up": False, "down": False, "left": False, "right": False,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": True
        }
        
        # シールド前の状態を確認
        assert player.is_shield_active == False
        assert player.shield_duration_counter == 0
        
        # プレイヤーを更新
        player.update(keys, arena, opponent)
        
        # シールドが有効になっていることを確認
        assert player.is_shield_active == True
        assert player.shield_duration_counter > 0
        
        # ハイパーゲージが消費されていることを確認
        assert player.hyper_gauge < 100
    
    def test_heat_and_overheat(self, setup_game_and_players):
        """ヒートゲージとオーバーヒート機能のテスト
        
        テスト項目:
        1. 通常時のダッシュ開始
        2. ダッシュによるヒート上昇
        3. 200%到達時の状態確認（ダッシュ継続可、再開始不可）
        4. ダッシュ解除後の再ダッシュ不可状態の確認
        5. ヒート減少後（200%未満）の再ダッシュ可能状態の確認
        6. 300%到達時の強制ダッシュ解除
        """
        data = setup_game_and_players
        player = data['player1']
        arena = data['arena']
        opponent = data['player2']
        
        # オーバーヒート設定を初期化
        player.overheat_cooldown = 100  # オーバーヒート解除しきい値を100に設定
        player.is_overheated = False
        
        # ヒートゲージを0に設定
        player.heat = 0
        
        # ダッシュキー入力
        keys_dash_on = {
            "up": False, "down": False, "left": False, "right": True,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": True, "special": False, "shield": False
        }
        
        # ダッシュキー解除
        keys_dash_off = {
            "up": False, "down": False, "left": False, "right": True,
            "weapon_a": False, "weapon_b": False, "hyper": False, 
            "dash": False, "special": False, "shield": False
        }
        
        # 1. 通常時のダッシュ開始
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == True
        assert player.heat < 200
        
        # 2. ダッシュによるヒート上昇をシミュレート
        # 190%まで上昇させる
        player.heat = 190
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == True
        assert player.heat >= 190
        
        # 3. 200%到達時の状態確認
        player.heat = 210  # 200%以上に設定
        player.is_dashing = True  # ダッシュ中と仮定
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == True  # 既に開始したダッシュは継続できる
        
        # 4. ダッシュ解除後の再ダッシュ不可状態の確認
        player.update(keys_dash_off, arena, opponent)  # ダッシュ解除
        assert player.is_dashing == False
        # 再度ダッシュ開始を試みる
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == False  # 200%以上なので再ダッシュ不可
        
        # 5. ヒート減少後の再ダッシュ可能状態の確認
        player.heat = 190  # 200%未満に減少
        player.dash_cooldown = 0  # ダッシュクールダウンを0に設定（確実にダッシュ可能な状態に）
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == True  # 再ダッシュ可能
        
        # 6. 300%到達時の強制ダッシュ解除
        player.heat = MAX_HEAT  # 300%に設定
        player.is_dashing = True  # ダッシュ中と仮定
        player.is_overheated = False  # オーバーヒート状態をリセット
        
        # 強制的にMAX_HEATとダッシュがONの状態から更新
        player.update(keys_dash_on, arena, opponent)
        
        # オーバーヒート状態になっていることを確認
        assert player.is_overheated == True
        # ダッシュが解除されていることを確認
        assert player.is_dashing == False
        
        # ヒートがMAX_HEAT以上であることを確認 (1フレームで減少するため完全に等しくない可能性がある)
        assert player.heat >= MAX_HEAT - HEAT_DECREASE_RATE
        
        # 再度ダッシュを試みても失敗することを確認
        player.update(keys_dash_on, arena, opponent)
        assert player.is_dashing == False 