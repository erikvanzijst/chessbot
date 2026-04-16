import json
import logging
import os
import random
from threading import Thread

import chess
import berserk
from openai import OpenAI

from chessbot.log import setup_logging

logger = setup_logging("chessbot")


LICHESS_TOKEN = os.environ["LICHESS_TOKEN"]
OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.environ["MODEL"]

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session)

llm = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


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
            reasoning_effort="none",
        )

        reasoning = response.choices[0].message.reasoning_content.strip()
        logger.debug(reasoning)
        move = response.choices[0].message.content.strip()
        return move, reasoning

    except Exception:
        logger.exception(f"LLM error")
        return None, None


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

    logger.warning(f"Invalid LLM move: {llm_move}, falling back to a random move")
    return random.choice(legal_moves)


def play_game(game_id, bot_id):
    logger.info(f"Starting game {game_id}")

    color = None
    opponent_id = None

    def log(msg, level=logging.INFO):
        logger.log(level, f"[{game_id} - {opponent_id}] {msg}")

    for state in client.bots.stream_game_state(game_id):
        logger.debug(f"State: {json.dumps(state, indent=2, default=str)}")

        if "winner" in state:

            log(f"Game over. Winner: {bot_id if (state['winner'] == color) else opponent_id}")
            break
        elif "stalemate" in state:
            log("Stalemate")
            break

        elif state["type"] in ["gameFull", "gameState"]:
            if state["type"] == "gameFull":
                color = "white" if state["white"]["id"] == bot_id else "black"
                opponent_id = state["white"]["id"] if state["black"]["id"] == bot_id else state["black"]["id"]

                log(f"Playing as {color}")
                moves = state["state"]["moves"]
                board = build_board(moves)

            else:
                moves = state["moves"]
                board = build_board(moves)
                if color is None:
                    continue

            log(f"Constructing board from moves", logging.DEBUG)
            log(f"Board: {board.fen()}", logging.DEBUG)

            if not is_our_turn(board, color == "white"):
                log(f"{opponent_id}'s turn")
                continue
            else:
                log("Our turn")

            legal_moves = [m.uci() for m in board.legal_moves]

            llm_move, reasoning = call_llm(board.fen(), color, legal_moves)
            move = choose_safe_move(board, llm_move)

            log(f"Playing move: {move}")

            client.bots.make_move(game_id, move)
            # TODO: Lichess has a hard 140 char limit on chat messages
            # if reasoning:
            #     try:
            #         client.board.post_message(
            #             game_id, reasoning[:500], room="player"
            #         )
            #     except Exception as e:
            #         logger.warning(f"Failed to send chat: {e}")


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
