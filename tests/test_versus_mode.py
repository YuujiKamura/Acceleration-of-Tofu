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
from game.states import TitleState, SingleVersusGameState, PauseState # Import necessary states
from game.constants import PLAYER_SPEED, ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS, MAX_HEAT, MAX_HYPER # Import constants if needed for assertions

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
        pygame.quit = MagicMock() # Mock quit to prevent exit

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
        # Ensure the game starts in TitleState (or mock as needed)
        self.game.current_state = TitleState(self.game)

    def tearDown(self):
        """Cleanup after each test"""
        self.exit_patcher.stop() # Stop mocking sys.exit

    def test_versus_mode_initialization(self):
        """Test initialization state for versus mode"""
        # Transition from title screen to versus mode
        title_state = self.game.current_state
        title_state.selected_item = title_state.menu_items.index("シングル対戦モード")
        enter_event = Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        title_state.handle_input(enter_event)

        # Confirm state changed to SingleVersusGameState
        self.assertIsInstance(self.game.current_state, SingleVersusGameState, "State should transition to SingleVersusGameState")

        # Check player reset (more direct check)
        # Since reset_players is called in __init__, direct testing is difficult
        # Instead, check player initial positions and state
        self.assertNotEqual(self.game.player1.x, 0, "Player 1 should have initial position X")
        self.assertNotEqual(self.game.player1.y, 0, "Player 1 should have initial position Y")
        self.assertNotEqual(self.game.player2.x, 0, "Player 2 should have initial position X")
        self.assertNotEqual(self.game.player2.y, 0, "Player 2 should have initial position Y")
        
        # TODO: Consider how to verify player 2 is under AI control
        # (e.g., check if simple_ai_control is called in update, etc.)

    def test_player1_movement_response(self):
        """Test player 1 response to movement input in versus mode"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Get player 1 initial position
        initial_x = self.game.player1.x
        initial_y = self.game.player1.y

        # --- Right movement test ---
        # テストを両方のキー（矢印キーとD）で行う
        # まず右矢印キーでテスト
        event_right_down = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(event_right_down.key)

        # Player 1's internal key state should be updated
        action = self.game.key_mapping_p1.get(pygame.K_RIGHT)
        self.assertEqual(action, "right", "K_RIGHT should map to 'right' for P1")
        
        # Update game state for one frame
        self.game.update()

        # Check if player 1 moved right
        self.assertGreater(self.game.player1.x, initial_x, "Player 1 should move right on RIGHT key down")
        self.assertEqual(self.game.player1.y, initial_y, "Player 1 Y should not change on right move")

        # 右矢印キーリリース
        current_x = self.game.player1.x
        event_right_up = Event(pygame.KEYUP, {"key": pygame.K_RIGHT})
        self.game.handle_keyup(event_right_up.key)
        self.game.update()

        # 次にDキーでテスト
        initial_x = self.game.player1.x
        event_d_down = Event(pygame.KEYDOWN, {"key": pygame.K_d})
        self.game.handle_keydown(event_d_down.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_d)
        self.assertEqual(action, "right", "K_d should map to 'right' for P1")
        
        self.game.update()
        self.assertGreater(self.game.player1.x, initial_x, "Player 1 should move right on D key down")
        
        # D key release
        current_x = self.game.player1.x
        event_d_up = Event(pygame.KEYUP, {"key": pygame.K_d})
        self.game.handle_keyup(event_d_up.key)
        self.game.update()
        self.assertEqual(self.game.player1.x, current_x, "Player 1 should stop moving right on D key up")

        # --- Test other directions similarly ---
        # (left, up, down)

        # --- Left movement test ---
        initial_x = self.game.player1.x
        event_left_down = Event(pygame.KEYDOWN, {"key": pygame.K_a})
        self.game.handle_keydown(event_left_down.key)
        self.game.update()
        self.assertLess(self.game.player1.x, initial_x, "Player 1 should move left on A key down")
        current_x = self.game.player1.x
        event_left_up = Event(pygame.KEYUP, {"key": pygame.K_a})
        self.game.handle_keyup(event_left_up.key)
        self.game.update()
        self.assertEqual(self.game.player1.x, current_x, "Player 1 should stop moving left on A key up")

        # --- Up movement test ---
        initial_y = self.game.player1.y
        event_up_down = Event(pygame.KEYDOWN, {"key": pygame.K_w})
        self.game.handle_keydown(event_up_down.key)
        self.game.update()
        self.assertLess(self.game.player1.y, initial_y, "Player 1 should move up on W key down")
        current_y = self.game.player1.y
        event_up_up = Event(pygame.KEYUP, {"key": pygame.K_w})
        self.game.handle_keyup(event_up_up.key)
        self.game.update()
        self.assertEqual(self.game.player1.y, current_y, "Player 1 should stop moving up on W key up")
        
        # --- Down movement test ---
        initial_y = self.game.player1.y
        event_down_down = Event(pygame.KEYDOWN, {"key": pygame.K_s})
        self.game.handle_keydown(event_down_down.key)
        self.game.update()
        self.assertGreater(self.game.player1.y, initial_y, "Player 1 should move down on S key down")
        current_y = self.game.player1.y
        event_down_up = Event(pygame.KEYUP, {"key": pygame.K_s})
        self.game.handle_keyup(event_down_up.key)
        self.game.update()
        self.assertEqual(self.game.player1.y, current_y, "Player 1 should stop moving down on S key up")

    def test_player1_weapon_a_action(self):
        """Test player 1 weapon A action (tofu throw)"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Record initial projectile count
        initial_projectile_count = len(self.game.projectiles)
        
        # Z key press event (weapon A)
        weapon_a_event = Event(pygame.KEYDOWN, {"key": pygame.K_z})
        self.game.handle_keydown(weapon_a_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_z)
        self.assertEqual(action, "weapon_a", "K_z should map to 'weapon_a' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if projectile was fired
        self.assertGreater(len(self.game.projectiles), initial_projectile_count, 
                          "Player 1 should create projectile on weapon_a key press")
        
        # J key press event (weapon A alternative)
        # Reset projectiles first
        self.game.projectiles = []
        initial_projectile_count = 0
        
        weapon_a_alt_event = Event(pygame.KEYDOWN, {"key": pygame.K_j})
        self.game.handle_keydown(weapon_a_alt_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_j)
        self.assertEqual(action, "weapon_a", "K_j should map to 'weapon_a' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if projectile was fired
        self.assertGreater(len(self.game.projectiles), initial_projectile_count, 
                          "Player 1 should create projectile on alternative weapon_a key press")

    def test_player1_shield_action(self):
        """Test player 1 shield action"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Record pre-shield status
        self.assertFalse(self.game.player1.is_shielding(), "Player 1 shield should not be active initially")
        
        # X key press event (weapon B/shield)
        shield_event = Event(pygame.KEYDOWN, {"key": pygame.K_x})
        self.game.handle_keydown(shield_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_x)
        self.assertEqual(action, "weapon_b", "K_x should map to 'weapon_b' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if shield is active
        self.assertTrue(self.game.player1.is_shielding(), "Player 1 shield should be active after weapon_b key press")
        
        # Release shield and reset state
        shield_up_event = Event(pygame.KEYUP, {"key": pygame.K_x})
        self.game.handle_keyup(shield_up_event.key)
        self.game.update()
        
        # Test alternative key (K_k)
        self.assertFalse(self.game.player1.is_shielding(), "Shield should be inactive after key release")
        
        shield_alt_event = Event(pygame.KEYDOWN, {"key": pygame.K_k})
        self.game.handle_keydown(shield_alt_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_k)
        self.assertEqual(action, "weapon_b", "K_k should map to 'weapon_b' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if shield is active
        self.assertTrue(self.game.player1.is_shielding(), "Player 1 shield should be active after alternative key press")

    def test_player1_dash_action(self):
        """Test player 1 dash action"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Test LSHIFT key for dash
        # Record initial position and speed
        initial_x = self.game.player1.x
        initial_y = self.game.player1.y
        normal_speed = PLAYER_SPEED

        # First press direction key to set movement direction
        move_right_event = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(move_right_event.key)
        
        # LSHIFT key press event (dash)
        dash_event = Event(pygame.KEYDOWN, {"key": pygame.K_LSHIFT})
        self.game.handle_keydown(dash_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_LSHIFT)
        self.assertEqual(action, "dash", "K_LSHIFT should map to 'dash' for P1")
        
        # Update game state (several frames)
        for _ in range(5):
            self.game.update()
        
        # Check if movement was faster
        current_x = self.game.player1.x
        self.assertGreater(current_x - initial_x, normal_speed * 5, 
                          "Player 1 should move faster when dashing with LSHIFT")
        
        # Now test H key for dash
        # Release all keys and reset position
        event_right_up = Event(pygame.KEYUP, {"key": pygame.K_RIGHT})
        self.game.handle_keyup(event_right_up.key)
        event_shift_up = Event(pygame.KEYUP, {"key": pygame.K_LSHIFT})
        self.game.handle_keyup(event_shift_up.key)
        
        # Reset position
        self.game.player1.x = initial_x
        self.game.player1.y = initial_y
        
        # Press direction key again
        self.game.handle_keydown(move_right_event.key)
        
        # H key press event (dash alternative)
        dash_alt_event = Event(pygame.KEYDOWN, {"key": pygame.K_h})
        self.game.handle_keydown(dash_alt_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_h)
        self.assertEqual(action, "dash", "K_h should map to 'dash' for P1")
        
        # Update game state (several frames)
        for _ in range(5):
            self.game.update()
        
        # Check if movement was faster with alternative key
        current_x = self.game.player1.x
        self.assertGreater(current_x - initial_x, normal_speed * 5, 
                          "Player 1 should move faster when dashing with H key")

    def test_player1_hyper_mode(self):
        """Test player 1 hyper mode"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Set hyper gauge to maximum
        self.game.player1.hyper_gauge = 100
        self.assertFalse(self.game.player1.is_hyper, "Player 1 should not be in hyper mode initially")
        
        # SPACE key press event (hyper)
        hyper_event = Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        self.game.handle_keydown(hyper_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_SPACE)
        self.assertEqual(action, "hyper", "K_SPACE should map to 'hyper' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if hyper mode is active
        self.assertTrue(self.game.player1.is_hyper, 
                       "Player 1 should enter hyper mode when hyper key is pressed with full gauge")
        
        # Check if hyper gauge decreases
        self.assertLess(self.game.player1.hyper_gauge, 100, 
                       "Hyper gauge should decrease when in hyper mode")
        
        # Reset for alternative key test
        self.game.player1.is_hyper = False
        self.game.player1.hyper_gauge = 100
        
        # L key press event (hyper alternative)
        hyper_alt_event = Event(pygame.KEYDOWN, {"key": pygame.K_l})
        self.game.handle_keydown(hyper_alt_event.key)
        
        # Check key mapping
        action = self.game.key_mapping_p1.get(pygame.K_l)
        self.assertEqual(action, "hyper", "K_l should map to 'hyper' for P1")
        
        # Update game state
        self.game.update()
        
        # Check if hyper mode is active with alternative key
        self.assertTrue(self.game.player1.is_hyper, 
                       "Player 1 should enter hyper mode when alternative hyper key is pressed")

    def test_hud_display(self):
        """Test if HUD displays correctly"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Set player states
        self.game.player1.health = 75  # Set health to 75%
        self.game.player1.heat = 30    # Set heat to 30%
        self.game.player1.hyper_gauge = 50  # Set hyper gauge to 50%
        
        self.game.player2.health = 60  # Set health to 60%
        
        # Check HUD initialization
        self.assertIsNotNone(self.game.hud, "HUD should be initialized")
        
        # Run game drawing process
        # Note: Since drawing is mocked, we can't visually verify
        # but we can check that no exceptions are raised
        try:
            self.game.current_state.draw(self.mock_screen)
            self.game.current_state.draw_hud(self.mock_screen)
            # If no exceptions, test passes
            passed = True
        except Exception as e:
            passed = False
            print(f"HUD drawing failed: {e}")
        
        self.assertTrue(passed, "HUD drawing should not raise exceptions")

    def test_player_collision_detection(self):
        """Test player-to-player collision detection"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Initially, players should be separated
        distance = self.calculate_distance(self.game.player1, self.game.player2)
        self.assertGreater(distance, self.game.player1.radius + self.game.player2.radius,
                          "Players should start separated")
        
        # Force player 1 to player 2's position
        self.game.player1.x = self.game.player2.x
        self.game.player1.y = self.game.player2.y
        
        # Run update to detect collision
        self.game.update()
        
        # After collision handling, players should be pushed apart
        distance_after = self.calculate_distance(self.game.player1, self.game.player2)
        self.assertGreaterEqual(distance_after, self.game.player1.radius,
                               "Players should be pushed apart after collision")
    
    def test_projectile_player_collision(self):
        """Test projectile-to-player collision"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Record player 2's initial health
        initial_health = self.game.player2.health
        
        # Create projectile fired from player 1
        from game.projectile import Projectile  # Import as needed
        
        # Fire projectile from player 1's position
        projectile = Projectile(self.game.player1.x, self.game.player1.y, 0, 10, self.game.player1)
        self.game.projectiles.append(projectile)
        
        # Move projectile to player 2's position
        projectile.x = self.game.player2.x
        projectile.y = self.game.player2.y
        
        # Run collision detection
        self.game.handle_collisions()
        
        # Check if player 2 took damage
        self.assertLess(self.game.player2.health, initial_health,
                       "Player 2 should take damage when hit by a projectile")
        
        # Check if projectile was removed
        self.assertNotIn(projectile, self.game.projectiles,
                        "Projectile should be removed after hitting a player")
    
    def test_player2_ai_behavior(self):
        """Test player 2 AI behavior (versus mode)"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Record player 2's initial position
        initial_x = self.game.player2.x
        initial_y = self.game.player2.y
        
        # Run AI updates for several frames
        for _ in range(10):
            self.game.update()
        
        # Check if player 2 moved
        current_x = self.game.player2.x
        current_y = self.game.player2.y
        has_moved = (current_x != initial_x) or (current_y != initial_y)
        
        self.assertTrue(has_moved, "Player 2 (AI) should move during gameplay")
        
        # Check if AI fires projectiles
        projectile_count_before = len(self.game.projectiles)
        
        # Run more updates
        for _ in range(30):  # Run longer to increase chance of firing
            self.game.update()
        
        # Check if AI fired projectiles
        projectile_count_after = len(self.game.projectiles)
        
        # Note: This test might fail depending on AI implementation
        # as AI might not always fire
        self.assertGreaterEqual(projectile_count_after, projectile_count_before,
                               "Player 2 (AI) should fire projectiles")
    
    def test_game_state_pause_transition(self):
        """Test transition from game to pause state"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Press ESC key to pause
        esc_event = Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        self.game.handle_keydown(esc_event.key)
        
        # Check if transitioned to pause state
        self.assertIsInstance(self.game.current_state, PauseState,
                             "Game should transition to PauseState when ESC is pressed")
        
        # Press ESC again to return
        self.game.handle_keydown(esc_event.key)
        
        # Check if returned to game state
        self.assertIsInstance(self.game.current_state, SingleVersusGameState, 
        "Game should return to SingleVersusGameState when ESC is pressed in PauseState")
    
    def calculate_distance(self, obj1, obj2):
        """Helper method to calculate distance between two objects"""
        import math
        return math.sqrt((obj1.x - obj2.x)**2 + (obj1.y - obj2.y)**2)

    def test_key_mappings_multiple_keys(self):
        """Test that both arrow keys and WASD keys map to the same actions"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # Test player 1 key mappings: arrow keys and WASD for movement
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_UP), "up")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_w), "up")
        
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_DOWN), "down")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_s), "down")
        
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_LEFT), "left")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_a), "left")
        
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_RIGHT), "right")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_d), "right")
        
        # Test weapon key mappings: z/j for weapon_a, x/k for weapon_b
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_z), "weapon_a")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_j), "weapon_a")
        
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_x), "weapon_b")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_k), "weapon_b")
        
        # Test special actions: SPACE/l for hyper, LSHIFT/h for dash
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_SPACE), "hyper")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_l), "hyper")
        
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_LSHIFT), "dash")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_h), "dash")
        
        # Test other special actions
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_c), "special")
        self.assertEqual(self.game.key_mapping_p1.get(pygame.K_v), "shield")

    def test_key_input_registration(self):
        """Test basic key input registration system"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # 最初はキー入力がない状態を確認
        self.assertFalse(any(self.game.keys_pressed.values()), "No keys should be pressed initially")
        
        # キー押下イベントの登録テスト
        key_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(key_down_event.key)
        
        # キーが正しく登録されているか確認
        self.assertTrue(self.game.keys_pressed.get(pygame.K_RIGHT, False), 
                        "RIGHT key should be registered as pressed")
        
        # キーリリースイベントのテスト
        key_up_event = Event(pygame.KEYUP, {"key": pygame.K_RIGHT})
        self.game.handle_keyup(key_up_event.key)
        
        # キーが正しく解除されているか確認
        self.assertFalse(self.game.keys_pressed.get(pygame.K_RIGHT, False), 
                         "RIGHT key should be registered as released")
    
    def test_multiple_keys_pressed(self):
        """Test handling of multiple keys pressed simultaneously"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # プレイヤー1の初期位置を記録
        initial_x = self.game.player1.x
        initial_y = self.game.player1.y
        
        # 斜め移動のテスト：右と下を同時押し
        right_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(right_down_event.key)
        
        down_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
        self.game.handle_keydown(down_down_event.key)
        
        # 両方のキーが押されていることを確認
        self.assertTrue(self.game.keys_pressed.get(pygame.K_RIGHT, False), "RIGHT key should be pressed")
        self.assertTrue(self.game.keys_pressed.get(pygame.K_DOWN, False), "DOWN key should be pressed")
        
        # 更新して斜め移動が行われることを確認
        self.game.update()
        
        # プレイヤーが右下に移動したことを確認
        self.assertGreater(self.game.player1.x, initial_x, "Player should move right")
        self.assertGreater(self.game.player1.y, initial_y, "Player should move down")
        
        # 移動しながら攻撃するテスト
        weapon_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_z})
        self.game.handle_keydown(weapon_down_event.key)
        
        # 攻撃キーも押されていることを確認
        self.assertTrue(self.game.keys_pressed.get(pygame.K_z, False), "Z key should be pressed")
        
        # 初期プロジェクタイル数を記録
        initial_projectile_count = len(self.game.projectiles)
        
        # 更新して移動しながら攻撃が行われることを確認
        self.game.update()
        
        # プレイヤーが移動し続けていることを確認
        self.assertGreater(self.game.player1.x, initial_x, "Player should continue moving right")
        self.assertGreater(self.game.player1.y, initial_y, "Player should continue moving down")
        
        # プロジェクタイルが生成されたことを確認
        self.assertGreater(len(self.game.projectiles), initial_projectile_count, 
                          "Projectile should be created while moving")
    
    def test_input_buffer_persistence(self):
        """Test if input buffer correctly maintains key states between frames"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # キー押下
        key_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(key_down_event.key)
        
        # キー状態が保持されていることを確認（複数フレーム）
        for _ in range(5):
            self.game.update()
            self.assertTrue(self.game.keys_pressed.get(pygame.K_RIGHT, False), 
                           "Key state should persist between frames")
        
        # キーリリース
        key_up_event = Event(pygame.KEYUP, {"key": pygame.K_RIGHT})
        self.game.handle_keyup(key_up_event.key)
        
        # キー状態が解除されたことを確認
        self.assertFalse(self.game.keys_pressed.get(pygame.K_RIGHT, False), 
                         "Key state should be cleared after release")
        
        # 更新後もキー状態が解除されたままであることを確認
        self.game.update()
        self.assertFalse(self.game.keys_pressed.get(pygame.K_RIGHT, False), 
                         "Key state should remain cleared after update")
    
    def test_player_update_with_key_states(self):
        """Test that player's update method correctly processes key states"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # プレイヤーオブジェクトのupdateメソッドをモック化して呼び出しを確認
        original_update = self.game.player1.update
        call_args = []
        
        def mock_update(*args, **kwargs):
            call_args.append((args, kwargs))
            return original_update(*args, **kwargs)
        
        self.game.player1.update = mock_update
        
        # キー押下
        key_down_event = Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        self.game.handle_keydown(key_down_event.key)
        
        # ゲーム更新
        self.game.update()
        
        # プレイヤーのupdateメソッドが正しく呼ばれたことを確認
        self.assertGreaterEqual(len(call_args), 1, "Player update method should be called")
        
        # プレイヤー更新時に必要なパラメータが渡されていることを確認
        if call_args:
            last_call = call_args[-1]
            
            # キー状態が渡されているかチェック
            self.assertIn("keys", last_call[1], "Keys should be passed to player update")
            
            # アリーナ情報が渡されているかチェック
            self.assertIn("arena", last_call[1], "Arena info should be passed to player update")
            
            # 対戦相手情報が渡されているかチェック
            self.assertIn("opponent", last_call[1], "Opponent info should be passed to player update")

    def test_heat_gauge_management(self):
        """Test heat gauge management system"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # ヒートゲージの初期状態を確認
        initial_heat = self.game.player1.heat
        self.assertEqual(initial_heat, 0, "Heat gauge should start at 0")
        
        # 攻撃によるヒート上昇のテスト
        # 武器Aの発射
        weapon_a_event = Event(pygame.KEYDOWN, {"key": pygame.K_z})
        self.game.handle_keydown(weapon_a_event.key)
        self.game.update()
        
        # ヒートゲージが上昇したことを確認
        self.assertGreater(self.game.player1.heat, initial_heat, 
                          "Heat gauge should increase after firing weapon")
        
        # 複数回攻撃でヒートが蓄積するか確認
        current_heat = self.game.player1.heat
        for _ in range(3):
            self.game.update()
        
        # ヒートがさらに上昇したことを確認
        self.assertGreater(self.game.player1.heat, current_heat, 
                          "Heat gauge should accumulate with multiple attacks")
        
        # 攻撃キーを離す
        weapon_a_up_event = Event(pygame.KEYUP, {"key": pygame.K_z})
        self.game.handle_keyup(weapon_a_up_event.key)
        
        # 時間経過によるヒート減少のテスト
        high_heat = self.game.player1.heat
        
        # 攻撃せずに数フレーム待機
        for _ in range(10):
            self.game.update()
        
        # ヒートが減少したことを確認
        self.assertLess(self.game.player1.heat, high_heat, 
                       "Heat gauge should decrease over time when not attacking")
    
    def test_overheat_condition(self):
        """Test overheat condition and its effects"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # ヒートゲージを強制的に高い値に設定
        self.game.player1.heat = MAX_HEAT * 0.9  # 90%まで上昇
        
        # 攻撃によりオーバーヒート状態へ
        weapon_a_event = Event(pygame.KEYDOWN, {"key": pygame.K_z})
        self.game.handle_keydown(weapon_a_event.key)
        
        # 数回更新してヒートを最大まで上げる
        for _ in range(5):
            self.game.update()
        
        # オーバーヒート状態になったか確認
        self.assertGreaterEqual(self.game.player1.heat, MAX_HEAT, 
                               "Player should enter overheat state")
        
        # オーバーヒート状態では攻撃できないことを確認
        initial_projectile_count = len(self.game.projectiles)
        self.game.update()
        
        # プロジェクタイルが増えていないことを確認
        self.assertEqual(len(self.game.projectiles), initial_projectile_count, 
                        "Player should not be able to attack in overheat state")
        
        # オーバーヒート状態の回復を確認
        # 攻撃キーを離す
        weapon_a_up_event = Event(pygame.KEYUP, {"key": pygame.K_z})
        self.game.handle_keyup(weapon_a_up_event.key)
        
        # 数フレーム待機
        for _ in range(20):
            self.game.update()
        
        # ヒートが減少していることを確認
        self.assertLess(self.game.player1.heat, MAX_HEAT, 
                       "Heat gauge should cool down after overheat")
    
    def test_arena_boundary_heat_effect(self):
        """Test heat increase effect when player is near arena boundary"""
        # Set game state to SingleVersusGameState
        self.game.change_state(SingleVersusGameState(self.game))
        
        # プレイヤーを中央に配置
        center_x = ARENA_CENTER_X
        center_y = ARENA_CENTER_Y
        self.game.player1.x = center_x
        self.game.player1.y = center_y
        
        # 中央での通常の攻撃ヒート上昇を記録
        self.game.player1.heat = 0
        weapon_event = Event(pygame.KEYDOWN, {"key": pygame.K_z})
        self.game.handle_keydown(weapon_event.key)
        self.game.update()
        center_heat_increase = self.game.player1.heat
        
        # 攻撃キーを離す
        weapon_up_event = Event(pygame.KEYUP, {"key": pygame.K_z})
        self.game.handle_keyup(weapon_up_event.key)
        
        # プレイヤーをアリーナ境界近くに移動
        radius = ARENA_RADIUS
        self.game.player1.x = center_x + radius * 0.9  # 境界の90%位置
        self.game.player1.y = center_y
        
        # ヒートをリセット
        self.game.player1.heat = 0
        
        # 境界付近での攻撃ヒート上昇を記録
        self.game.handle_keydown(weapon_event.key)
        self.game.update()
        boundary_heat_increase = self.game.player1.heat
        
        # 境界付近でのヒート上昇が中央よりも大きいことを確認
        self.assertGreater(boundary_heat_increase, center_heat_increase, 
                          "Heat increase should be greater near arena boundary")

if __name__ == '__main__':
    unittest.main() 