# LLM Chess Bot

A stateless chess-playing bot for Lichess powered by a local LLM via an
OpenAI-compatible API.

LLMs are not very good at chess, and this bot proves it.

## Overview

This bot connects to Lichess and plays games using a local LLM (e.g.,
llama.cpp) to select moves. It uses python-chess for move validation and
berserk for Lichess API interaction.

## Requirements

- Python 3.11+
- Lichess API token
- OpenAI-compatible LLM (e.g., llama.cpp)

## Environment Variables

The following environment variables must be set:

- `LICHESS_TOKEN` - Your Lichess API token
- `OPENAI_BASE_URL` - Base URL for the LLM API (e.g. http://localhost:8080/v1)
- `OPENAI_API_KEY` - API key for the LLM
- `MODEL` - Model name to use

## Installation

Install dependencies using uv:

```bash
uv sync
```

## Running Locally

Set the required environment variables and run:

```bash
python main.py
```

## Docker

Build the Docker image:

```bash
docker build -t chessbot:latest .
```

Run the container:

```bash
docker run -d \
  -e LICHESS_TOKEN=your_token \
  -e OPENAI_BASE_URL=http://host.docker.internal:8080/v1 \
  -e OPENAI_API_KEY=your_key \
  -e MODEL=your_model \
  chessbot:latest
```

## Kubernetes

The Docker image is automatically built and pushed to GHCR on push to main.
Deploy using the published image:

```
ghcr.io/erikvanzijst/chessbot:latest
```

Set the required environment variables in your deployment configuration.

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

## Principles

1. **Stateless Move Generation** - Each move is generated independently using
   the current FEN and list of legal moves. The LLM does not maintain
   conversation
   history.

2. **FEN is the Source of Truth** - The board state is always reconstructed
   from the move list using python-chess.

3. **Strict Move Validation** - All LLM outputs are validated against the list
   of legal moves. Invalid moves fall back to a random legal move.

4. **No Hidden State** - The bot does not maintain any implicit memory
   or chat sessions.