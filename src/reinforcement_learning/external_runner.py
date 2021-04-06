import time

from src.client import ClientSocket
from src.environment import Environment
from src.reinforcement_learning.player import Player

def rl_play(args, filename):
    environment = Environment()

    player = Player('vampires', 
                    from_file=filename, 
                    max_epsilon=0, 
                    min_epsilon=0)

    print('Player loaded')

    client_socket = ClientSocket(args.ip, args.port)
    client_socket.send_nme(filename)
    
    # set message
    [_, [height, width]] = client_socket.get_message()
    
    # hum message
    _ = client_socket.get_message()
    
    # hme message
    [_, [x_init, y_init]] = client_socket.get_message()

    # map message
    [_, map_array] = client_socket.get_message()
    
    environment.set_map_from_server(width, height, map_array)
    
    race, _ = environment.find_group(x_init, y_init)
    player.set_race(race)

    # start of the game
    while True:
        message = client_socket.get_message()
        receiving_message_time = time.time()

        if message[0] == 'upd':
            [_, update_array] = message
            environment.update_map_from_server(update_array)

            _, moves = player.play(environment)
            moves_for_server = list()
            for (x_start, y_start), n_units, (x_end, y_end) in moves:
                moves_for_server.append([x_start, y_start, n_units, x_end, y_end])
            
            time.sleep(0.6 - (time.time() - receiving_message_time))

            client_socket.send_mov(len(moves_for_server), moves_for_server)
