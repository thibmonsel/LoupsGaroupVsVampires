from src.reinforcement_learning.runner import Runner
from src.reinforcement_learning.player import Player

# RL test

player_1 = Player(
    'vampires', 
    from_file='player_1_winning',
    is_trainable=False
    # max_memory=50000, 
    # batch_size=20, 
    # max_epsilon=0.5, 
    # min_epsilon=0.001,
    # decay=0.001,
    # gamma=0.99,
    # lr=1e-4
)

player_2 = Player(
    'werewolves', 
    from_file='mainly_winning_strategy',
    # is_random=True
    # max_memory=50000, 
    # batch_size=20, 
    max_epsilon=0.1, 
    min_epsilon=0.001,
    decay=0.001,
    # gamma=0.99,
    lr=2e-4
)

runner = Runner(player_1, player_2, n_games=5000, limit_rounds=80)
runner.run()

runner.plot_results()

player_2.save('mainly_winning_strategy_2')
