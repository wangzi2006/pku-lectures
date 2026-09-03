# Project Notes

## Purpose

`pku-lectures` is a public, human-reviewed board for upcoming lectures at PKU and nearby areas.

## Run and verify

- Install and run: `npm ci`, then `npm run dev`.
- Frontend gates: `npm run lint`, `npm run typecheck`, `npm run build`.
- Bridge test: `node --test local_bridge/test_bridge.mjs`.
- Pipeline tests require Python 3.12 and `pipeline/requirements.txt`.

## Stack

- React 19 + TypeScript + vinext, exported as a static GitHub Pages site.
- Python pipelines and GitHub Actions handle crawling, review, feedback, and data writes.
- A Windows PowerShell/Node bridge sends local WeRSS discoveries to GitHub Issues.

## Sources of truth

- `data/sources.json`: approved sources, including WeRSS `feedId` values.
- `config/policy.json`, `config/topics.json`, `config/regions.json`: filtering and display policy.
- `data/lectures.json`: published lectures; `data/candidates.json`: pending review.
- `README.md`: public usage and operations contract.

## Safety and conventions

- Never commit API keys, GitHub tokens, WeChat cookies, QR sessions, or copied article bodies.
- Keep local credentials under `%LOCALAPPDATA%\pku-lectures`; only metadata and original links may reach Issues.
- Preserve short sequential review IDs (`L001`, `S001`) and 0–1 confidence values.
- Owner review remains the publication gate; model output does not publish directly.

## Current state

- `main` deploys automatically to the public GitHub Pages URL in `README.md`.
- The local WeRSS bridge is installed; a successful empty bridge run does not prove WeRSS fetched articles.
- Next operational step: verify a real WeRSS article reaches a `[公众号文章]` Issue, then add more approved accounts.
