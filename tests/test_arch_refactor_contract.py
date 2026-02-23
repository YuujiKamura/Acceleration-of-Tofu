import pygame
from unittest.mock import MagicMock

from game.game import Game
from game.projectile import Projectile
from game.states import AutoTestState, SingleVersusGameState, TitleState


def test_state_update_contracts():
    pygame.init()
    screen = pygame.Surface((1280, 720))
    game = Game(screen)

    assert game.current_state.needs_game_update() is False

    versus = SingleVersusGameState(game)
    auto_test = AutoTestState(game)

    assert versus.needs_game_update() is True
    assert auto_test.needs_game_update() is True


def test_game_update_delegates_to_current_state_update():
    pygame.init()
    screen = pygame.Surface((1280, 720))
    game = Game(screen)

    state = TitleState(game)
    game.change_state(state)
    state.update = MagicMock(wraps=state.update)

    game.update()

    assert state.update.call_count == 1


def test_projectile_has_is_expired_alias():
    pygame.init()
    screen = pygame.Surface((1280, 720))
    game = Game(screen)
    owner = game.player1

    projectile = Projectile(owner.x, owner.y, 0.0, 1, owner)

    assert projectile.is_expired is False
    projectile.is_dead = True
    assert projectile.is_expired is True
