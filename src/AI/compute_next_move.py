import random
from AI.alpha_beta import alpha_beta

def format_moves_for_response(moves):
    return [[source[0],source[1],nb,dest[0],dest[1]] for source,nb,dest in moves]


def compute_next_move(game_state):
    score,move = alpha_beta(game_state,6)
    print(score,move)
    return len(move), format_moves_for_response(move)
