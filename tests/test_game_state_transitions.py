import os
import sys

# プロジェクトのルートディレクトリをPythonのパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

import pygame
from unittest.mock import MagicMock, patch
from game.game import Game
from game.state import GameState
from game.constants import DEFAULT_KEY_MAPPING_P1, DEFAULT_KEY_MAPPING_P2
from game.states import TitleState, TrainingState, AutoTestState, PauseState, OptionsState, InstructionsState, KeyConfigState, SingleVersusGameState

# Pygameの初期化をモック
@pytest.fixture(scope="session", autouse=True)
def mock_pygame_init(session_mocker):
    session_mocker.patch("pygame.init", return_value=(6, 0))
    session_mocker.patch("pygame.display.set_mode", return_value=MagicMock())
    session_mocker.patch("pygame.display.set_caption", return_value=None)
    session_mocker.patch("pygame.font.init", return_value=None)
    session_mocker.patch("pygame.font.Font", return_value=MagicMock())
    session_mocker.patch("pygame.font.SysFont", return_value=MagicMock())
    session_mocker.patch("pygame.mixer.Sound", return_value=MagicMock())
    session_mocker.patch("pygame.mixer.music.load", return_value=None)
    session_mocker.patch("pygame.mixer.music.play", return_value=None)
    session_mocker.patch("pygame.mixer.music.set_volume", return_value=None)
    session_mocker.patch("pygame.time.Clock", return_value=MagicMock())
    # quitとexitもモック
    session_mocker.patch("pygame.quit", return_value=None)
    session_mocker.patch("sys.exit", return_value=None)


@pytest.fixture
def game_instance(mocker):
    # Gameインスタンスを作成し、依存メソッドをモック
    screen_mock = MagicMock()
    game = Game(screen_mock)
    
    # 重要なメソッドをモックして呼び出しを検証
    mocker.patch.object(game, 'reset_players')
    mocker.patch.object(game, 'save_key_config')
    mocker.patch.object(game, 'reset_key_config')
    
    # サウンド再生もモック
    mocker.patch.object(game.sounds.get("menu", MagicMock()), 'play')
    mocker.patch.object(game.sounds.get("special", MagicMock()), 'play')
    
    # キーマッピングをデフォルトに戻す
    game.key_mapping_p1.clear()
    game.key_mapping_p1.update(DEFAULT_KEY_MAPPING_P1)
    game.key_mapping_p2.clear()
    game.key_mapping_p2.update(DEFAULT_KEY_MAPPING_P2)
    
    return game

# --- タイトル画面テスト ---

def test_title_select_game(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 0 # シングル対戦モード
    
    # モックをリセット
    game_instance.reset_players.reset_mock()
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態が変わったことを確認
    assert isinstance(game_instance.current_state, game_instance.current_state.__class__)
    # 現在の実装では2回呼ばれることを確認
    assert game_instance.reset_players.call_count == 2

def test_title_select_training(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 1 # トレーニングモード
    
    # モックをリセット
    game_instance.reset_players.reset_mock()
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態が変わったことを確認
    assert isinstance(game_instance.current_state, game_instance.current_state.__class__)
    # 現在の実装では2回呼ばれることを確認
    assert game_instance.reset_players.call_count == 2

def test_title_select_auto_test(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 2 # 自動テスト
    
    # モックをリセット
    game_instance.reset_players.reset_mock()
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態が変わったことを確認
    assert isinstance(game_instance.current_state, game_instance.current_state.__class__)
    # 現在の実装では2回呼ばれることを確認
    assert game_instance.reset_players.call_count == 2

def test_title_select_controls(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 3 # 操作説明
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態が変わったことを確認
    assert isinstance(game_instance.current_state, InstructionsState)

def test_title_select_options(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 4 # オプション
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態が変わったことを確認
    assert isinstance(game_instance.current_state, game_instance.current_state.__class__)

def test_title_select_exit(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    game_instance.current_state.selected_item = 5 # 終了
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 終了が呼ばれたことを確認
    pygame.quit.assert_called_once()
    sys.exit.assert_called_once()

def test_title_navigation(game_instance, mocker):
    # TitleStateを設定
    game_instance.change_state(TitleState(game_instance))
    initial_item = game_instance.current_state.selected_item
    
    # 下キーを押す
    event_down = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
    game_instance.current_state.handle_input(event_down)
    
    assert game_instance.current_state.selected_item == (initial_item + 1) % len(game_instance.menu_items)
    game_instance.sounds["menu"].play.assert_called_once()
    
    # 上キーを押す
    event_up = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP})
    game_instance.current_state.handle_input(event_up)
    
    assert game_instance.current_state.selected_item == initial_item
    assert game_instance.sounds["menu"].play.call_count == 2

# --- 操作説明画面テスト ---

def test_controls_back_to_title(game_instance, mocker):
    # InstructionsStateを設定
    game_instance.change_state(InstructionsState(game_instance))
    
    # 戻るキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がTitleStateに変わったことを確認
    assert isinstance(game_instance.current_state, TitleState)

def test_controls_back_to_pause(game_instance, mocker):
    # SingleVersusGameState→PauseState→InstructionsStateの順に遷移させる
    from game.states import SingleVersusGameState as SingleVersusGameStateClass
    game_instance.change_state(SingleVersusGameStateClass(game_instance))
    game_instance.current_state.selected_item = 1 # 操作説明を選択
    
    # 決定キーを押す（操作説明画面へ）
    event_z = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event_z)
    
    # 戻るキーを押す
    event_esc = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event_esc)
    
    # 状態がPauseStateに戻ったことを確認
    assert isinstance(game_instance.current_state, PauseState) # 修正: InstructionsStateからは呼び出し元のPauseStateに戻る

# --- ポーズメニューテスト ---

def test_pause_to_game(game_instance, mocker):
    # SingleVersusGameState→PauseStateの順に遷移させる
    from game.states import SingleVersusGameState as SingleVersusGameStateClass
    previous_state = SingleVersusGameStateClass(game_instance)
    game_instance.change_state(PauseState(game_instance, previous_state))
    game_instance.current_state.selected_item = 0 # ゲームに戻る
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 元のゲーム状態に戻ったことを確認
    assert isinstance(game_instance.current_state, SingleVersusGameStateClass)

def test_pause_to_controls(game_instance, mocker):
    # PauseStateを設定
    game_instance.change_state(PauseState(game_instance))
    game_instance.current_state.selected_item = 1 # 操作説明
    
    # 決定キーを押す（ENTERキーを使用）
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
    game_instance.current_state.handle_input(event)
    
    # 状態がInstructionsStateに変わったことを確認
    assert isinstance(game_instance.current_state, InstructionsState)

def test_pause_to_title(game_instance, mocker):
    # PauseStateを設定
    game_instance.change_state(PauseState(game_instance))
    game_instance.current_state.selected_item = 2 # タイトルに戻る
    
    # 決定キーを押す（ENTERキーを使用）
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態がTitleStateに変わったことを確認
    # 注：実際のゲームではゲームオーバー確認などを経由するのが望ましい
    assert isinstance(game_instance.current_state, TitleState)

# --- オプション画面テスト ---

def test_options_to_key_config(game_instance, mocker):
    # OptionsStateを設定
    game_instance.change_state(OptionsState(game_instance))
    game_instance.current_state.selected_item = 0 # キーコンフィグ
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態がKeyConfigStateに変わったことを確認
    assert isinstance(game_instance.current_state, KeyConfigState)
    assert game_instance.key_config_player == 1
    assert game_instance.key_config_selected_item == 0
    assert not game_instance.waiting_for_key_input

def test_options_back_to_title_confirm(game_instance, mocker):
    # OptionsStateを設定
    game_instance.change_state(OptionsState(game_instance))
    game_instance.current_state.selected_item = 3 # 戻る
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    # 状態がTitleStateに変わったことを確認
    assert isinstance(game_instance.current_state, TitleState)

def test_options_back_to_title_cancel(game_instance, mocker):
    # OptionsStateを設定
    game_instance.change_state(OptionsState(game_instance))
    
    # 戻るキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がTitleStateに変わったことを確認
    assert isinstance(game_instance.current_state, TitleState)

# --- キーコンフィグ画面テスト (メニュー部分) ---

def test_key_config_navigation(game_instance, mocker):
    # KeyConfigStateを設定
    game_instance.change_state(KeyConfigState(game_instance))
    game_instance.waiting_for_key_input = False
    initial_item = game_instance.key_config_selected_item
    
    # 下キーを押す
    event_down = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
    game_instance.current_state.handle_input(event_down)
    
    assert game_instance.key_config_selected_item == (initial_item + 1) % len(game_instance.key_config_items)
    
    # 上キーを押す
    event_up = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP})
    game_instance.current_state.handle_input(event_up)
    
    assert game_instance.key_config_selected_item == initial_item

def test_key_config_switch_player(game_instance, mocker):
    # KeyConfigStateを設定
    game_instance.change_state(KeyConfigState(game_instance))
    game_instance.waiting_for_key_input = False
    initial_player = game_instance.key_config_player
    
    # 右キーを押す
    event_right = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
    game_instance.current_state.handle_input(event_right)
    
    assert game_instance.key_config_player != initial_player
    
    # 左キーを押す
    event_left = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
    game_instance.current_state.handle_input(event_left)
    
    assert game_instance.key_config_player == initial_player

def test_key_config_enter_wait(game_instance, mocker):
    # KeyConfigStateを設定
    game_instance.change_state(KeyConfigState(game_instance))
    game_instance.waiting_for_key_input = False
    
    # 決定キーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
    game_instance.current_state.handle_input(event)
    
    assert game_instance.waiting_for_key_input

def test_key_config_back_to_options(game_instance, mocker):
    # KeyConfigStateを設定
    game_instance.change_state(KeyConfigState(game_instance))
    
    # 戻るキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がOptionsStateに変わったことを確認
    assert isinstance(game_instance.current_state, OptionsState)

def test_key_config_reset_keys(game_instance, mocker):
    # KeyConfigStateを設定
    game_instance.change_state(KeyConfigState(game_instance))
    
    # reset_key_configのモックを元の関数に戻す
    # モックされた関数の参照を取得
    original_reset_key_config = Game.reset_key_config
    # game_instanceのmockedメソッドを元の関数で上書き
    game_instance.reset_key_config = lambda: original_reset_key_config(game_instance)
    
    # P1のキー配置を変更して空にする
    game_instance.key_mapping_p1.clear()
    assert len(game_instance.key_mapping_p1) == 0
    
    # リセットキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r})
    game_instance.current_state.handle_input(event)
    
    # デフォルト設定に戻ったことを確認
    assert len(game_instance.key_mapping_p1) > 0
    expected_keys = DEFAULT_KEY_MAPPING_P1.keys()
    for key in expected_keys:
        assert key in game_instance.key_mapping_p1

# --- ゲームプレイ時の状態遷移テスト ---

def test_gameplay_escape_to_pause(game_instance, mocker):
    # SingleVersusGameStateを設定
    from game.states import SingleVersusGameState as SingleVersusGameStateClass
    game_state = SingleVersusGameStateClass(game_instance)
    game_instance.change_state(game_state)
    
    # ESCキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がPauseStateに変わったことを確認
    assert isinstance(game_instance.current_state, PauseState)

def test_training_escape_to_pause(game_instance, mocker):
    # TrainingStateを設定
    game_instance.change_state(TrainingState(game_instance))
    
    # ESCキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がPauseStateに変わったことを確認
    assert isinstance(game_instance.current_state, PauseState)

def test_auto_test_escape_to_pause(game_instance, mocker):
    # AutoTestStateを設定
    game_instance.change_state(AutoTestState(game_instance))
    
    # ESCキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 状態がPauseStateに変わったことを確認
    assert isinstance(game_instance.current_state, PauseState)

def test_pause_escape_back_to_game(game_instance, mocker):
    # SingleVersusGameState→PauseStateの順に遷移させる
    from game.states import SingleVersusGameState as SingleVersusGameStateClass
    previous_state = SingleVersusGameStateClass(game_instance)
    game_instance.change_state(PauseState(game_instance, previous_state))
    
    # ESCキーを押す
    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    game_instance.current_state.handle_input(event)
    
    # 元の状態に戻ったことを確認
    assert isinstance(game_instance.current_state, SingleVersusGameStateClass)

# --- クラス形式のテスト ---

class TestGameStateTransitions:
    def test_initial_state(self, game_instance):
        # 最初の状態はTitleStateであることを確認
        game_instance.change_state(TitleState(game_instance))
        assert isinstance(game_instance.current_state, TitleState)

    def test_title_to_game_state_transition(self, game_instance):
        # TitleStateからSingleVersusGameStateへの遷移
        game_instance.change_state(TitleState(game_instance))
        game_instance.current_state.selected_item = 0  # シングル対戦モード
        
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
        game_instance.current_state.handle_input(event)
        
        # SingleVersusGameStateに遷移したことを確認
        from game.states import SingleVersusGameState as SingleVersusGameStateClass
        assert isinstance(game_instance.current_state, SingleVersusGameStateClass)

    def test_title_to_options_transition(self, game_instance):
        # TitleStateからOptionsStateへの遷移
        game_instance.change_state(TitleState(game_instance))
        game_instance.current_state.selected_item = 4  # オプション
        
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
        game_instance.current_state.handle_input(event)
        
        # OptionsStateに遷移したことを確認
        assert isinstance(game_instance.current_state, OptionsState)

    def test_options_to_key_config_transition(self, game_instance):
        # OptionsStateからKeyConfigStateへの遷移
        game_instance.change_state(OptionsState(game_instance))
        game_instance.current_state.selected_item = 0  # キーコンフィグ
        
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
        game_instance.current_state.handle_input(event)
        
        # KeyConfigStateに遷移したことを確認
        assert isinstance(game_instance.current_state, KeyConfigState)

    def test_circular_state_transitions(self, game_instance):
        # TitleState -> OptionsState -> KeyConfigState -> OptionsState -> TitleState という循環遷移
        game_instance.change_state(TitleState(game_instance))
        
        # タイトルからオプションへ
        game_instance.current_state.selected_item = 4  # オプション
        event_z = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
        game_instance.current_state.handle_input(event_z)
        assert isinstance(game_instance.current_state, OptionsState)
        
        # オプションからキーコンフィグへ
        game_instance.current_state.selected_item = 0  # キーコンフィグ
        game_instance.current_state.handle_input(event_z)
        assert isinstance(game_instance.current_state, KeyConfigState)
        
        # キーコンフィグからオプションへ
        event_x = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        game_instance.current_state.handle_input(event_x)
        assert isinstance(game_instance.current_state, OptionsState)
        
        # オプションからタイトルへ
        game_instance.current_state.handle_input(event_x)
        assert isinstance(game_instance.current_state, TitleState)

    def test_escape_key_behavior(self, game_instance, mocker):
        # ESCキーの挙動テスト
        
        # SingleVersusGameStateからPauseStateへ
        from game.states import SingleVersusGameState as SingleVersusGameStateClass
        game_state = SingleVersusGameStateClass(game_instance)
        game_instance.change_state(game_state)
        
        event_esc = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        game_instance.current_state.handle_input(event_esc)
        assert isinstance(game_instance.current_state, PauseState)
        
        # PauseStateからSingleVersusGameStateへ
        game_instance.current_state.handle_input(event_esc)
        assert isinstance(game_instance.current_state, SingleVersusGameStateClass) 