import numpy as np

def distance_to_humans(game_state):
    total_score = 0
    for i in range(game_state.STATE.shape[0]):
        for j in range(game_state.STATE.shape[1]):
            if game_state.STATE[i,j,0] > 0:
                n_human = game_state.STATE[i,j,0]
                dists = []
                for i2,j2 in game_state.TEAM_POSITIONS:
                    if game_state.STATE[i2,j2,game_state.TEAM] >= n_human:
                        dists.append(max(np.abs(i2-i),np.abs(j2-j)))
                if len(dists) > 0:
                    total_score += n_human/min(dists)
    return total_score




def heuristic(game_state):
    is_won = len(game_state.ENEMY_POSITIONS) == 0
    if is_won: return 100
    is_lost = len(game_state.TEAM_POSITIONS) == 0
    if is_lost: return -100
    COEFF_1 = 1
    COEFF_2 = .2
    units_diff = np.sum(game_state.STATE[:,:,game_state.TEAM]) - np.sum(game_state.STATE[:,:,game_state.ENEMY_TEAM])
    heuristic_value = COEFF_1*units_diff + COEFF_2*distance_to_humans(game_state)
    return 100*np.tanh(heuristic_value/100)


def alpha_beta(game_state,rec_depth,alpha=-100,beta=100):
    if rec_depth == 0:
        return heuristic(game_state),None
    GAMMA =0.99999999999
    possible_moves = game_state.get_next_moves()
    max_move = None
    for move in possible_moves:
        game_states = game_state.apply_move(move)
        if len(game_states) > 1:
            score,_ = alpha_beta_proba(game_states,rec_depth,-beta,-alpha)
            score = -GAMMA*score
        else: 
            score,_ = alpha_beta(game_states[0][1],rec_depth-1,-beta,-alpha)
            score = -GAMMA*score
        if score >= beta: #Beta cut
            return beta,move
        if score > alpha:
            alpha,max_move = score,move
    return alpha,max_move


def alpha_beta_proba(game_states,rec_depth,alpha,beta):
    score = 0
    for proba,game_state in game_states:
        rec_score,_ = alpha_beta(game_state,rec_depth-1,alpha,beta)
        score += proba*rec_score
    return score,None
