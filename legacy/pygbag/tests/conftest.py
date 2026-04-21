import pytest
import pygame
import sys
import os
from unittest.mock import MagicMock

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game import Game
from game.arena import Arena
from game.player import Player


@pytest.fixture(scope="session", autouse=True)
def setup_pygame():
    """すべてのテストの前にpygameを初期化"""
    pygame.init()
    pygame.font.init()
    # テスト中は実際の画面を表示しない
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    yield
    pygame.quit()


@pytest.fixture
def mock_screen():
    """モックスクリーンを提供"""
    return pygame.Surface((800, 600))


@pytest.fixture
def game_instance(mock_screen):
    """ゲームインスタンスを提供"""
    game = Game(mock_screen)
    # テスト用に音声を無効化
    game.sounds = {}
    return game


@pytest.fixture
def arena_instance():
    """アリーナインスタンスを提供"""
    return Arena()


@pytest.fixture
def player_instances(game_instance):
    """プレイヤーインスタンスを提供"""
    return {
        'player1': game_instance.player1,
        'player2': game_instance.player2
    }


@pytest.fixture
def key_press_simulation():
    """キー入力シミュレーション用のヘルパー関数"""
    def _simulate_key_press(key_code):
        return pygame.event.Event(pygame.KEYDOWN, {"key": key_code})
    return _simulate_key_press


@pytest.fixture
def key_release_simulation():
    """キーリリースシミュレーション用のヘルパー関数"""
    def _simulate_key_release(key_code):
        return pygame.event.Event(pygame.KEYUP, {"key": key_code})
    return _simulate_key_release 