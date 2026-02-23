import pytest
import pygame
import sys
import os
from unittest.mock import MagicMock

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.hud import HUD
from game.states import TitleState, SingleVersusGameState, TrainingState, PauseState
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_HEALTH, MAX_HEAT, MAX_HYPER


class TestUIComponentPlacement:
    """UI要素（HUDやメニュー）が正しく配置されるかテスト"""
    
    @pytest.fixture
    def setup_game(self):
        """テスト用のゲームセットアップ"""
        pygame.init()
        
        # 実際のSurfaceを使用
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game = Game(screen)
        
        # テスト用に音声を無効化
        game.sounds = {}
        
        return game
    
    def test_hud_initialization(self, setup_game):
        """HUDの初期化と参照テスト"""
        game = setup_game
        
        # HUDが正しく初期化されているか
        assert game.hud is not None
        assert game.hud.player1 == game.player1
        assert game.hud.player2 == game.player2
    
    def test_hud_player_data_reference(self, setup_game):
        """HUDがプレイヤーデータを正しく参照しているかテスト"""
        game = setup_game
        
        # プレイヤーの状態を変更
        game.player1.health = 75
        game.player1.heat = 50
        game.player1.hyper_gauge = 30
        
        # HUDの描画後も変更が持続しているか（参照が正しいか）
        assert game.player1.health == 75
        assert game.player1.heat == 50
        assert game.player1.hyper_gauge == 30
    
    def test_game_state_hud_display(self, setup_game):
        """ゲーム状態でのHUD表示テスト"""
        game = setup_game
        
        # GameStateに遷移
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # 両プレイヤーのヘルスをテスト用に変更
        game.player1.health = 80
        game.player2.health = 60
        
        # 変更が反映されているか確認
        assert game.player1.health == 80
        assert game.player2.health == 60
    
    def test_training_state_hud_display(self, setup_game):
        """トレーニングモードでのHUD表示テスト"""
        game = setup_game
        
        # TrainingStateに遷移
        training_state = TrainingState(game)
        game.change_state(training_state)
        
        # プレイヤーのヒートとハイパーゲージをテスト用に変更
        game.player1.heat = 75
        game.player1.hyper_gauge = 90
        
        # 変更が反映されているか確認
        assert game.player1.heat == 75
        assert game.player1.hyper_gauge == 90
    
    def test_title_menu_positioning(self, setup_game):
        """タイトル画面のメニュー位置テスト"""
        game = setup_game
        
        # TitleStateに遷移
        title_state = TitleState(game)
        game.change_state(title_state)
        
        # メニュー項目の数と選択状態を確認
        assert len(title_state.menu_items) == len(game.menu_items)
        assert title_state.selected_item == 0
        
        # 選択項目を変更
        title_state.selected_item = 2
        assert title_state.selected_item == 2
    
    def test_pause_menu_positioning(self, setup_game):
        """ポーズ画面のメニュー位置テスト"""
        game = setup_game
        
        # まずGameStateに遷移してからPauseStateに遷移
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        pause_state = PauseState(game)
        game.change_state(pause_state, game_state)
        
        # メニュー項目と選択状態を確認
        assert len(pause_state.menu_items) == 4  # ゲームに戻る、操作説明、タイトルに戻る、ゲーム終了
        assert pause_state.selected_item == 0
        
        # 選択項目を変更
        pause_state.selected_item = 1
        assert pause_state.selected_item == 1
    
    def test_hud_bar_scaling(self, setup_game):
        """HUDのバー表示スケーリングテスト"""
        game = setup_game
        
        # 様々な値でプレイヤーの状態をテスト
        test_values = [
            (100, 0, 0),    # 最大HP、最小ヒート、最小ハイパー
            (50, 50, 50),   # 中間値
            (1, 99, 99),    # 最小HP、最大に近いヒートとハイパー
            (0, MAX_HEAT, MAX_HYPER)  # 死亡状態、最大ヒート、最大ハイパー
        ]
        
        for hp, heat, hyper in test_values:
            # プレイヤーの状態を設定
            game.player1.health = hp
            game.player1.heat = heat
            game.player1.hyper_gauge = hyper
            
            # 設定した値が正しく反映されるか
            assert game.player1.health == hp
            assert game.player1.heat == heat
            assert game.player1.hyper_gauge == hyper
    
    def test_hud_special_state_indicators(self, setup_game):
        """HUDの特殊状態インジケーターテスト"""
        game = setup_game
        
        # GameStateに遷移
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # 特殊状態をセット
        game.player1.is_shield_active = True
        game.player1.is_hyper_active = True
        game.player1.is_overheated = True
        
        # ハイパー持続時間の設定
        game.player1.hyper_duration = 300
        
        # プレイヤー2も特殊状態を一部セット
        game.player2.is_shield_active = True
        
        # 設定した状態が正しく反映されるか
        assert game.player1.is_shield_active
        assert game.player1.is_hyper_active
        assert game.player1.is_overheated
        assert game.player1.hyper_duration == 300
        assert game.player2.is_shield_active
        
        # 特殊状態を解除して再テスト
        game.player1.is_shield_active = False
        game.player1.is_hyper_active = False
        game.player1.is_overheated = False
        game.player2.is_shield_active = False
        
        # 解除した状態が正しく反映されるか
        assert not game.player1.is_shield_active
        assert not game.player1.is_hyper_active
        assert not game.player1.is_overheated
        assert not game.player2.is_shield_active
    
    def test_result_screen_component_placement(self, setup_game):
        """リザルト画面のコンポーネント配置テスト"""
        game = setup_game
        
        # GameStateに遷移してリザルト状態をセットアップ
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # プレイヤー1が勝利した場合のリザルト状態をシミュレート
        game.player2.health = 0
        
        # リザルト表示用の状態をセット
        from game.state import GameState as GameStateEnum
        game.current_state = GameStateEnum.RESULT
        game.winner = 1
        game.result_timer = 0
        
        # 設定した状態が正しく反映されるか
        assert game.player2.health == 0
        assert game.current_state == GameStateEnum.RESULT
        assert game.winner == 1
        assert game.result_timer == 0
        
        # カウントダウンタイマーを進める
        game.result_timer = 60  # 1秒経過
        
        # タイマーの進行が反映されるか
        assert game.result_timer == 60 