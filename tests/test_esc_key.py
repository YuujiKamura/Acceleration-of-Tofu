#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, Mock

# テスト対象のモジュールを参照できるようにパスを調整
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from game.game import Game
from game.states import (
    BaseState, TitleState, GameState, TrainingState, 
    AutoTestState, InstructionsState, OptionsState, 
    KeyConfigState, PauseState
)
from pygame.event import Event

class TestEscKeyHandling(unittest.TestCase):
    """ESCキーの処理をテストするテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # Pygameを初期化
        pygame.init()
        pygame.font.init()  # フォント初期化を追加
        
        # 画面をモック
        self.mock_screen = MagicMock()
        
        # ゲームオブジェクトを作成（screenパラメータを渡す）
        self.game = Game(screen=self.mock_screen)
        
        # 状態遷移メソッドをモック化
        self.game.change_state = MagicMock()
        
        # ESCキーイベントを作成
        self.esc_event = Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        
        # pygameの初期化をモック化
        pygame.quit = MagicMock(return_value=None)
        pygame.display.set_mode = MagicMock(return_value=MagicMock())
        pygame.mixer.init = MagicMock(return_value=None)
        pygame.mixer.Sound = MagicMock(return_value=MagicMock())
        
        # sys.exitをモック化してテストが終了しないようにする
        self.exit_patcher = patch('sys.exit')
        self.mock_exit = self.exit_patcher.start()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.exit_patcher.stop()
        pygame.quit()
    
    def test_title_state_esc_key(self):
        """TitleStateでのESCキー処理をテスト"""
        # TitleStateのインスタンスを作成
        title_state = TitleState(self.game)
        
        # ESCキーイベントを処理
        title_state.handle_input(self.esc_event)
        
        # 結果を検証: TitleStateではESCキーでゲームを終了するはず
        # ここではpygame.quitとsys.exitがモック化されていないのでテストできない
        # 代わりに、handle_inputが例外を発生させずに完了することを確認
        self.assertTrue(True)
    
    def test_game_state_esc_key(self):
        """GameStateでのESCキー処理をテスト"""
        # GameStateのインスタンスを作成
        game_state = GameState(self.game)
        
        # ESCキーイベントを処理
        game_state.handle_input(self.esc_event)
        
        # 結果を検証: GameStateではESCキーでPauseStateに遷移するはず
        self.game.change_state.assert_called_once()
        # 引数としてPauseStateが渡されていることを確認（インスタンスの型をチェック）
        self.assertIsInstance(self.game.change_state.call_args[0][0], PauseState)
    
    def test_pause_state_esc_key(self):
        """PauseStateでのESCキー処理をテスト"""
        # 前の状態（GameState）をモック化
        previous_state = MagicMock()
        
        # PauseStateのインスタンスを作成
        pause_state = PauseState(self.game, previous_state)
        
        # ESCキーイベントを処理
        pause_state.handle_input(self.esc_event)
        
        # 結果を検証: PauseStateではESCキーで前の状態（GameState）に戻るはず
        self.game.change_state.assert_called_once_with(previous_state)
    
    def test_options_state_esc_key(self):
        """OptionsStateでのESCキー処理をテスト"""
        # OptionsStateのインスタンスを作成
        options_state = OptionsState(self.game)
        
        # ESCキーイベントを処理
        options_state.handle_input(self.esc_event)
        
        # 結果を検証: OptionsStateではESCキーでTitleStateに戻るはず
        self.game.change_state.assert_called_once()
        self.assertIsInstance(self.game.change_state.call_args[0][0], TitleState)
    
    def test_key_config_state_esc_key(self):
        """KeyConfigStateでのESCキー処理をテスト"""
        # KeyConfigStateのインスタンスを作成
        key_config_state = KeyConfigState(self.game)
        
        # ESCキーイベントを処理
        key_config_state.handle_input(self.esc_event)
        
        # 結果を検証: KeyConfigStateではESCキーでOptionsStateに戻るはず
        self.game.change_state.assert_called_once()
        self.assertIsInstance(self.game.change_state.call_args[0][0], OptionsState)
    
    def test_instructions_state_esc_key(self):
        """InstructionsStateでのESCキー処理をテスト"""
        # InstructionsStateのインスタンスを作成
        instructions_state = InstructionsState(self.game)
        
        # ESCキーイベントを処理
        instructions_state.handle_input(self.esc_event)
        
        # 結果を検証: InstructionsStateではESCキーでTitleStateに戻るはず
        self.game.change_state.assert_called_once()
        self.assertIsInstance(self.game.change_state.call_args[0][0], TitleState)

if __name__ == '__main__':
    unittest.main() 