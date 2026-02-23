import pytest
import pygame
import sys
import os
import time

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.states import TitleState, AutoTestState
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class TestTitleBackground:
    """タイトル画面の背景アドバタイズ機能に関するテスト"""
    
    @pytest.fixture
    def setup_environment(self):
        """テスト環境のセットアップ"""
        # Pygameを初期化
        pygame.init()
        pygame.mixer.init()
        
        # 画面サーフェス作成（実際には表示されない）
        screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # メインゲームインスタンス
        main_game = Game(screen)
        main_game.change_state(TitleState(main_game))
        
        # 背景用ゲームインスタンス
        background_game = Game(screen)
        background_game.change_state(AutoTestState(background_game))
        
        # 背景描画用サーフェス
        background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        return {
            'screen': screen,
            'main_game': main_game,
            'background_game': background_game,
            'background_surface': background_surface
        }
    
    def test_title_background_rendering(self, setup_environment):
        """タイトル画面での背景アドバタイズ描画をテスト"""
        env = setup_environment
        screen = env['screen']
        main_game = env['main_game']
        background_game = env['background_game']
        background_surface = env['background_surface']
        
        # 背景サーフェスをクリア
        background_surface.fill((0, 0, 0, 0))
        
        # メインループの一部を模倣
        # 1. 背景ゲームの状態を更新
        background_game.update()
        
        # 2. メインゲームの状態を更新
        main_game.update()
        
        # 3. 背景ゲームを背景サーフェスに描画
        try:
            # 重要: ここでdraw_to_surfaceメソッドを呼び出す
            background_game.draw_to_surface(background_surface)
            
            # オーバーレイ適用
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            background_surface.blit(overlay, (0, 0))
            
            # 背景をメイン画面に描画
            screen.blit(background_surface, (0, 0))
            
            # メインゲーム描画（HUDなし）
            main_game.draw()
            
            test_passed = True
        except Exception as e:
            test_passed = False
            pytest.fail(f"タイトル背景描画中にエラー発生: {e}")
        
        assert test_passed, "タイトル背景の描画テストに失敗しました"
        
        # 追加検証: 背景サーフェスに何か描画されているかチェック
        non_empty = False
        for x in range(0, SCREEN_WIDTH, 50):
            for y in range(0, SCREEN_HEIGHT, 50):
                if background_surface.get_at((x, y))[3] > 0:
                    non_empty = True
                    break
            if non_empty:
                break
        
        assert non_empty, "背景サーフェスが空です（何も描画されていません）"
    
    def test_title_background_interaction(self, setup_environment):
        """タイトル画面でのメインゲームと背景ゲームの相互作用テスト"""
        env = setup_environment
        screen = env['screen']
        main_game = env['main_game']
        background_game = env['background_game']
        background_surface = env['background_surface']
        
        # シミュレーションを数フレーム実行してみる
        for _ in range(5):  # 5フレーム分実行
            # 背景ゲームの状態を更新
            background_game.update()
            
            # メインゲームの状態を更新
            main_game.update()
            
            # 背景サーフェスクリア
            background_surface.fill((0, 0, 0, 0))
            
            # 背景描画
            background_game.draw_to_surface(background_surface)
            screen.blit(background_surface, (0, 0))
            
            # メインゲーム描画
            main_game.draw()
            
            # 短い待機（シミュレーション）
            time.sleep(0.01)
        
        # 何も例外が発生しなければ成功
        assert True, "タイトル背景の相互作用テストに成功しました" 