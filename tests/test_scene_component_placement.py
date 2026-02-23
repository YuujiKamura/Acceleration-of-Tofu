import pytest
import pygame
import sys
import os
from unittest.mock import MagicMock

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.states import TitleState, SingleVersusGameState, TrainingState, AutoTestState, PauseState, OptionsState, InstructionsState, KeyConfigState
from game.constants import ARENA_CENTER_X, ARENA_CENTER_Y, MAX_HEALTH, MAX_HEAT, MAX_HYPER, SCREEN_WIDTH, SCREEN_HEIGHT


class TestSceneComponentPlacement:
    """各シーンの初期化時にコンポーネントが正しく配置されているかテスト"""
    
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
    
    def test_title_state_component_placement(self, setup_game):
        """タイトル画面の初期化と配置テスト"""
        game = setup_game
        
        # TitleStateを明示的に作成して設定
        title_state = TitleState(game)
        game.change_state(title_state)
        
        # メニュー項目の選択位置は0から始まるか
        assert title_state.selected_item == 0
        
        # メニュー項目が正しく設定されているか
        assert len(title_state.menu_items) > 0
        assert "シングル対戦モード" in title_state.menu_items
        assert "トレーニングモード" in title_state.menu_items
        assert "自動テスト" in title_state.menu_items
        assert "操作説明" in title_state.menu_items
        assert "オプション" in title_state.menu_items
        assert "終了" in title_state.menu_items
        
        # 選択項目を変更できるか
        title_state.selected_item = 2
        assert title_state.selected_item == 2
        
        # アドバタイズモードのテスト
        # 背景ゲームを作成
        background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        background_game = Game(game.screen)
        background_game.change_state(AutoTestState(background_game))
        
        # draw_to_surfaceメソッドが例外を発生させずに動作するか
        try:
            background_game.draw_to_surface(background_surface)
            test_passed = True
        except Exception as e:
            test_passed = False
            pytest.fail(f"draw_to_surfaceメソッドが例外を発生させました: {e}")
        
        assert test_passed, "アドバタイズモードの描画処理が失敗しました"
        
        # バッファが空でないことを確認
        buffer_empty = True
        for x in range(0, SCREEN_WIDTH, 50):  # 50ピクセルごとにサンプリング
            for y in range(0, SCREEN_HEIGHT, 50):
                if background_surface.get_at((x, y))[3] > 0:  # アルファ値が0より大きい
                    buffer_empty = False
                    break
            if not buffer_empty:
                break
        
        assert not buffer_empty, "アドバタイズモードの背景が描画されていません"
        
        # プレイヤー間距離によるズーム処理のテスト
        # プレイヤーを近づける
        background_game.player1.x = ARENA_CENTER_X - 50
        background_game.player2.x = ARENA_CENTER_X + 50
        background_game.draw_to_surface(background_surface)
        
        # プレイヤーを離す
        background_game.player1.x = ARENA_CENTER_X - 200
        background_game.player2.x = ARENA_CENTER_X + 200
        background_game.draw_to_surface(background_surface)
        
        # 両方のケースで例外なく描画できることを確認
        assert True, "ズーム処理が正常に動作しました"
    
    def test_single_versus_game_state_component_placement(self, setup_game):
        """ゲームプレイ画面の初期化と配置テスト"""
        game = setup_game
        
        # SingleVersusGameStateを明示的に作成して設定
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # プレイヤーが正しい初期位置に配置されているか
        assert game.player1.x == ARENA_CENTER_X - 100
        assert game.player1.y == ARENA_CENTER_Y
        assert game.player2.x == ARENA_CENTER_X + 100
        assert game.player2.y == ARENA_CENTER_Y
        
        # プレイヤーの初期状態が正しいか
        assert game.player1.health == MAX_HEALTH
        assert game.player1.heat == 0
        assert game.player1.hyper_gauge == MAX_HYPER / 2  # 初期値は半分から始まる
        assert not game.player1.is_dashing
        assert not game.player1.is_shield_active
        assert not game.player1.is_hyper_active
        
        assert game.player2.health == MAX_HEALTH
        assert game.player2.heat == 0
        assert game.player2.hyper_gauge == MAX_HYPER / 2  # 初期値は半分から始まる
        assert not game.player2.is_dashing
        assert not game.player2.is_shield_active
        assert not game.player2.is_hyper_active
        
        # 弾とエフェクトのリストが空か
        assert len(game.projectiles) == 0
        assert len(game.effects) == 0
    
    def test_training_state_component_placement(self, setup_game):
        """トレーニングモードの初期化と配置テスト"""
        game = setup_game
        
        # TrainingStateを明示的に作成して設定
        training_state = TrainingState(game)
        game.change_state(training_state)
        
        # プレイヤーが正しい初期位置に配置されているか
        assert game.player1.x == ARENA_CENTER_X - 100
        assert game.player1.y == ARENA_CENTER_Y
        assert game.player2.x == ARENA_CENTER_X + 100
        assert game.player2.y == ARENA_CENTER_Y
        
        # プレイヤーの初期状態が正しいか (SingleVersusGameStateと同様)
        assert game.player1.health == MAX_HEALTH
        assert game.player2.health == MAX_HEALTH
        
        # 弾とエフェクトのリストが空か
        assert len(game.projectiles) == 0
        assert len(game.effects) == 0
    
    def test_pause_state_component_placement(self, setup_game):
        """ポーズ画面の初期化と配置テスト"""
        game = setup_game
        
        # まずSingleVersusGameStateに遷移してからPauseStateに遷移
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # PauseStateを明示的に作成して設定
        pause_state = PauseState(game)
        game.change_state(pause_state, game_state)
        
        # メニュー項目の選択位置は0から始まるか
        assert pause_state.selected_item == 0
        
        # メニュー項目が正しく設定されているか
        assert len(pause_state.menu_items) > 0
        assert "ゲームに戻る" in pause_state.menu_items
        assert "操作説明" in pause_state.menu_items
        assert "タイトルに戻る" in pause_state.menu_items
        assert "ゲーム終了" in pause_state.menu_items
        
        # 前の状態への参照が保持されているか
        assert game.previous_state == game_state
        
        # 選択項目を変更できるか
        pause_state.selected_item = 1
        assert pause_state.selected_item == 1
    
    def test_options_state_component_placement(self, setup_game):
        """オプション画面の初期化と配置テスト"""
        game = setup_game
        
        # OptionsStateを明示的に作成して設定
        options_state = OptionsState(game)
        game.change_state(options_state)
        
        # メニュー項目の選択位置は0から始まるか
        assert options_state.selected_item == 0
        
        # メニュー項目が正しく設定されているか
        assert len(options_state.menu_items) > 0
        assert "プレイヤー1設定" in options_state.menu_items
        assert "プレイヤー2設定" in options_state.menu_items
        assert "サウンド設定" in options_state.menu_items
        assert "戻る" in options_state.menu_items
        
        # 選択項目を変更できるか
        options_state.selected_item = 2
        assert options_state.selected_item == 2
    
    def test_instructions_state_component_placement(self, setup_game):
        """操作説明画面の初期化と配置テスト"""
        game = setup_game
        
        # InstructionsStateを明示的に作成して設定
        instructions_state = InstructionsState(game)
        game.change_state(instructions_state)
        
        # 操作説明画面が正しく初期化されているか
        assert hasattr(instructions_state, 'game')
        assert instructions_state.game == game
    
    def test_key_config_state_component_placement(self, setup_game):
        """キーコンフィグ画面の初期化と配置テスト"""
        game = setup_game
        
        # KeyConfigStateを明示的に作成して設定
        key_config_state = KeyConfigState(game)
        game.change_state(key_config_state)
        
        # 基本状態の確認
        assert key_config_state.player in [1, 2]  # プレイヤー番号は1か2
        assert key_config_state.selected_item == 0  # 最初の選択項目
        assert key_config_state.waiting_for_input == False  # キー入力待ちではない
        
        # 設定項目が存在するか
        assert len(key_config_state.config_items) > 0
        
        # 選択項目を変更できるか
        key_config_state.selected_item = 1
        assert key_config_state.selected_item == 1
    
    def test_auto_test_state_component_placement(self, setup_game):
        """自動テスト画面の初期化と配置テスト"""
        game = setup_game
        
        # AutoTestStateを明示的に作成して設定
        auto_test_state = AutoTestState(game)
        game.change_state(auto_test_state)
        
        # プレイヤーが正しい初期位置に配置されているか
        assert game.player1.x == ARENA_CENTER_X - 100
        assert game.player1.y == ARENA_CENTER_Y
        assert game.player2.x == ARENA_CENTER_X + 100
        assert game.player2.y == ARENA_CENTER_Y
        
        # プレイヤーの初期状態が正しいか
        assert game.player1.health == MAX_HEALTH
        assert game.player2.health == MAX_HEALTH
        
        # テスト用タイマーが初期化されているか
        assert game.test_timer == 0
        
        # 弾とエフェクトのリストが空か
        assert len(game.projectiles) == 0
        assert len(game.effects) == 0
    
    def test_state_transition_preserves_components(self, setup_game):
        """状態遷移時にコンポーネントが適切に保持されるかのテスト"""
        game = setup_game
        
        # まずPauseStateに遷移
        pause_state = PauseState(game)
        game.change_state(pause_state)
        
        # プレイヤーの位置を少し移動させる
        initial_p1_x = game.player1.x
        initial_p1_y = game.player1.y
        game.player1.x += 50
        game.player1.y += 30
        
        # ダミーの弾とエフェクトを追加
        mock_projectile = MagicMock()
        mock_projectile.is_dead = False
        mock_effect = MagicMock()
        mock_effect.is_dead = False
        
        game.projectiles.append(mock_projectile)
        game.effects.append(mock_effect)
        
        # 一時的に別の状態に遷移
        title_state = TitleState(game)
        game.change_state(title_state, pause_state)
        
        # 元のPauseStateに戻る
        game.change_state(pause_state)
        
        # プレイヤーの位置が保持されているか
        assert game.player1.x == initial_p1_x + 50
        assert game.player1.y == initial_p1_y + 30
        
        # 弾とエフェクトが保持されているか
        assert len(game.projectiles) == 1
        assert len(game.effects) == 1
    
    def test_reset_players_on_game_start(self, setup_game):
        """ゲーム開始時にプレイヤーが正しくリセットされるかのテスト"""
        game = setup_game
        
        # プレイヤーの状態を変更
        game.player1.health = 50
        game.player1.heat = 75
        game.player1.hyper_gauge = 50
        
        # SingleVersusGameStateに遷移（プレイヤーのリセットが行われる）
        game_state = SingleVersusGameState(game)
        game.change_state(game_state)
        
        # プレイヤーの状態がリセットされているか
        assert game.player1.health == MAX_HEALTH
        assert game.player1.heat == 0
        assert game.player1.hyper_gauge == MAX_HYPER / 2  # リセット後は半分から始まる
        
        # 弾とエフェクトのリストが空か
        assert len(game.projectiles) == 0
        assert len(game.effects) == 0 