# AGENTS.md

## Overview

This project implements a chess-playing bot for Lichess using a local LLM served via an OpenAI-compatible API (e.g. llama.cpp).

The system is intentionally minimal and deterministic:

* No chess engine (e.g. Stockfish)
* No long-running LLM sessions
* Stateless move generation per turn
* Strict legality enforcement

---

## Architecture

```
Lichess API (berserk)
        ↓
Game loop (bot.py)
        ↓
Board state (python-chess)
        ↓
LLM (via OpenAI-compatible API)
        ↓
Move validation
        ↓
Lichess move submission
```

---

## Core Principles

### 1. Stateless Move Generation

Each move is generated independently using:

* Current FEN
* List of legal moves

The LLM must not rely on conversation history.

**Rationale:**

* Avoids drift and hallucination
* Keeps latency and token usage low
* Ensures deterministic behavior

---

### 2. FEN is the Source of Truth

The board state must always be reconstructed from the move list using `python-chess`.

Do NOT rely on:

* LLM memory
* Incremental board updates without validation

---

### 3. Strict Move Validation

All LLM outputs must be validated:

* Must parse as UCI
* Must be in `board.legal_moves`

If invalid:

* Fallback to a deterministic or random legal move

---

### 4. No Hidden State

Avoid implicit memory such as:

* Chat sessions
* Long prompt histories

If strategy is needed, it must be:

* Explicit
* Injected into the prompt each turn

---

## LLM Integration

### Backend

The LLM is accessed via an OpenAI-compatible API (e.g. llama.cpp):

```
https://ai.deprutser.be/v1/chat/completions
```

### Client

Use the official OpenAI Python client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="{OPENAI_BASE_URL}",
    api_key="{OPENAI_API_KEY}"
)
```

---

### Prompt Requirements

Each call MUST include:

* FEN string
* Full list of legal moves

Example:

```
FEN:
<fen>

Legal moves:
[e2e4, d2d4, ...]

Return ONLY one move in UCI format.
```

---

### Output Requirements

The model must return:

```
e2e4
```

No:

* explanations
* punctuation
* additional text

---

## Game Loop

### Event Handling

The bot listens to:

* `challenge` → accept
* `gameStart` → begin play loop

### Game State

Two event types:

* `gameFull` → contains player info (used to determine color)
* `gameState` → contains moves

---

### Color Handling

The bot determines its color from `gameFull`:

```
is_white = (white_player_id == bot_id)
```

Turn logic:

```
board.turn == is_white
```

---

## Move Selection Pipeline

1. Receive move list from Lichess
2. Reconstruct board using `python-chess`
3. Check if it is our turn
4. Generate legal moves
5. Call LLM
6. Validate move
7. Submit move

---

## Failure Handling

### Invalid LLM Output

If:

* Move is malformed
* Move is illegal

Then:

* Select fallback move from legal moves

---

### API Failures

If LLM call fails:

* Retry once (optional)
* Otherwise fallback to legal move

---

## Performance Considerations

* Keep prompts short
* Use low `max_tokens` (e.g. 20–50)
* Use low temperature (e.g. 0.1–0.3)
* Avoid streaming unless needed

---

## Non-Goals

This project does NOT aim to:

* Compete with chess engines
* Provide deep search or evaluation
* Maintain long-term memory via chat sessions

---

## Future Improvements

Possible extensions:

### 1. Strategy Layer

Maintain a small structured strategy object:

* plan (e.g. "attack kingside")
* priorities
* constraints

Inject into prompt each turn.

---

### 2. Multi-Sample Voting

Call LLM multiple times and select:

* most frequent move
* or best scored move

---

### 3. Blunder Filtering

Add a second LLM pass:

* evaluate candidate moves
* reject obvious blunders

---

### 4. Opening Memory

Track early moves and bias toward:

* common openings
* consistent development

---

## Development Guidelines

* Keep logic simple and explicit
* Prefer determinism over cleverness
* Avoid hidden state
* Validate all external outputs
* Log decisions for debugging

---

## Summary

This project treats the LLM as:

> A stateless heuristic move selector constrained by strict rules

All correctness comes from:

* `python-chess` (rules)
* Lichess API (game state)

The LLM provides:

* style
* heuristics
* imperfect but interesting play
