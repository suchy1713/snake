import numpy as np
import random
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.autograd as autograd
from torch.autograd import Variable

######################################################

class Network(nn.Module):
    
    def __init__(self, input_size, hl_size, nb_action):
        super(Network, self).__init__()
        self.input_size = input_size
        self.nb_action = nb_action
        self.hl_size = hl_size
        
        self.fc1 = nn.Linear(input_size, hl_size)
        self.fc2 = nn.Linear(hl_size, nb_action)
        
        
    def forward(self, state):
        x = F.relu(self.fc1(state))
        q_values = self.fc2(x)
        
        return q_values

######################################################
        
class ReplayMemory(object):
    
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        

    def push(self, event):
        self.memory.append(event)
        
        if len(self.memory) > self.capacity:
            del self.memory[0]
            
    
    def sample(self, batch_size):
        samples = zip(*random.sample(self.memory, batch_size))
        return map(lambda x: Variable(torch.cat(x, 0)), samples)

######################################################

class Brain():

    def __init__(self, input_size, hl_size, nb_action, temperature, gamma, learning_rate, memory_capacity, batch_size):
        self.gamma = gamma
        self.model = Network(input_size, hl_size, nb_action)
        self.memory = ReplayMemory(memory_capacity)
        self.reward_window = []
        self.optimizer = optim.Adam(self.model.parameters(), lr = learning_rate)
        self.last_state = torch.Tensor(input_size).unsqueeze(0)
        self.last_reward = 0
        self.last_action = 0
        self.temperature = temperature
        self.batch_size = batch_size


    def select_action(self, state):
        probs = F.softmax(self.model.forward(Variable(state, volatile = True))*self.temperature)
        action = probs.multinomial()
        return action.data[0,0]


    def learn(self, batch_state, batch_next_state, batch_reward, batch_action):
        outputs = self.model.forward(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)
        next_outputs = self.model.forward(batch_next_state).detach().max(1)[0]
        target = self.gamma * next_outputs + batch_reward
        td_loss = F.smooth_l1_loss(outputs, target)
        self.optimizer.zero_grad()
        td_loss.backward(retain_variables = True)
        self.optimizer.step()


    def update(self, reward, new_signal):
        new_state = torch.Tensor(new_signal).float().unsqueeze(0)
        self.memory.push((self.last_state, new_state, torch.LongTensor([int(self.last_action)]), torch.Tensor([self.last_reward])))
        action = self.select_action(new_state)

        if len(self.memory.memory) > self.batch_size:
            batch_state, batch_next_state, batch_action, batch_reward = self.memory.sample(self.batch_size)
            self.learn(batch_state, batch_next_state, batch_reward, batch_action)

        self.last_action = action
        self.last_state = new_state
        self.last_reward = reward
        self.reward_window.append(reward)

        if len(self.reward_window) > 1000:
            del self.reward_window[0]

        return action

    
    def score(self):
        return sum(self.reward_window)/(len(self.reward_window)+1)


    def save(self):
        torch.save({'state_dict': self.model.state_dict(),
                    'optimizer': self.optimizer.state_dict()}, 'last_brain.pth')

    
    def load(self):
        if os.path.isfile('last_brain.pth'):
            print('==> Loading THE BRAIN...')
            checkpoint = torch.load('last_brain.pth')
            self.model.load_state_dict(checkpoint['state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            print('Done!')

        else:
            print('No brain found') 