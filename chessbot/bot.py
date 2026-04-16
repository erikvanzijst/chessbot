import json
import os
import random
from threading import Thread

import chess
import berserk
from openai import OpenAI

from chessbot.log import setup_logging

logger = setup_logging("chessbot")


# -----------------------------
# Config
# -----------------------------
LICHESS_TOKEN = os.environ["LICHESS_TOKEN"]
OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.environ["MODEL"]

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session)

llm = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)

def call_llm(fen, color, legal_moves):
    prompt = f"""
You are a chess move generator. You are playing as {color}.

The current board layout (FEN) is as follows:
{fen}

The only currently available legal moves are:
{legal_moves}

You must choose the next move to make.

ABSOLUTELY CRITICAL RULES TO ABIDE BY:
- Given the position, immediately return the best move
- Do NOT explain
- Do NOT include reasoning
- Do NOT think step-by-step
- You MUST choose ONLY from the legal moves list
- RETURN ONLY A MOVE IN UCI FORMAT -- NO OTHER OUTPUT (e.g. e2e4)
"""

    try:
        response = llm.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=10000,
            stream=False,
            reasoning_effort="none"
        )

        logger.debug(response.choices[0].message.reasoning_content.strip())
        move = response.choices[0].message.content.strip()
        return move

    except Exception:
        logger.exception(f"LLM error")
        return None


def build_board(moves_str):
    board = chess.Board()
    if moves_str.strip():
        for m in moves_str.split():
            board.push_uci(m)
    return board


def is_our_turn(board, is_white_bot):
    return board.turn == is_white_bot


def choose_safe_move(board, llm_move):
    legal_moves = [m.uci() for m in board.legal_moves]

    if llm_move in legal_moves:
        return llm_move

    logger.warning(f"Invalid LLM move: {llm_move}, falling back")
    return random.choice(legal_moves)


# -----------------------------
# Game loop
# -----------------------------
def play_game(game_id, bot_id):
    logger.info(f"Starting game {game_id}")

    is_white_bot = None

    for state in client.bots.stream_game_state(game_id):
        logger.debug(f"State: {json.dumps(state, indent=2, default=str)}")

        if 'winner' in state:
            logger.info(f"Game over. Winner: {state['winner']}")
            break

        elif state["type"] in ["gameFull", "gameState"]:
            if state["type"] == "gameFull":
                white_id = state["white"]["id"]
                if is_white_bot is None:
                    is_white_bot = (white_id == bot_id)
                    logger.info(f"Playing as {'white' if is_white_bot else 'black'}")
                moves = state["state"]["moves"]
                board = build_board(moves)

            else:
                moves = state["moves"]
                board = build_board(moves)
                if is_white_bot is None:
                    continue

            logger.debug(f"Constructing board from moves")
            logger.debug(f"Board: {board.fen()}")

            if not is_our_turn(board, is_white_bot):
                logger.info("Not our turn")
                continue

            logger.info("Our turn")

            legal_moves = [m.uci() for m in board.legal_moves]

            llm_move = call_llm(board.fen(), 'white' if is_white_bot else 'black', legal_moves)
            move = choose_safe_move(board, llm_move)

            logger.info(f"Playing move: {move}")

            try:
                client.bots.make_move(game_id, move)
            except Exception as e:
                logger.exception(f"Failed to send move: {e}")


def main():
    account = client.account.get()
    bot_id = account["id"]

    logger.info(f"Logged in as: {bot_id}")

    for event in client.bots.stream_incoming_events():

        if event["type"] == "challenge":
            challenge_id = event["challenge"]["id"]
            logger.info(f"Accepting challenge {challenge_id}")
            client.bots.accept_challenge(challenge_id)

        elif event["type"] == "gameStart":
            game_id = event["game"]["id"]
            Thread(target=play_game, args=(game_id, bot_id)).start()
