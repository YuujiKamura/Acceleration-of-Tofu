# Acceleration of Tofu

2D versus shooter (browser, 2-player local). Tofu-themed characters.

## Tech Stack

- TypeScript + Vite for frontend tooling (`web/`, builds to static assets)
- Phaser 3 for 2D rendering (`web/src/scenes/`, `web/src/entities/`)
- GitHub Pages for hosting (static, deployed from `web/dist/` via Pages workflow)
- No backend, no DB, no auth — fully client-side single-session local-versus
- Playwright for visual / e2e regression (`web/e2e/`)
- `legacy/pygbag/` is the original Python + Pygame + pygbag WASM build (predecessor, kept for reference, not the active build target)

## Tips

- Use `cd web && npm run typecheck` and `npm run build` to verify your work as soon as you complete a feature or task. Don't ship without `tsc --noEmit` clean.
- Use the `PLAN.md` file at repo root to guide your work when building new features or balancing.
- Log multi-iteration tuning work under `.logs/` (create new log files as you see fit) to record balance/visual decisions and reference them when iterating. For 1-shot fixes, an issue body is enough — don't over-document.
- Use Playwright (`web/e2e/`) to test the visual output of Phaser scenes when changes affect layout, HUD overlap, or canvas aspect. Iterate if it doesn't look right or fit the tofu theme.
- For asset / sprite generation, save the prompts you used under `.prompts/` so the same visual style can be reproduced later.
- Use Context7 MCP to fetch Phaser 3 docs (`/photonstorm/phaser`) when implementing new scene / entity patterns.
- The Python version under `legacy/pygbag/game/` is the source of truth for original game feel — when porting weapons, AI, or balance, cross-reference Python source line numbers in code comments (existing convention, see `Player.ts` `py:NNN` markers).
- Color palette is centralized in `web/src/config/colors.ts`. Don't introduce hex literals in entity / scene code; import a named constant or add one to the palette.
- Constants (frame counts, cooldowns, damage, speeds) live in `web/src/config/constants.ts`. Same rule: don't hardcode in entities.
