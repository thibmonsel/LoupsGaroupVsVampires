import time
import random

def format_moves_for_response(moves):
    return [[source[0],source[1],nb,dest[0],dest[1]] for source,nb,dest in moves]


def compute_next_move(game_state):
    time.sleep(1)
    moves_possibilities = list(game_state.get_possible_moves())
    moves = random.choice(moves_possibilities)
    return len(moves), format_moves_for_response(moves)
