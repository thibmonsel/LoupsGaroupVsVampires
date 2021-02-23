import time

from client import ClientSocket
from argparse import ArgumentParser

from state import GameState


def play_game(args):
    game_state = GameState()
    client_socket = ClientSocket(args.ip, args.port)
    client_socket.send_nme("NOM DE VOTRE IA")
    # set message
    message = client_socket.get_message()
    game_state.update_game_state(message)
    # hum message
    message = client_socket.get_message()
    game_state.update_game_state(message)
    # hme message
    message = client_socket.get_message()
    game_state.update_game_state(message)
    # map message
    message = client_socket.get_message()
    game_state.update_game_state(message)
    print(game_state.STATE,game_state.TEAM, game_state.TEAM_POSITIONS)
    print(game_state.get_possible_moves())
    # start of the game
    while True:
        message  = client_socket.get_message()
        time_message_received = time.time()
        game_state.update_game_state(message)
        if message[0] == "upd":
            nb_moves, moves = COMPUTE_NEXT_MOVE(game_state.STATE)
            client_socket.send_mov(nb_moves, moves)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest='ip', default='localhost', type=str, help='IP adress the connection should be made to.')
    parser.add_argument(dest='port', default='5555', type=int, help='Chosen port for the connection.')

    args = parser.parse_args()
    
    play_game(args)
