from src.reinforcement_learning.runner import Runner
from src.reinforcement_learning.player import Player

# RL test

player_1 = Player(
    'vampires', 
    # from_file='player_1'
    max_memory=1000, 
    batch_size=10, 
    max_epsilon=0.5, 
    min_epsilon=0.001,
    decay=0.001,
    gamma=0.99,
    lr=1e-4
)

player_2 = Player(
    'werewolves', 
    is_random=True
    # max_memory=1000, 
    # batch_size=10, 
    # max_epsilon=0.5, 
    # min_epsilon=0.001,
    # decay=0.001,
    # gamma=0.99,
    # lr=1e-4
)

runner = Runner(player_1, player_2, n_games=10000, limit_rounds=50)
runner.run()

runner.plot_results()

player_1.save('player_1')
