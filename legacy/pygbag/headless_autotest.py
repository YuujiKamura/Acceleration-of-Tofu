import os
import sys
import pygame

# Set dummy drivers for headless environment
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.game import Game
from game.states import AutoTestState

def main():
    print("Initializing Pygame (Headless)...")
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    print("Starting Game in AutoTestMode...")
    game = Game(screen, debug=True)
    game.change_state(AutoTestState(game))
    
    # Run for 10 seconds (600 frames at 60 FPS)
    frames_to_run = 600
    print(f"Running simulation for {frames_to_run} frames...")
    
    for frame in range(frames_to_run):
        game.update()
        if frame % 60 == 0:
            print(f"Frame {frame}: P1 HP={game.player1.health:.1f}, P2 HP={game.player2.health:.1f}")
        
        # Check if match ended early
        if game.player1.health <= 0 or game.player2.health <= 0:
            print(f"Match ended at frame {frame}")
            break
            
    print("Simulation complete.")
    pygame.quit()

if __name__ == "__main__":
    main()
