#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from pygame.event import Event
from game.game import Game
from game.player import Player
from game.states import TitleState, SingleVersusGameState, PauseState
from game.constants import (
    PLAYER_SPEED, ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS, 
    MAX_HEAT, MAX_HYPER, SCREEN_WIDTH, SCREEN_HEIGHT
)

class TestVersusMode(unittest.TestCase):
    """Integration test for versus mode"""

    @classmethod
    def setUpClass(cls):
        """Class setup: Initialize Pygame"""
        pygame.init()
        pygame.font.init()
        # Mock necessary Pygame modules to avoid display/sound errors
        cls.mock_screen = MagicMock(spec=pygame.Surface)
        pygame.display.set_mode = MagicMock(return_value=cls.mock_screen)
        pygame.mixer.init = MagicMock()
        pygame.mixer.Sound = MagicMock(return_value=MagicMock(play=MagicMock()))
        pygame.quit = MagicMock()

    @classmethod
    def tearDownClass(cls):
        """Class teardown: Quit Pygame"""
        pygame.quit()

    def setUp(self):
        """Setup before each test: Create game instance"""
        # Mock sys.exit to prevent test runner exit
        self.exit_patcher = patch('sys.exit')
        self.mock_exit = self.exit_patcher.start()
        
        # Create a fresh game instance for each test
        self.game = Game(screen=self.mock_screen)
        self.game.current_state = TitleState(self.game)

    def tearDown(self):
        """Cleanup after each test"""
        self.exit_patcher.stop()

    def test_versus_mode_initialization(self):
        """Test initialization state for versus mode"""
        title_state = self.game.current_state
        title_state.selected_item = title_state.menu_items.index("シングル対戦モード")
        enter_event = Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        title_state.handle_input(enter_event)

        self.assertIsInstance(self.game.current_state, SingleVersusGameState)
        self.assertNotEqual(self.game.player1.x, 0)
        self.assertNotEqual(self.game.player2.x, 0)

    def test_player1_movement_response(self):
        """Test player 1 response to movement input in versus mode"""
        self.game.change_state(SingleVersusGameState(self.game))
        # Disable AI to prevent it from overwriting key states
        with patch.object(SingleVersusGameState, 'uses_simple_ai_opponent', return_value=False):
            initial_x = self.game.player1.x
            
            # Right arrow key
            self.game.handle_keydown(pygame.K_RIGHT)
            self.assertEqual(self.game.key_mapping_p1.get(pygame.K_RIGHT), "right")
            self.game.update()
            self.assertGreater(self.game.player1.x, initial_x)

            # Right arrow key release
            current_x = self.game.player1.x
            self.game.handle_keyup(pygame.K_RIGHT)
            self.game.update()
            self.assertEqual(self.game.player1.x, current_x)

            # WASD (P2 default)
            initial_x_p2 = self.game.player2.x
            event_d_down = Event(pygame.KEYDOWN, {"key": pygame.K_d})
            self.game.player2.handle_key_event(event_d_down)
            self.assertEqual(self.game.key_mapping_p2.get(pygame.K_d), "right")
            self.game.update()
            self.assertGreater(self.game.player2.x, initial_x_p2)

    def test_player1_weapon_a_action(self):
        """Test player 1 weapon A action"""
        self.game.change_state(SingleVersusGameState(self.game))
        initial_count = len(self.game.projectiles)
        
        # Z key
        self.game.handle_keydown(pygame.K_z)
        self.game.update()
        self.assertGreater(len(self.game.projectiles), initial_count)
        
        # Alternative key test - reuse P1 but manually set another key to weapon_a
        self.game.projectiles = []
        self.game.player1.shoot_cooldown = 0
        self.game.key_mapping_p1[pygame.K_j] = "weapon_a"
        self.game.handle_keydown(pygame.K_j)
        self.game.update()
        self.assertGreater(len(self.game.projectiles), 0)

    def test_player1_shield_action(self):
        """Test player 1 shield action"""
        self.game.change_state(SingleVersusGameState(self.game))
        # Disable AI
        with patch.object(SingleVersusGameState, 'uses_simple_ai_opponent', return_value=False):
            self.assertFalse(self.game.player1.is_shielding())
            
            # V key + enough hyper gauge
            self.game.player1.hyper_gauge = 100
            self.game.handle_keydown(pygame.K_v)
            self.game.update()
            self.assertTrue(self.game.player1.is_shielding())

    def test_player1_dash_action(self):
        """Test player 1 dash action"""
        self.game.change_state(SingleVersusGameState(self.game))
        initial_x = self.game.player1.x
        
        self.game.handle_keydown(pygame.K_RIGHT)
        self.game.handle_keydown(pygame.K_LSHIFT)
        for _ in range(5):
            self.game.update()
        
        self.assertGreater(self.game.player1.x - initial_x, PLAYER_SPEED * 5)

    def test_player1_hyper_mode(self):
        """Test player 1 hyper mode"""
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.player1.hyper_gauge = 100
        self.game.handle_keydown(pygame.K_SPACE)
        self.game.update()
        self.assertTrue(self.game.player1.is_hyper)

    def test_hud_display(self):
        """Test HUD drawing"""
        self.game.change_state(SingleVersusGameState(self.game))
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        try:
            self.game.current_state.draw(surface)
            passed = True
        except Exception:
            passed = False
        self.assertTrue(passed)

    def test_player_collision_detection(self):
        """Test player-to-player collision"""
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.player1.x = self.game.player2.x
        self.game.player1.y = self.game.player2.y
        self.game.update()
        
        distance = self.calculate_distance(self.game.player1, self.game.player2)
        self.assertGreaterEqual(distance, self.game.player1.radius)

    def test_projectile_player_collision(self):
        """Test projectile-to-player collision"""
        self.game.change_state(SingleVersusGameState(self.game))
        from game.projectile import Projectile
        projectile = Projectile(self.game.player2.x, self.game.player2.y, 0, 10, self.game.player1)
        self.game.projectiles.append(projectile)
        initial_health = self.game.player2.health
        self.game.handle_collisions()
        self.assertLess(self.game.player2.health, initial_health)

    def test_player2_ai_behavior(self):
        """Test player 2 AI"""
        self.game.change_state(SingleVersusGameState(self.game))
        initial_x = self.game.player2.x
        for _ in range(60): # 1 second
            self.game.update()
        self.assertNotEqual(self.game.player2.x, initial_x)

    def test_game_state_pause_transition(self):
        """Test pause transition"""
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.handle_keydown(pygame.K_ESCAPE)
        self.assertIsInstance(self.game.current_state, PauseState)

    def calculate_distance(self, obj1, obj2):
        import math
        return math.sqrt((obj1.x - obj2.x)**2 + (obj1.y - obj2.y)**2)

    def test_key_mappings_multiple_keys(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_UP), "up")
        self.assertEqual(self.game.key_mapping_p2.get(pygame.K_w), "up")

    def test_key_input_registration(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.handle_keydown(pygame.K_RIGHT)
        self.assertTrue(self.game.keys_pressed.get("right"))

    def test_multiple_keys_pressed(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.handle_keydown(pygame.K_RIGHT)
        self.game.handle_keydown(pygame.K_DOWN)
        self.assertTrue(self.game.keys_pressed.get("right"))
        self.assertTrue(self.game.keys_pressed.get("down"))

    def test_input_buffer_persistence(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.handle_keydown(pygame.K_RIGHT)
        self.game.update()
        self.assertTrue(self.game.keys_pressed.get("right"))

    def test_player_update_with_key_states(self):
        self.game.change_state(SingleVersusGameState(self.game))
        with patch.object(Player, 'update', wraps=self.game.player1.update) as mock_update:
            self.game.update()
            self.assertGreaterEqual(mock_update.call_count, 1)

    def test_heat_gauge_management(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.handle_keydown(pygame.K_z)
        self.game.update()
        self.assertGreater(self.game.player1.heat, 0)

    def test_overheat_condition(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.player1.heat = MAX_HEAT - 1
        self.game.handle_keydown(pygame.K_z)
        self.game.player1.shoot_cooldown = 0
        # Need two updates: one to fire and increase heat, another to detect overheat
        self.game.update()
        self.game.player1.shoot_cooldown = 0 # Ensure it can fire/be checked
        self.game.update()
        self.assertTrue(self.game.player1.is_overheated)

    def test_arena_boundary_heat_effect(self):
        self.game.change_state(SingleVersusGameState(self.game))
        self.game.player1.x = ARENA_CENTER_X + ARENA_RADIUS * 0.9
        self.game.handle_keydown(pygame.K_z)
        self.game.update()
        self.assertGreater(self.game.player1.heat, 0)

if __name__ == '__main__':
    unittest.main()
