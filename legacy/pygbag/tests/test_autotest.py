import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
import sys
from game.game import Game
from game.states import AutoTestState

class TestAutoTestMode(unittest.TestCase):
    def setUp(self):
        # pygameの初期化をモック
        pygame.init = Mock()
        pygame.display.set_mode = Mock(return_value=Mock())
        pygame.display.set_caption = Mock()
        
        # スクリーンをモック
        self.screen = MagicMock()
        self.screen.get_width.return_value = 800
        self.screen.get_height.return_value = 600
        
        # ゲームインスタンスを作成
        self.game = Game(self.screen)
        
        # 自動テスト状態に設定
        self.game.change_state(AutoTestState(self.game))
    
    def test_auto_test_hud_displayed(self):
        """自動テストモードでもHUDが表示されるかテスト"""
        # draw_hudメソッドをモック
        with patch.object(self.game.current_state, 'draw_hud') as mock_draw_hud:
            # ゲームの描画を実行
            self.game.current_state.draw(self.screen)
            
            # draw_hudメソッドが呼ばれたことを確認
            mock_draw_hud.assert_called_once_with(self.screen)

    def test_auto_test_update(self):
        """自動テストモードでの更新処理が正しく行われるかテスト"""
        # 初期状態を確認
        self.assertEqual(self.game.test_timer, 0)
        
        # 更新処理を実行
        self.game.update()
        
        # テストタイマーが更新されていることを確認
        self.assertEqual(self.game.test_timer, 1)
    
    def test_auto_test_ai_control(self):
        """自動テストモードでのAI制御が正しく機能するかテスト"""
        # AI制御の結果を取得
        ai_keys = self.game.auto_test_ai_control(self.game.player1, self.game.player2, is_player1=True)
        
        # 各キーがbool型であることを確認
        for key, value in ai_keys.items():
            self.assertIsInstance(value, bool)
        
        # 必要なすべてのキーが含まれていることを確認
        expected_keys = ["up", "down", "left", "right", "weapon_a", "weapon_b", "hyper", "dash", "special", "shield"]
        for key in expected_keys:
            self.assertIn(key, ai_keys)

if __name__ == '__main__':
    unittest.main() 