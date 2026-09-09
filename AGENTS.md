# Project Notes

## Purpose

`pku-lectures` is a public, rule-filtered board for upcoming lectures at PKU and nearby areas.

## Run and verify

- Install and run: `npm ci`, then `npm run dev`.
- Frontend gates: `npm run lint`, `npm run typecheck`, `npm run build`.
- Bridge test: `node --test local_bridge/test_bridge.mjs`.
- Pipeline tests require Python 3.12 and `pipeline/requirements.txt`.

## Stack

- React 19 + TypeScript + vinext, exported as a static GitHub Pages site.
- Python pipelines and GitHub Actions handle crawling, automatic publication, source review, feedback, and data writes.
- A Windows PowerShell/Node bridge sends local WeRSS discoveries to GitHub Issues.

## Sources of truth

- `data/sources.json`: approved sources, including WeRSS `feedId` values.
- `config/policy.json`, `config/topics.json`, `config/regions.json`: filtering and display policy.
- `data/lectures.json`: published lectures; `data/candidates.json`: transient publication queue.
- `README.md`: public usage and operations contract.

## Safety and conventions

- Never commit API keys, GitHub tokens, WeChat cookies, QR sessions, or copied article bodies.
- Keep local credentials under `%LOCALAPPDATA%\pku-lectures`; only metadata and original links may reach Issues.
- Preserve short sequential IDs (`L001`, `S001`) and 0–1 confidence values.
- Lecture publication is automatic after deterministic hard exclusions, thresholds, time-window checks, and deduplication. New sources remain Owner-gated.

## Current state

- Pages deploys the latest `main` after human pushes and successful daily, WeChat intake, source-review, and settings workflows.
- The local WeRSS task covers six approved accounts at 08:17 daily; the Windows bridge checks at 08:27. A successful empty bridge run does not prove WeRSS fetched articles.
- Next operational checks: confirm the next automated data update triggers Pages, and verify one real WeRSS article reaches a `[公众号文章]` Issue and appears on the public site when it passes the fixed rules.
