#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import sys
import traceback

import pygame

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from game.game import Game
from game.states import SplashScreenState


async def main():
    # argparse: works on desktop; in browser (pygbag) argv is minimal so no args.
    parser = argparse.ArgumentParser(description="豆腐の加速")
    parser.add_argument("-d", "--debug", action="store_true", help="デバッグモードを有効化")
    # Tolerate unknown args (e.g. pygbag may inject flags).
    args, _unknown = parser.parse_known_args()

    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    game = Game(screen, debug=args.debug)
    game.change_state(SplashScreenState(game))

    running = True
    while running:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
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

            # Yield to browser event loop (required by pygbag, no-op on desktop).
            await asyncio.sleep(0)
        except Exception:
            traceback.print_exc()
            running = False

    pygame.quit()
    # sys.exit would abort pygbag's Python runtime; just return instead.
    if sys.platform != "emscripten":
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
