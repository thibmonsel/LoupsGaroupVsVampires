import time

def format_moves_for_response(moves):
    print(moves)
    return [[source[0],source[1],nb,dest[0],dest[1]] for source,nb,dest in moves]


def compute_next_move(game_state):
    time.sleep(1)
    return 1, format_moves_for_response([game_state.get_possible_moves()[0]])
