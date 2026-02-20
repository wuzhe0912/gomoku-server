# Gomoku Server Guidelines

This repo is public and follows the shared conventions from the project.

## Commit Message Format

```text
[Type][Scope] Short description
```

Examples:

```text
[Feature][ws] Add websocket endpoint for room sessions
[Feature][room] Start game automatically when second player joins
[Fix][game] Reject out-of-board coordinates and occupied cells
```

### Type

- `Feature`
- `Fix`
- `Refactor`
- `Chore`
- `Docs`
- `Style`
- `Test`

### Scope (Server)

- `ws`: websocket handlers and protocol events
- `room`: room creation/join/leave lifecycle
- `game`: board state, turn control, win checks
- `api`: health check and HTTP endpoints
- `reconnect`: reconnect and state recovery flow
- `timer`: per-turn timeout logic
- `infra`: Docker, compose, deploy, environment setup
- `deps`: dependency updates
- `docs`: repo docs

## Conventions

- Commit title only. No `Co-Authored-By` or auto-generated signature lines.
- Keep one logical change per commit.
- Do not commit secrets. Keep `.env` in `.gitignore`, maintain `.env.example` if needed.
- Default prose can be Traditional Chinese; keep technical terms in English.

