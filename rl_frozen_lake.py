import numpy as np
import gymnasium as gym
from frozen_lake_utils import plot_frozenlake_model_free_results
from enum import Enum
import random as random

    
class RLAlgorithm(Enum):
    SARSA = 'SARSA'
    Q_LEARNING = 'Q-Learning'
    EXPECTED_SARSA = 'Expected SARSA'


class ModelFreeAgent:
    def __init__(self, algorithm, alpha, eps, gamma, eps_decay,
                 num_train_episodes, num_test_episodes, max_episode_length):
        self.algorithm = algorithm
        self.alpha = alpha
        self.eps = eps
        self.gamma = gamma
        self.eps_decay = eps_decay
        self.num_train_episodes = num_train_episodes
        self.num_test_episodes = num_test_episodes
        self.max_episode_length = max_episode_length
        self.test_reward, self.train_reward = None, None


        random.seed(5)
        np.random.seed(5)

        self.env = gym.make('FrozenLake-v1', desc=None, map_name="4x4",
                            is_slippery=True, render_mode='human').unwrapped
        self.num_actions = self.env.action_space.n
        self.num_states = self.env.observation_space.n
    
        self.Q = np.zeros((self.num_states, self.num_actions))


    def set_render_mode(self, render: bool):
        self.env.render_mode = 'human' if render else None


    def policy(self, state, is_training):
        """
        Given a state, return an action according to an epsilon-greedy policy.
        :param state: The current state
        :param is_training: Whether we are training or testing the agent
        :return: An action (int)
        """

        # TODO: Implement an epsilon-greedy policy
        # - with probability self.eps return a random action
        # - otherwise find the action that maximizes self.Q
        # - when testing, do not use epsilon-greedy exploration but always return the greedy action

        if is_training == True:
            if random.uniform(0, 1) < self.eps:
                return random.randrange(0,self.num_actions) 
            else:
                return np.argmax(self.Q[state,],axis=0) 
        else:
                return np.argmax(self.Q[state,],axis=0)  

    def train_step(self, state, action, reward, next_state, next_action, done):
        """
        Update the Q-table `self.Q` according to the used algorithm (self.algorithm).

        :param state: State we were in *before* taking the action
        :param action: Action we have just taken
        :param reward: Immediate reward received after taking the action
        :param next_state: State we are in *after* taking the action
        :param next_action: Next action we *will* take (sampled from our policy)
        :param done: If True, the episode is over
        """

        if self.algorithm == RLAlgorithm.SARSA:
            # TODO: Implement the SARSA update.

            self.Q[state,action] += self.alpha * (reward + self.gamma * self.Q[next_state,next_action] - self.Q[state,action])
            
            # Q(s, a) = alpha * (reward + gamma * Q(s', a') - Q(s, a))
            #raise NotImplementedError(f'{self.algorithm.name} not implemented')

        elif self.algorithm == RLAlgorithm.Q_LEARNING:
            # TODO: Implement the Q-Learning update.
            max_val = np.max(self.Q[next_state,],axis=0)
            self.Q[state,action] += self.alpha * (reward + self.gamma * max_val - self.Q[state,action])

            # Q(s, a) = alpha * (reward + gamma * max_a' Q(s', a') - Q(s, a))
            # where the max is taken over all possible actions
            #raise NotImplementedError(f'{self.algorithm.name} not implemented')

        elif self.algorithm == RLAlgorithm.EXPECTED_SARSA:
            # TODO: Implement the Expected SARSA update.
            action_probabilities = np.ones(self.num_actions) * (self.eps / self.num_actions)
            action_probabilities[np.argmax(self.Q[next_state,])] += (1 - self.eps)  #completed policy probabilities
            expectation = sum(action_probabilities * self.Q[next_state,])
            self.Q[state,action] += self.alpha * (reward + self.gamma * expectation - self.Q[state,action]) 


            # Q(s, a) = alpha * (reward + gamma * E[Q(s', a')] - Q(s, a))
            # where the expectation E[Q(s', a')] is taken wrt. actions a' of the policy (s' is given by next_state)
            #raise NotImplementedError(f'{self.algorithm.name} not implemented')


    def run_episode(self, training, render=False):
        """
        Run an episode with the current policy `self.policy`
        and return the sum of rewards.
        We stop the episode if we reach a terminal state or
        if the episode length exceeds `self.max_episode_length`.
        :param training: True if we are training the agent, False if we are testing it
        :param render: True if we want to render the environment, False otherwise
        :return: sum of rewards of the episode
        """

        self.set_render_mode(render)

        episode_reward = 0
        state, _ = self.env.reset()
        action = self.policy(state, training)
        for t in range(self.max_episode_length):
            next_state, reward, done, _, _ = self.env.step(action)
            episode_reward += reward
            next_action = self.policy(next_state, training)
            if training:
                self.train_step(state, action, reward, next_state, next_action, done)
            state, action = next_state, next_action
            if done:
                break

        return episode_reward


    def train(self):
        """
        Train the agent for self.max_train_iterations episodes.
        After each episode, we decay the exploration rate self.eps using self.eps_decay.
        After training, self.train_reward contains the reward-sum of each episode.
        """

        self.train_reward = []
        for _ in range(self.num_train_episodes):
            self.train_reward.append(self.run_episode(training=True))
            self.eps *= self.eps_decay


    def test(self, render=False):
        """
        Test the agent for `num_episodes` episodes.
        After testing, self.test_reward contains the reward-sum of each episode.
        :param num_episodes: The number of episodes to test the agent
        :param render: True if we want to render the environment, False otherwise
        """

        self.test_reward = []
        for _ in range(self.num_test_episodes):
            self.test_reward.append(self.run_episode(training=False, render=render))


def train_test_agent(algorithm, gamma, alpha, eps, eps_decay,
                     num_train_episodes=10_000, num_test_episodes=5000,
                     max_episode_length=200, render_on_test=False, savefig=True):
    """
    Trains and tests an agent with the given parameters.

    :param algorithm: The RLAgorithm to use (SARSA, Q_LEARNING, EXPECTED_SARSA)
    :param gamma: Discount rate
    :param alpha: "Learning rate"
    :param eps: Initial exploration rate
    :param eps_decay: Exploration rate decay
    :param num_train_episodes: Number of episodes to train the agent
    :param num_test_episodes: Number of episodes to test the agent
    :param max_episode_length: Episodes are terminated after this many steps
    :param render_on_test: If true, the environment is rendered during testing
    :param savefig: If True, saves a plot of the result figure in the current directory. Otherwise, we show the plot.
    :return:
    """

    agent = ModelFreeAgent(algorithm=algorithm, alpha=alpha, eps=eps,
                           gamma=gamma, eps_decay=eps_decay,
                           num_train_episodes=num_train_episodes,
                           num_test_episodes=num_test_episodes,
                           max_episode_length=max_episode_length)
    agent.train()
    agent.test(render=render_on_test)
    plot_frozenlake_model_free_results(agent, gamma, savefig=savefig)
    print(f'{algorithm.value} | Mean Training Reward: {np.mean(agent.train_reward)} |',
          f'Mean Test Reward: {np.mean(agent.test_reward)} | {gamma=}, {alpha=}, {eps=}, {eps_decay=}')


if __name__ == '__main__':
    eps = 1
    random.seed(5)
    for gamma in [0.95, 1.0]:
        for algo in [ RLAlgorithm.SARSA, RLAlgorithm.Q_LEARNING, RLAlgorithm.EXPECTED_SARSA]:

            # TODO: For each algorithm independently, set good values for alpha and eps_decay
            
            alpha, eps_decay = None, None

            if algo == RLAlgorithm.SARSA:
                if gamma == 0.95:
                    alpha = 0.4
                    eps_decay = 0.998
                else: 
                    alpha = 0.15
                    eps_decay = 0.998

            elif algo == RLAlgorithm.Q_LEARNING:
                 if gamma == 0.95:
                        alpha = 0.4
                        eps_decay = 0.997
                 else:
                        alpha = 0.07
                        eps_decay = 0.999  

            elif algo == RLAlgorithm.EXPECTED_SARSA:
                 if gamma == 0.95:
                     alpha = 0.35
                     eps_decay = 0.998
                 else:
                     alpha = 0.15
                     eps_decay = 0.998  


            train_test_agent(algorithm=algo, gamma=gamma, alpha=alpha, eps=eps, eps_decay=eps_decay,
                             num_train_episodes=10_000, num_test_episodes=5_000,
                             max_episode_length=200, savefig=False)
