#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import sys
import traceback

import pygame

from game.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.game import Game
from game.i18n import set_language, tr


async def main():
    # argparse: works on desktop; in browser (pygbag) argv is minimal so no args.
    parser = argparse.ArgumentParser(description="Acceleration of Tofu")
    parser.add_argument("-d", "--debug", action="store_true", help="デバッグモードを有効化 / Enable debug mode")
    parser.add_argument("--lang", default=None, help="Language code (ja, en, ...). Overrides auto-detect.")
    # Tolerate unknown args (e.g. pygbag may inject flags).
    args, _unknown = parser.parse_known_args()

    # Apply CLI-provided language if any; otherwise i18n auto-detected at import.
    if args.lang:
        set_language(args.lang)

    # mixer は pygame.init() より前に pre_init すること (pygbag/WASM では必須)。
    # buffer=512 はブラウザの AudioContext コールバック周期より短くアンダーランで音割れするため 1024 に拡大。
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
    pygame.init()
    pygame.display.set_caption(tr("title"))

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Game.__init__ が既に TitleState を current_state に設定しているので、
    # ここで追加の change_state は呼ばない (スプラッシュは廃止)。
    game = Game(screen, debug=args.debug)

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
