import time

from client import ClientSocket
from argparse import ArgumentParser


def play_game(strategy, args):
    client_socket = ClientSocket(args.ip, args.port)
    client_socket.send_nme("NOM DE VOTRE IA")
    # set message
    message = client_socket.get_message()
    UPDATE_GAME_STATE(message)
    # hum message
    message = client_socket.get_message()
    UPDATE_GAME_STATE(message)
    # hme message
    message = client_socket.get_message()
    UPDATE_GAME_STATE(message)
    # map message
    message = client_socket.get_message()
    UPDATE_GAME_STATE(message)

    # start of the game
    while True:
        message  = client_socket.get_message()
        time_message_received = time.time()
        UPDATE_GAME_STATE(message)
        if message[0] == "upd":
            nb_moves, moves = COMPUTE_NEXT_MOVE(GAME_STATE)
            client_socket.send_mov(nb_moves, moves)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest='ip', default='localhost', type=str, help='IP adress the connection should be made to.')
    parser.add_argument(dest='port', default='5555', type=int, help='Chosen port for the connection.')

    args = parser.parse_args()
    
    play_game()
