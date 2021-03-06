from DFA import DFA
from DFA import DRA
from DFA import DRA2
from DFA import Action
from MDP import MDP
import time
from copy import deepcopy as dcp
import numpy as np

if __name__ == '__main__':
    # DFA generated from LTL:
    # (F (G1 and G3) or F (G3 and G1)) and G !G2
    g1 = Action('g1')
    g2 = Action('g2') # set as an globally unsafe obstacle
    g3 = Action('g3')
    g23 = Action('g2&g3')
    obs = Action('obs')
    phi = Action('phi')
    whole = Action('whole')
    trial_number = 100

    row, col = 6, 8
    i, j = range(1, row + 1), range(1, col + 1)
    states = [[x, y] for x in i for y in j]
    S = [tuple([x, y]) for x in i for y in j]

    # # print  S

    s_q = {}
    q_s = {}
    q_s[g1.v] = [(3, 1), (3, 2)]  # (1, 2), (1, 3)
    q_s[obs.v] = [(2, 4), (3, 4), (4, 4), (5, 1), (5, 2), (6, 1), (6, 2), (1, 6), (2, 6), (6, 6)]  # (3, 4), (4, 4), (5, 4)
    q_s[g2.v] = [(3, 8), (4, 8)] # (4, 8)
    q_s[g23.v] = [(4, 8)]
    q_s[g3.v] = [(5, 8), (4, 8)]  # (4, 8),
    q_s[phi.v] = list(set(S) - set(q_s[g1.v] + q_s[g2.v] + q_s[g3.v] + q_s[obs.v]))
    q_s[whole.v] = S
    for s in S:
        s_q[s] = []
        if s in q_s[g1.v] and g1.v not in s_q[s]:
            s_q[s].append(g1.v)
        if s in q_s[g2.v] and g2.v not in s_q[s]:
            s_q[s].append(g2.v)
        if s in q_s[g3.v] and g3.v not in s_q[s]:
            s_q[s].append(g3.v)
        if s in q_s[g23.v] and g23.v not in s_q[s]:
            # s_q[s].append(g23.v)
            s_q[s] = [g23.v]
            # temp = g23.v.split('-')
            # for element in temp:
            #     if element not in s_q[s]:
            #         s_q[s].append(element)
        if s in q_s[obs.v] and obs.v not in s_q[s]:
            s_q[s].append(obs.v)
        if s in q_s[phi.v] and phi.v not in s_q[s]:
            s_q[s].append(phi.v)
    print (s_q)
    # initialize origin MDP
    mdp = MDP()

    # a = ['a', 'a-b', 'c', 'd', 'a-c', 'a-e', 'b-d', 'e']
    # b = mdp.bubble(a)

    mdp.set_S(states)
    mdp.set_WallCord(mdp.add_wall(states))
    mdp.set_P()
    mdp.set_L(s_q) # L: labeling function (L: S -> Q), e.g. self.L[(2, 3)] = 'g1'
    mdp.set_Exp(q_s) # L^-1: inverse of L (L: Q -> S), e.g. self.Exp['g1'] = (2, 3)
    mdp.set_Size(6, 8)
    # # print  "probabilities", len(mdp.P)

    dfa = DFA(0, [g1, g2, obs, g3, phi, whole])

    dfa.set_final(4)
    dfa.set_sink(5)

    sink = list(dfa.sink_states)[0]

    for i in range(sink + 1):
        dfa.add_transition(phi.display(), i, i)
        if i < sink:
            dfa.add_transition(obs.display(), i, sink)

    dfa.add_transition(whole.display(), sink, sink)

    dfa.add_transition(g1.display(), 0, 1)
    for i in range(1, sink + 1):
        dfa.add_transition(g1.display(), i, i)

    dfa.add_transition(g2.display(), 1, 2)
    dfa.add_transition(g2.display(), 3, 4)
    dfa.add_transition(g2.display(), 0, 0)
    dfa.add_transition(g2.display(), 2, 2)

    dfa.add_transition(g3.display(), 1, 3)
    dfa.add_transition(g3.display(), 2, 4)
    dfa.add_transition(g3.display(), 0, 0)
    dfa.add_transition(g3.display(), 3, 3)

    dfa.add_transition(g23.display(), 1, 4)
    dfa.add_transition(g23.display(), 0, 0)
    dfa.add_transition(g23.display(), 2, 4)
    dfa.add_transition(g23.display(), 3, 4)

    dfa.toDot("DFA")
    dfa.prune_eff_transition()
    dfa.g_unsafe = 'obs'

    curve = {}
    t0 = time.time()
    result = mdp.product(dfa, mdp)
    result.plotKey = False
    curve['action'] = result.SVI(0.001)
    t1 = time.time()

    print("action time for task 1", t1 - t0)
    V_action = result.goal_probability(result.Pi, result.P, ((3, 3), 0), 0.001)

    Policy = result.policy_evaluation(result.V)
    print('rate for action is:', result.evaluation(Policy, result.P, ((3, 5), 0), trial=trial_number))

    curve['optimal'], Policy_hard = result.Hardmax_SVI(0.001)
    print('rate for baseline is:', result.evaluation(Policy_hard, result.P, ((3, 5), 0), trial=trial_number))

    t1 = time.time()
    result.AOpt = mdp.option_generation(dfa)
    t2 = time.time()
    result.option_factory()
    t3 = time.time()
    print("total time for learning the options:", t3 - t1)

    curve['option'] = result.SVI_option(0.001)
    t4 = time.time()
    print("option time for task 1", t4 - t3)

    Policy = result.policy_evaluation(result.V)
    V_option = result.goal_probability(Policy, result.P, ((3, 3), 0), 0.001)
    print('rate for option is:', result.evaluation(Policy, result.P, ((3, 5), 0), trial=trial_number))

    t4 = time.time()
    curve['hybrid'] = result.SVI_option(0.001, hybrid = True)
    print("hybrid time for task 1", time.time() - t4)

    Policy = result.policy_evaluation(result.V)
    V_hybrid = result.goal_probability(Policy, result.P, ((3, 3), 0), 0.001)
    print('rate for hybrid is:', result.evaluation(Policy, result.P, ((3, 5), 0), trial=trial_number))
    result.plot_curve(curve, 'compare_result_normalized_reward')

    result.compute_norm(V_action, V_option, 2)
    result.compute_norm(V_action, V_hybrid, 2)
    result.compute_norm(V_action, V_option, np.infty)
    result.compute_norm(V_action, V_hybrid, np.infty)

    result.layer_plot()
    result.option_plot()


# ==================== task2
    g1_3 = Action('g1|g3')

    q_s[g1_3.v] = [(3, 1), (3, 2), (5, 8), (4, 8)]
    s_q = {}

    for s in S:
        s_q[s] = []
        if s in q_s[g1.v] and g1.v not in s_q[s]:
            s_q[s].append(g1.v)
        if s in q_s[g2.v] and g2.v not in s_q[s]:
            s_q[s].append(g2.v)
        if s in q_s[g3.v] and g3.v not in s_q[s]:
            s_q[s].append(g3.v)
        if s in q_s[g1_3.v] and g1_3.v not in s_q[s]:
            s_q[s] = [g1_3.v]
        if s in q_s[g23.v] and g23.v not in s_q[s]:
            s_q[s] = [g23.v]
        if s in q_s[obs.v] and obs.v not in s_q[s]:
            s_q[s].append(obs.v)
        if s in q_s[phi.v] and phi.v not in s_q[s]:
            s_q[s].append(phi.v)

    # for s in S:
    #     if s in q_s[g1_3.v] and g1_3.v not in s_q[s] and g23.v not in s_q[s]:
    #         s_q[s] = [g1_3.v]

    dfa2 = DRA(0, [g2, obs, g23, g1_3, phi, whole])

    dfa2.set_final(3)
    dfa2.set_sink(4)

    sink = list(dfa2.sink_states)[0]

    for i in range(sink + 1):
        dfa2.add_transition(phi.display(), i, i)
        if i < sink:
            dfa2.add_transition(obs.display(), i, sink)

    dfa2.add_transition(whole.display(), sink, sink)

    dfa2.add_transition(g1_3.display(), 0, 2)
    dfa2.add_transition(g1_3.display(), 1, 3)
    dfa2.add_transition(g1_3.display(), 2, 2)

    dfa2.add_transition(g2.display(), 0, 1)
    dfa2.add_transition(g2.display(), 1, 1)
    dfa2.add_transition(g2.display(), 2, 3)

    dfa2.add_transition(g23.display(), 0, 3)
    dfa2.add_transition(g23.display(), 1, 3)
    dfa2.add_transition(g23.display(), 2, 3)

    dfa2.toDot("DFA2")
    dfa2.prune_eff_transition()
    dfa2.g_unsafe = 'obs'
    print (dfa2.state_info)

    mdp2 = MDP()
    mdp2.set_S(states)
    mdp2.set_WallCord(mdp.add_wall(states))
    mdp2.set_P()
    mdp2.set_L(s_q)  # L: labeling function (L: S -> Q), e.g. self.L[(2, 3)] = 'g1'
    mdp2.set_Exp(q_s)  # L^-1: inverse of L (L: Q -> S), e.g. self.Exp['g1'] = (2, 3)
    mdp2.set_Size(6, 8)

    curve2 = {}
    # # # print  "probabilities", len(mdp.P)
    t0 = time.time()
    result2 = mdp2.product(dfa2, mdp2)
    result2.plotKey = False
    curve2['action'] = result2.SVI(0.001)
    t1 = time.time()

    V_action2 = result2.goal_probability(result2.Pi, result2.P, ((3, 3), 0), 0.001)
    Policy2 = result2.policy_evaluation(result2.V)

    print ("action time for task 2", t1 - t0)
    print('rate for action is:', result2.evaluation(Policy2, result2.P, ((3, 5), 0), trial=trial_number))

    curve2['optimal'], Policy_hard2 = result2.Hardmax_SVI(0.001)
    print('rate for baseline is:', result2.evaluation(Policy_hard2, result2.P, ((3, 5), 0), trial=trial_number))

    result2.AOpt = mdp2.option_generation(dfa2, result.AOpt)


    # print (result2.AOpt.keys())
    # print (dfa2.alphabet)
    keys = dcp(list(result2.AOpt.keys()))
    for key in keys:
        if key not in dfa2.alphabet:
            result2.AOpt.pop(key)
    # print(result2.AOpt.keys())


    result2.option_factory()
    # t3 = time.time()

    t2 = time.time()
    curve2['option'] = result2.SVI_option(0.001)
    t3 = time.time()

    print ("option time for task 2", t3 - t2)

    Policy2 = result2.policy_evaluation(result2.V)
    V_option2 = result2.goal_probability(Policy2, result2.P, ((3, 3), 0), 0.001)
    print('rate for option is:', result2.evaluation(Policy2, result2.P, ((3, 5), 0), trial=trial_number))

    t4 = time.time()
    curve2['hybrid'] = result2.SVI_option(0.001, hybrid=True)
    print("hybrid time for task 2", time.time()-t4)

    Policy2 = result2.policy_evaluation(result2.V)
    V_hybrid2 = result2.goal_probability(Policy2, result2.P, ((3, 3), 0), 0.001)
    print('rate for hybrid is:', result2.evaluation(Policy2, result2.P, ((3, 5), 0), trial=trial_number))
    result2.plot_curve(curve2, 'compare_result_normalized_reward2')

    result2.compute_norm(V_action2, V_option2, 2)
    result2.compute_norm(V_action2, V_hybrid2, 2)
    result2.compute_norm(V_action2, V_option2, np.infty)
    result2.compute_norm(V_action2, V_hybrid2, np.infty)
    

# task 3 ==============================
    g1_2 = Action('g1|g2')

    q_s[g1_2.v] = [(3, 1), (3, 2), (3, 8), (4, 8)]

    s_q = {}
    for s in S:
        s_q[s] = []
        if s in q_s[g1.v] and g1.v not in s_q[s]:
            s_q[s].append(g1.v)
        if s in q_s[g2.v] and g2.v not in s_q[s]:
            s_q[s].append(g2.v)
        if s in q_s[g3.v] and g3.v not in s_q[s]:
            s_q[s].append(g3.v)
        if s in q_s[g1_2.v] and g1_2.v not in s_q[s]:
            s_q[s] = [g1_2.v]
        if s in q_s[g23.v] and g23.v not in s_q[s]:
            s_q[s] = [g23.v]
        if s in q_s[obs.v] and obs.v not in s_q[s]:
            s_q[s].append(obs.v)
        if s in q_s[phi.v] and phi.v not in s_q[s]:
            s_q[s].append(phi.v)

    dfa3 = DRA2(0, [g1_2, obs, g23, g3, phi, whole])

    dfa3.set_final(2)
    dfa3.set_sink(3)

    sink = list(dfa3.sink_states)[0]

    for i in range(sink + 1):
        dfa3.add_transition(phi.display(), i, i)
        if i < sink:
            dfa3.add_transition(obs.display(), i, sink)

    dfa3.add_transition(whole.display(), sink, sink)

    dfa3.add_transition(g1_2.display(), 0, 1)
    dfa3.add_transition(g1_2.display(), 1, 1)

    dfa3.add_transition(g23.display(), 0, 2)
    dfa3.add_transition(g23.display(), 1, 2)

    dfa3.add_transition(g3.display(), 0, 0)
    dfa3.add_transition(g3.display(), 1, 1)

    dfa3.toDot("DFA3")
    dfa3.prune_eff_transition()
    dfa3.g_unsafe = 'obs'

    print (dfa2.state_transitions)
    print (dfa3.state_transitions)

    mdp3 = MDP()
    mdp3.set_S(states)
    mdp3.set_WallCord(mdp.add_wall(states))
    mdp3.set_P()
    mdp3.set_L(s_q)  # L: labeling function (L: S -> Q), e.g. self.L[(2, 3)] = 'g1'
    mdp3.set_Exp(q_s)  # L^-1: inverse of L (L: Q -> S), e.g. self.Exp['g1'] = (2, 3)
    mdp3.set_Size(6, 8)

    print(mdp3.L)

    curve3 = {}
    # # # print  "probabilities", len(mdp.P)
    t0 = time.time()
    result3 = mdp3.product(dfa3, mdp3)
    result3.plotKey = False
    curve3['action'] = result3.SVI(0.001)
    t1 = time.time()
    print("action time for task 3", t1 - t0)

    V_action3 = result3.goal_probability(result3.Pi, result3.P, ((3, 3), 0), 0.001)
    Policy3 = result3.policy_evaluation(result3.V)
    print('rate for action is:', result3.evaluation(Policy3, result3.P, ((3, 5), 0), trial=trial_number))
    # print  "action time", t1 - t0
    curve3['optimal'], Policy_hard3 = result3.Hardmax_SVI(0.001)
    print('rate for baseline is:', result3.evaluation(Policy_hard3, result3.P, ((3, 5), 0), trial=trial_number))

    result3.AOpt = mdp3.option_generation(dfa3, result.AOpt)
    # print (result2.AOpt.keys())
    # print (dfa2.alphabet)
    keys = dcp(list(result3.AOpt.keys()))
    for key in keys:
        if key not in dfa3.alphabet:
            result3.AOpt.pop(key)
    # print(result2.AOpt.keys())
    t2 = time.time()

    result3.option_factory()
    t3 = time.time()

    curve3['option'] = result3.SVI_option(0.001)
    print("option time for task 3", time.time() - t3)

    Policy3 = result3.policy_evaluation(result3.V)
    V_option3 = result3.goal_probability(Policy3, result3.P, ((3, 3), 0), 0.001)
    # print('rate for option is:', result.evaluation(Policy, result.P, ((3, 7), 0), trial=10000))
    print('rate for option is:', result3.evaluation(Policy3, result3.P, ((3, 5), 0), trial=trial_number))
    t4 = time.time()
    curve3['hybrid'] = result3.SVI_option(0.001, hybrid=True)
    print("hybrid time for task 3", time.time() - t4)

    Policy3 = result3.policy_evaluation(result3.V)
    V_hybrid3 = result3.goal_probability(Policy3, result3.P, ((3, 3), 0), 0.001)
    # print('rate for hybrid is:', result.evaluation(Policy, result.P, ((3, 7), 0), trial=10000))
    result3.plot_curve(curve3, 'compare_result_normalized_reward3')
    print('rate for hybrid is:', result3.evaluation(Policy3, result3.P, ((3, 5), 0), trial=trial_number))
    print (V_action3)
    print (V_option3)
    print (V_hybrid3)

    result3.compute_norm(V_action3, V_option3, 2)
    result3.compute_norm(V_action3, V_hybrid3, 2)
    result3.compute_norm(V_action3, V_option3, np.infty)
    result3.compute_norm(V_action3, V_hybrid3, np.infty)
