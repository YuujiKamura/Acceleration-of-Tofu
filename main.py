#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import traceback

import pygame

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.game import Game
from game.states import SplashScreenState


def main():
    parser = argparse.ArgumentParser(description="豆腐の加速")
    parser.add_argument("-d", "--debug", action="store_true", help="デバッグモードを有効化")
    args = parser.parse_args()

    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    game = Game(screen, debug=args.debug)
    game.change_state(SplashScreenState(game))

    while True:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    game.handle_keydown(event.key)
                    if event.key == pygame.K_d:
                        game.toggle_debug_mode()
                elif event.type == pygame.KEYUP:
                    game.handle_keyup(event.key)

            game.update()
            screen.fill((0, 0, 0))
            game.draw()

            pygame.display.flip()
            clock.tick(FPS)
        except Exception:
            traceback.print_exc()
            pygame.quit()
            sys.exit(1)


if __name__ == "__main__":
    main()
