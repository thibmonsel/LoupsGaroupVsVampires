from argparse import ArgumentParser

from src.reinforcement_learning.external_runner import rl_play


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(dest='ip', default='localhost', type=str, help='IP adress the connection should be made to.')
    parser.add_argument(dest='port', default='5555', type=int, help='Chosen port for the connection.')

    args = parser.parse_args()
    
    rl_play(args, 'mainly_winning_strategy_2')
