import pytest
import pygame
import sys
import os
import time

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.states import AutoTestState, TitleState
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class TestAutoTestTimeout:
    """自動テストモードのタイムアウト後の状態遷移テスト"""
    
    @pytest.fixture
    def setup_game(self):
        """テスト用のゲームセットアップ"""
        pygame.init()
        pygame.mixer.init()
        
        # 画面サーフェス作成（実際には表示されない）
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        game = Game(screen)
        
        # テスト用に音声を無効化
        game.sounds = {}
        
        # AutoTestStateに変更
        game.change_state(AutoTestState(game))
        
        # テストのために短い時間に設定
        game.test_duration = 10  # 非常に短いテスト時間（10フレーム）
        
        return game
    
    def test_auto_test_timeout_transition(self, setup_game):
        """自動テストモードのタイムアウト後、タイトル画面への遷移をテスト"""
        game = setup_game
        
        # 初期状態を確認
        assert game.current_state.__class__.__name__ == "AutoTestState"
        assert game.test_timer == 0
        assert game.test_duration == 10
        
        # タイムアウト直前まで更新
        for _ in range(9):
            game.update()
            assert game.current_state.__class__.__name__ == "AutoTestState"
        
        # タイムアウトして状態遷移が発生するフレーム
        try:
            game.update()
            # 状態がTitleStateに変わっているはず
            assert game.current_state.__class__.__name__ == "TitleState"
            test_passed = True
        except Exception as e:
            pytest.fail(f"自動テストからタイトル画面への遷移時にエラー発生: {e}")
            test_passed = False
        
        assert test_passed, "自動テストモードからの状態遷移テストに失敗しました"
    
    def test_auto_test_game_over_transition(self, setup_game):
        """プレイヤーのHPが0になった時のタイトル画面への遷移をテスト"""
        game = setup_game
        
        # テスト時間を無限に設定（HP0による終了をテストするため）
        game.test_duration = float('inf')
        
        # 初期状態を確認
        assert game.current_state.__class__.__name__ == "AutoTestState"
        
        # プレイヤー1のHPを0に設定
        game.player1.health = 0
        
        try:
            # 更新（ここで状態が変わるはず）
            game.update()
            
            # 結果画面に遷移しているはず
            assert game.current_state.__class__.__name__ == "ResultState" or \
                   game.current_state.__class__.__name__ == "TitleState"
            
            # 勝者が設定されているはず
            if game.current_state.__class__.__name__ == "ResultState":
                assert game.winner == 2  # プレイヤー2の勝利
            
            test_passed = True
        except Exception as e:
            pytest.fail(f"ゲームオーバー時の状態遷移でエラー発生: {e}")
            test_passed = False
        
        assert test_passed, "ゲームオーバー時の状態遷移テストに失敗しました"
    
    def test_state_preservation_after_transition(self, setup_game):
        """状態遷移後もゲームオブジェクトの整合性が保たれているかテスト"""
        game = setup_game
        
        # タイムアウトさせて状態遷移を発生
        for _ in range(10):
            game.update()
        
        # タイトル画面に戻った後の状態確認
        assert game.current_state.__class__.__name__ == "TitleState"
        
        # タイトル画面での操作をシミュレート
        try:
            # 画面描画
            game.draw()
            
            # メニュー選択操作（下キーを押す）
            event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
            game.current_state.handle_input(event)
            
            # 更新と描画
            game.update()
            game.draw()
            
            test_passed = True
        except Exception as e:
            pytest.fail(f"タイトル画面への遷移後の操作でエラー発生: {e}")
            test_passed = False
        
        assert test_passed, "状態遷移後の操作テストに失敗しました" 