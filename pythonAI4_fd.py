import random, pygame, sys, pygame.mixer
from pygame.locals import *
from enum import Enum
import pickle
from brain import Brain
from math import sqrt
import matplotlib.pyplot as plt

pygame.init()

###############################################################################

#game conditions
speed = 10
width = 560
height = 360
field = 20
fields_x = width // field
fields_y = height // field

#pygame stuff
apple_image = pygame.image.load('apple.png')
apple_rect = apple_image.get_rect()
clock = pygame.time.Clock()
bg = pygame.display.set_mode((width, height))
font_title = pygame.font.Font("zig.ttf", 60) 
font_text = pygame.font.Font("zig.ttf", 20) 
font_score = pygame.font.Font("zig.ttf", 18)  
BLACK = (0, 0, 0)
BG = (124, 163, 82)
RED = (164, 4, 0)
TMP = (220,220,220)
hi_score = 0

class Direction(Enum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3

direction = Direction.RIGHT

#used as python_xy index
head = 0

#obstacle_distance and is_food index
left = 0
up = 1
right = 2

#ai - const
apple = []
head_var = []
sensor1 = []
sensor2 = []
sensor3 = []
obstacle_distance = [0, 0, 0]
is_food = [0, 0, 0]
is_closer = 0
iterator = 1
action = 0
reward = 0
score_var = []
distance_var = 0

# ai - modifiable
reward_apple = 1
reward_death = -1.2
reward_closer = 0.5
reward_further = -0.8
gamma = 0.9
learning_rate = 0.001
temperature = 10
hidden_layer_size = 20
memory_capacity = 100000
batch_size = 100

#brain init
brain = Brain(7, hidden_layer_size, 3, temperature, gamma, learning_rate, memory_capacity, batch_size)

###############################################################################

#game part functions
def distance(a, b):
    return sqrt((b[1] - a[1])**2 + (b[0] - a[0])**2)

def exit_f():
    pygame.quit()
    sys.exit()

def is_key_pressed(): 
    if len(pygame.event.get(QUIT)) > 0:
        exit_f()
 
    klawisz_event = pygame.event.get(KEYUP)
    if len(klawisz_event) == 0:
        return None
    if klawisz_event[0].key == K_ESCAPE:
        exit_f()
    return klawisz_event[0].key

def pause():
    text = font_text.render('PAUSE', True, RED)
    text_rect = text.get_rect()
    text_rect.center = (width/2, height/2)
    bg.blit(text, text_rect)

def layout():
    pygame.draw.line(bg, BLACK, (field, field), (field, height-field), 2)
    pygame.draw.line(bg, BLACK, (field, field), (width-field, field), 2)
    pygame.draw.line(bg, BLACK, (width-field, field), (width-field, height-field), 2)
    pygame.draw.line(bg, BLACK, (field, height-field), (width-field, height-field), 2)

def import_hiscore():
    global hi_score
    
    try:
        with open("score.dat", "rb") as file:
            hi_score = pickle.load(file)
            
    except:
        hi_score = 0

def score(score):        
    text = font_text.render(str(score), True, BLACK)
    text_rect = text.get_rect()
    text_rect.center = (width/2, field-9)
    bg.blit(text, text_rect)

def text_display():        
    text = font_score.render("[S]AVE [L]OAD [P]LOT P[A]USE [ESC]APE", True, BLACK)
    text_rect = text.get_rect()
    text_rect.center = (width/2, height-9)
    bg.blit(text, text_rect)   
    
def gameover(score):

    global hi_score

    text = font_title.render('GAME OVER', True, RED)
    text_rect = text.get_rect()
    text_rect.center = (width / 2, height / 2)
    bg.blit(text, text_rect)  
    
    if score > hi_score:
        text2 = font_score.render('NEW HIGH SCORE', True, RED)
        text2_rect = text2.get_rect()
        text2_rect.center = (width/2, height/2 + 2 * field)
        bg.blit(text2, text2_rect)
        
        hi_score = score
        
        with open("score.dat", "wb") as file:
            pickle.dump(hi_score, file)
    
    pygame.display.update()
    pygame.time.wait(500)

def apple_rand():
    global apple_var
    x = random.randint(2, fields_x - 3)
    y = random.randint(2, fields_y - 3)
    apple_var = [x, y]
    return {'x': x, 'y': y}

def draw_apple(coord):
    x = coord['x'] * field
    y = coord['y'] * field
    apple_rect.center = (x + field/2, y + field/2)
    bg.blit(apple_image, apple_rect)

def draw_python(python_xy, direction):
    for coord in python_xy:
        eye_size = 4
        offset = 2
        x = coord['x'] * field
        y = coord['y'] * field
        python_body = pygame.Rect(x, y, field - 1, field - 1)
        pygame.draw.rect(bg, BLACK, python_body)
        
        python_head = pygame.Rect(python_xy[head]['x']*field, python_xy[head]['y']*field, field - 1, field - 1)
        
        if direction == Direction.UP or direction == Direction.LEFT:
            eye_x = offset
            eye_y = offset
            
        elif direction == Direction.DOWN:
            eye_x = offset
            eye_y = field - offset - eye_size - 1
            
        elif direction == Direction.RIGHT:
            eye_x = field - offset - eye_size - 1
            eye_y = offset
        
        python_eye = pygame.Rect(python_xy[head]['x']*field + eye_x, python_xy[head]['y']*field + eye_y, eye_size, eye_size)
        pygame.draw.rect(bg, BLACK, python_head)
        pygame.draw.rect(bg, RED, python_eye)

###############################################################################

#ai part functions
def print_state():
    global iterator, head_var, apple_var, distance_var, reward, obstacle_distance, is_food, is_closer, action

    print("STATE:", iterator)
    print("head = ", head_var)
    print("apple = ", apple_var)
    print("distance = ", distance_var)
    print("reward = ", reward)
    print("obstacle_distance = ", obstacle_distance[left], obstacle_distance[up], obstacle_distance[right])
    print("is_food = ", is_food[left], is_food[up], is_food[right])
    print("is_closer = ", is_closer)
    print("action = ", action)
    print("----------")   

    iterator += 1


def set_sensors(sensor_1, sensor_2, sensor_3):
    global sensor1, sensor2, sensor3
    sensor1 = sensor_1
    sensor2 = sensor_2
    sensor3 = sensor_3


def learn():
    global obstacle_distance, is_food, is_closer, reward, action, score_var, brain
    brain_input = [obstacle_distance[left], obstacle_distance[up], obstacle_distance[right], is_food[left], is_food[up], is_food[right], is_closer]
    action = brain.update(reward, brain_input)
    score_var.append(brain.score())

def take_action():
    global action, direction
    if action != 0: #dont go forward
        if action == 1: #turn left
            if direction == Direction.UP:
                direction = Direction.LEFT

            elif direction == Direction.RIGHT:
                direction = Direction.UP

            elif direction == Direction.DOWN:
                direction = Direction.RIGHT

            elif direction == Direction.LEFT:
                direction = Direction.DOWN

        elif action == 2: #turn right
            if direction == Direction.UP:
                direction = Direction.RIGHT

            elif direction == Direction.RIGHT:
                direction = Direction.DOWN

            elif direction == Direction.DOWN:
                direction = Direction.LEFT

            elif direction == Direction.LEFT:
                direction = Direction.UP
    


###############################################################################
def game():

    global head_var, apple_var, distance_var, sensor1, sensor2, sensor3, is_food, brain, reward, is_closer, iterator, action, direction, obstacle_distance

    start_x = random.randint(5, fields_x//2)
    start_y = random.randint(5, fields_y - 6)
    
    set_sensors([start_x+1, start_y], [start_x, start_y+1], [start_x, start_y-1])
    python_xy = [{'x': start_x,     'y': start_y},
                  {'x': start_x - 1, 'y': start_y},
                  {'x': start_x - 2, 'y': start_y}]

    head_var = [python_xy[head]['x'], python_xy[head]['y']]
    apple = apple_rand()
    distance_var = distance(head_var, apple_var)
    
    obstacle_distance = [0, 0, 0]
    is_food = [0, 0, 0]
    direction = Direction.RIGHT

    while True:        
        for event in pygame.event.get():
            if event.type == QUIT:
                exit_f()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    exit_f()

                if event.key == K_p:
                    plt.plot(score_var)
                    plt.show()
                
                if event.key == K_s:
                    brain.save()

                if event.key == K_l:
                    brain.load()

                if event.key == K_a:
                    pause()
                    while 1: 
                        pause()
                        pygame.display.update()
                        event = pygame.event.wait()
                        if event.type == QUIT:
                            exit_f()
                        if event.type == KEYDOWN:
                            if event.key == K_ESCAPE:
                                exit_f()
                                
                            if event.key == K_a:
                                break;
        
###############################################################################

        print_state()

        learn()

        take_action()

        if direction == Direction.UP:
            new_head = {'x': python_xy[head]['x'], 'y': python_xy[head]['y'] - 1}
            head_var = [python_xy[head]['x'], python_xy[head]['y'] - 1]
            
        elif direction == Direction.DOWN:
            new_head = {'x': python_xy[head]['x'], 'y': python_xy[head]['y'] + 1}
            head_var = [python_xy[head]['x'], python_xy[head]['y'] + 1]
            
        elif direction == Direction.LEFT:
            new_head = {'x': python_xy[head]['x'] - 1, 'y': python_xy[head]['y']}
            head_var = [python_xy[head]['x'] - 1, python_xy[head]['y']]
            
        elif direction == Direction.RIGHT:
            new_head = {'x': python_xy[head]['x'] + 1, 'y': python_xy[head]['y']}
            head_var = [python_xy[head]['x'] + 1, python_xy[head]['y']]
###############################################################################

        if python_xy[head]['x'] == 1 or python_xy[head]['x'] == fields_x-2 or python_xy[head]['y'] == 1 or python_xy[head]['y'] == fields_y-2:
            reward = reward_death
            obstacle_distance = [0, 0, 0]
            print_state()
            learn()
            gameover(len(python_xy) - 3)
            reward = 0
            return
        
        for python_body in python_xy[1:]:
            if python_body['x'] == python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                reward = reward_death
                obstacle_distance = [0, 0, 0]
                print_state()
                learn()
                gameover(len(python_xy) - 3)
                reward = 0
                return

        if direction == Direction.UP:
            set_sensors([head_var[0], head_var[1]-1], [head_var[0]-1, head_var[1]], [head_var[0]+1, head_var[1]])

        elif direction == Direction.RIGHT:
            set_sensors([head_var[0]+1, head_var[1]], [head_var[0], head_var[1]+1], [head_var[0], head_var[1]-1] )

        elif direction == Direction.DOWN:
            set_sensors([head_var[0], head_var[1]+1], [head_var[0]+1, head_var[1]], [head_var[0]-1, head_var[1]] )

        elif direction == Direction.LEFT:
            set_sensors([head_var[0]-1, head_var[1]], [head_var[0], head_var[1]-1], [head_var[0], head_var[1]+1])


        is_food = [1, 1, 1]

        if direction == Direction.UP:
            if head_var[0] == apple_var[0] and head_var[1] > apple_var[1]:
                is_food[up] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] == apple_var[1] and head_var[0] > apple_var[0]:
                is_food[left] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] == apple_var[1] and head_var[0] < apple_var[0]:
                is_food[right] = distance(apple_var, head_var)/max(fields_x, fields_y)

        elif direction == Direction.RIGHT:
            if head_var[0] < apple_var[0] and head_var[1] == apple_var[1]:
                is_food[up] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] > apple_var[1] and head_var[0] == apple_var[0]:
                is_food[left] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] < apple_var[1] and head_var[0] == apple_var[0]:
                is_food[right] = distance(apple_var, head_var)/max(fields_x, fields_y)

        elif direction == Direction.DOWN:
            if head_var[0] == apple_var[0] and head_var[1] < apple_var[1]:
                is_food[up] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] == apple_var[1] and head_var[0] < apple_var[0]:
                is_food[left] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] == apple_var[1] and head_var[0] > apple_var[0]:
                is_food[right] = distance(apple_var, head_var)/max(fields_x, fields_y)

        elif direction == Direction.LEFT:
            if head_var[0] > apple_var[0] and head_var[1] == apple_var[1]:
                is_food[up] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] < apple_var[1] and head_var[0] == apple_var[0]:
                is_food[left] = distance(apple_var, head_var)/max(fields_x, fields_y)

            elif head_var[1] > apple_var[1] and head_var[0] == apple_var[0]:
                is_food[right] = distance(apple_var, head_var)/max(fields_x, fields_y)



        if direction == Direction.UP:
            obstacle_distance[left] = distance(head_var, [1, head_var[1]])
            obstacle_distance[right] = distance(head_var, [fields_x-2, head_var[1]])
            obstacle_distance[up] = distance(head_var, [head_var[0], 1])
            for python_body in python_xy[1:]:
                if python_body['x'] < python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[left] = distance(head_var, tmp)
                
                if python_body['x'] > python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[right] = distance(head_var, tmp)

                if python_body['x'] == python_xy[head]['x'] and python_body['y'] < python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[up] = distance(head_var, tmp)
                    

        elif direction == Direction.RIGHT:
            obstacle_distance[left] = distance(head_var, [head_var[0], 1])
            obstacle_distance[right] = distance(head_var, [head_var[0], fields_y-2])
            obstacle_distance[up] = distance(head_var, [fields_x-2, head_var[1]])
            for python_body in python_xy[1:]:
                if python_body['x'] == python_xy[head]['x'] and python_body['y'] < python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[left] = distance(head_var, tmp)
                
                if python_body['x'] == python_xy[head]['x'] and python_body['y'] > python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[right] = distance(head_var, tmp)

                if python_body['x'] > python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[up] = distance(head_var, tmp)

        elif direction == Direction.DOWN:
            obstacle_distance[left] = distance(head_var, [fields_x-2, head_var[1]])
            obstacle_distance[right] = distance(head_var, [1, head_var[1]])
            obstacle_distance[up] = distance(head_var, [head_var[0], fields_y-2])
            for python_body in python_xy[1:]:
                if python_body['x'] > python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[left] = distance(head_var, tmp)
                
                if python_body['x'] < python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[right] = distance(head_var, tmp)

                if python_body['x'] == python_xy[head]['x'] and python_body['y'] > python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[up] = distance(head_var, tmp)

        elif direction == Direction.LEFT:
            obstacle_distance[left] = distance(head_var, [head_var[0], fields_y-2])
            obstacle_distance[right] = distance(head_var, [head_var[0], 1])
            obstacle_distance[up] = distance(head_var, [1, head_var[1]])
            for python_body in python_xy[1:]:
                if python_body['x'] == python_xy[head]['x'] and python_body['y'] > python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[left] = distance(head_var, tmp)
                
                if python_body['x'] == python_xy[head]['x'] and python_body['y'] < python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[right] = distance(head_var, tmp)

                if python_body['x'] < python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                    tmp = [python_body['x'], python_body['y']]
                    obstacle_distance[up] = distance(head_var, tmp)

        obstacle_distance[up] /= max(fields_x, fields_y)
        obstacle_distance[left] /= max(fields_x, fields_y)
        obstacle_distance[right] /= max(fields_x, fields_y)
            

##########################################################################################################
     
        if python_xy[head]['x'] == apple['x'] and python_xy[head]['y'] == apple['y']:
            reward = reward_apple
            distance_var = 0
            is_food = [0, 0, 0]
            apple = apple_rand()

        else:
            if distance(head_var, apple_var) < distance_var:
                is_closer = 1
                reward = reward_closer

            else:
                is_closer = 0
                reward = reward_further

            del python_xy[-1]

        distance_var = distance(head_var, apple_var)

        python_xy.insert(0, new_head)
        bg.fill(BG)
        layout()
        draw_python(python_xy, direction)
        draw_apple(apple)
        score(len(python_xy) - 3)
        text_display()
        pygame.display.update()
        clock.tick(speed)
        
###############################################################################

import_hiscore()
while True:
    game()
