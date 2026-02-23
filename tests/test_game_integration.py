import pytest
import pygame
import sys
import os
from unittest.mock import MagicMock, patch

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.player import Player
from game.projectile import BeamProjectile
from game.states import TitleState, SingleVersusGameState, PauseState


class TestGameIntegration:
    """ゲームコンポーネント間の統合をテストするクラス"""
    
    @pytest.fixture
    def setup_game(self):
        """テスト用のゲームセットアップ"""
        # pygameを初期化（テスト中は表示しない）
        pygame.init()
        screen = pygame.Surface((800, 600))
        
        # ゲームインスタンスを作成
        game = Game(screen)
        
        # テスト用に音声を無効化
        game.sounds = {}
        
        # ゲームの初期状態をリセット
        game.projectiles = []
        game.effects = []
        
        return game
    
    def test_player_projectile_collision(self, setup_game):
        """プレイヤーと弾の衝突判定のテスト"""
        game = setup_game
        
        # テスト前の状態を確認
        assert game.player1.health == 1000  # MAX_HEALTHが1000に変更されたため修正
        
        # プレイヤー2から発射される弾を作成 - プレイヤー1と完全に重なるように位置を設定
        projectile = BeamProjectile(
            game.player1.x, game.player1.y, 
            0, 10, game.player2  # 角度0度、ダメージ10、オーナーはプレイヤー2
        )
        
        # 弾をゲームに追加
        game.projectiles.append(projectile)
        
        # 当たり判定処理を実行
        game.handle_collisions()
        
        # プレイヤー1のHPが減少していることを確認
        assert game.player1.health < 1000  # MAX_HEALTHが1000に変更されたため修正
        
        # 弾が消えていることを確認
        assert len(game.projectiles) == 0
    
    def test_player_shield_blocks_projectile(self, setup_game):
        """シールドが弾をブロックするテスト"""
        game = setup_game
        
        # シールドを有効化
        game.player1.shield_duration_counter = 60
        game.player1.is_shield_active = True
        
        # テスト前の状態を確認
        initial_health = game.player1.health
        
        # プレイヤー2から発射される弾を作成
        projectile = BeamProjectile(
            game.player1.x, game.player1.y + 20, 
            0, 10, game.player2
        )
        
        # 弾をゲームに追加
        game.projectiles.append(projectile)
        
        # 当たり判定処理を実行
        game.handle_collisions()
        
        # シールド中はダメージを受けないことを確認
        assert game.player1.health == initial_health
        
        # 弾が反射されているはずなので、まだ存在することを確認
        assert len(game.projectiles) == 1
    
    def test_state_transition(self, setup_game):
        """状態遷移のテスト"""
        game = setup_game
        
        # 初期状態はTitleState
        assert isinstance(game.current_state, TitleState)
        
        # SingleVersusGameStateに遷移
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # 現在の状態がSingleVersusGameStateに変わったことを確認
        assert isinstance(game.current_state, SingleVersusGameState)
        
        # PauseStateに遷移
        pause_state = PauseState(game)
        game.change_state(pause_state, game_state)
        
        # 現在の状態がPauseStateに変わったことを確認
        assert isinstance(game.current_state, PauseState)
        
        # 前の状態が保存されていることを確認
        assert game.previous_state == game_state
    
    def test_effect_lifecycle(self, setup_game):
        """エフェクトのライフサイクルテスト"""
        game = setup_game
        
        # モックエフェクトを作成 - updateメソッドも用意
        mock_effect = MagicMock()
        mock_effect.is_dead = False
        mock_effect.update = MagicMock()  # 明示的にupdateメソッドをモック化
        
        # エフェクトをゲームに追加
        game.effects.append(mock_effect)
        
        # 直接update_game_elementsを呼び出す
        game.update_game_elements()
        
        # updateメソッドが呼ばれたことを確認
        mock_effect.update.assert_called_once()
        
        # エフェクトを死亡状態に設定
        mock_effect.is_dead = True
        
        # 再度更新処理
        game.update_game_elements()
        
        # エフェクトが削除されたことを確認
        assert len(game.effects) == 0
    
    def test_keydown_handling(self, setup_game):
        """キー入力の処理テスト"""
        game = setup_game
        
        # 現在の状態のhandle_inputメソッドをモック化
        game.current_state.handle_input = MagicMock()
        
        # キー入力をシミュレート
        game.handle_keydown(pygame.K_SPACE)
        
        # 状態のhandle_inputメソッドが呼ばれたことを確認
        game.current_state.handle_input.assert_called_once()
        
        # 引数としてキー入力イベントが渡されたことを確認
        args, _ = game.current_state.handle_input.call_args
        assert args[0].type == pygame.KEYDOWN
        assert args[0].key == pygame.K_SPACE 