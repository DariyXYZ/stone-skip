# Stone Skipping Asset Workflow

Linear source of truth:

1. Edit art in `stone-skipping-shop-assets-editor.html`.
2. Click `Save browser draft` to preview the change in the game.
3. Tell Codex: `bake assets`.
4. Codex runs `python tools/bake_assets.py`.
5. Review `git diff`, then commit/push only after explicit approval.

The browser draft is temporary. The durable asset source is
`assets/stone-skipping-assets.json`, and the baked playable fallback is the
embedded `ASSET_PACK` in `stone-skipping-game.html`.

Fallback when browser storage is unavailable: use `Download patch` in the
editor, put that JSON in the repo, then run
`python tools/bake_assets.py --input path/to/downloaded.json`.

Do not treat browser `localStorage` as the final version.
