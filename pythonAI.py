import random, pygame, sys, pygame.mixer
from pygame.locals import *
from enum import Enum
import pickle
from brain import Brain
from math import sqrt
import matplotlib.pyplot as plt

pygame.init()

###############################################################################

apple_image = pygame.image.load('apple.png')
apple_rect = apple_image.get_rect()

speed = 10
width = 300
height = 300
field = 20
fields_x = width // field
fields_y = height // field

BLACK = (0, 0, 0)
BG = (124, 163, 82)
RED = (164, 4, 0)
TMP = (220,220,220)

head = 0
hi_score = 0

clock = pygame.time.Clock()
bg = pygame.display.set_mode((width, height))
font_title = pygame.font.Font("zig.ttf", 60) 
font_text = pygame.font.Font("zig.ttf", 20) 
font_score = pygame.font.Font("zig.ttf", 18)  

apple = []
head_var = []
last_head_var = []
sensor1 = []
sensor2 = []
sensor3 = []
sensor4 = []
signal1 = 0
signal2 = 0
signal3 = 0
signal4 = 0
food1 = 0
food2 = 0
food3 = 0
food4 = 0
is_closer = 0

brain = Brain(9, 20, 3, 4, 0.9)
action = 0
reward = 0
score_var = []
distance_var = 0

class Direction(Enum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3

###############################################################################

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

###############################################################################

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

###############################################################################

def draw_python(python_xy, direction, sensor1, sensor2, sensor3, sensor4):
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

    sensora = pygame.Rect(sensor1[0] * field, sensor1[1] * field, 20, 20)
    pygame.draw.rect(bg, TMP, sensora)
    sensorb = pygame.Rect(sensor2[0] * field, sensor2[1] * field, 20, 20)
    pygame.draw.rect(bg, TMP, sensorb)
    sensorc = pygame.Rect(sensor3[0] * field, sensor3[1] * field, 20, 20)
    pygame.draw.rect(bg, TMP, sensorc)
    sensord = pygame.Rect(sensor4[0] * field, sensor4[1] * field, 20, 20)
    pygame.draw.rect(bg, TMP, sensord)

###############################################################################

def game():

    global head_var
    global apple_var
    global distance_var
    global sensor1
    global sensor2
    global sensor3
    global sensor4
    global signal1
    global signal2
    global signal3
    global signal4
    global food1
    global food2
    global food3
    global food4
    global brain
    global reward
    global is_closer

    start_x = random.randint(5, fields_x//2)
    start_y = random.randint(5, fields_y - 6)
    sensor1 = [start_x+1, start_y]
    sensor4 = [start_x+2, start_y]
    sensor2 = [start_x, start_y+1]
    sensor3 = [start_x, start_y-1]
    python_xy = [{'x': start_x,     'y': start_y},
                  {'x': start_x - 1, 'y': start_y},
                  {'x': start_x - 2, 'y': start_y}]
    direction = Direction.RIGHT

    last_head_var = [python_xy[head]['x'], python_xy[head]['y']]
    head_var = [python_xy[head]['x'], python_xy[head]['y']]
    apple = apple_rand()
    distance_var = distance(head_var, apple_var)
     
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



            ###############################################################################3

        print("input =", reward, signal1, signal2, signal3, signal4, food1, food2, food3, food4)

        brain_input = [signal1, signal2, signal3, signal4, food1, food2, food3, food4, is_closer]
        action = brain.update(reward, brain_input)
        score_var.append(brain.score())

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
                    direction = Direction.LEFT

                elif direction == Direction.RIGHT:
                    direction = Direction.UP

                elif direction == Direction.DOWN:
                    direction = Direction.RIGHT

                elif direction == Direction.LEFT:
                    direction = Direction.DOWN



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

        if direction == Direction.UP:
            sensor1 = [head_var[0], head_var[1]-1]
            sensor2 = [head_var[0]-1, head_var[1]]
            sensor3 = [head_var[0]+1, head_var[1]] 
            sensor4 = [head_var[0], head_var[1]-2]

        elif direction == Direction.RIGHT:
            sensor1 = [head_var[0]+1, head_var[1]]
            sensor4 = [head_var[0]+2, head_var[1]]
            sensor2 = [head_var[0], head_var[1]+1]
            sensor3 = [head_var[0], head_var[1]-1] 

        elif direction == Direction.DOWN:
            sensor1 = [head_var[0], head_var[1]+1]
            sensor4 = [head_var[0], head_var[1]+2]
            sensor2 = [head_var[0]+1, head_var[1]]
            sensor3 = [head_var[0]-1, head_var[1]] 

        elif direction == Direction.LEFT:
            sensor1 = [head_var[0]-1, head_var[1]]
            sensor2 = [head_var[0], head_var[1]-1]
            sensor3 = [head_var[0], head_var[1]+1] 
            sensor4 = [head_var[0]-2, head_var[1]]


        signal1 = 1
        signal2 = 1
        signal3 = 1
        signal4 = 1
        food1 = 0
        food2 = 0
        food3 = 0
        food4 = 0

        if sensor1[0] == apple['x'] and sensor1[1] == apple['y']:
            food1 = 1

        elif sensor1[0] <= 1 or sensor1[0] >= fields_x-2 or sensor1[1] <= 1 or sensor1[1] >= fields_y-2:
            signal1 = 0

        for python_body in python_xy[1:]:
            if python_body['x'] == sensor1[0] and python_body['y'] == sensor1[1]:
                signal1 = 0


        if sensor2[0] == apple['x'] and sensor2[1] == apple['y']:
            food2 = 1

        elif sensor2[0] <= 1 or sensor2[0] >= fields_x-2 or sensor2[1] <= 1 or sensor2[1] >= fields_y-2:
            signal2 = 0

        for python_body in python_xy[1:]:
            if python_body['x'] == sensor2[0] and python_body['y'] == sensor2[1]:
                signal2 = 0

        if sensor3[0] == apple['x'] and sensor3[1] == apple['y']:
            food3 = 1

        elif sensor3[0] <= 1 or sensor3[0] >= fields_x-2 or sensor3[1] <= 1 or sensor3[1] >= fields_y-2:
            signal3 = 0

        for python_body in python_xy[1:]:
            if python_body['x'] == sensor3[0] and python_body['y'] == sensor3[1]:
                signal3 = 0
            
        if sensor4[0] == apple['x'] and sensor4[1] == apple['y']:
            food4 = 1

        elif sensor4[0] <= 1 or sensor4[0] >= fields_x-2 or sensor4[1] <= 1 or sensor4[1] >= fields_y-2:
            signal4 = 0

        for python_body in python_xy[1:]:
            if python_body['x'] == sensor4[0] and python_body['y'] == sensor4[1]:
                signal4 = 0

##########################################################################################################

        print(signal1, signal2, signal3, signal4, food1, food2, food3, food4)
        #print(signal1)
        #print(sensor2)
        #print(sensor3)

        if python_xy[head]['x'] == 1 or python_xy[head]['x'] == fields_x-2 or python_xy[head]['y'] == 1 or python_xy[head]['y'] == fields_y-2:
            reward = -3.5
            brain_input = [signal1, signal2, signal3, signal4, food1, food2, food3, food4, is_closer]
            action = brain.update(reward, brain_input)
            score_var.append(brain.score())
            print(head_var)
            print(apple_var)
            print(distance_var)
            print("r = ", reward)
            print("----------")  
            gameover(len(python_xy) - 3)
            return
        
        for python_body in python_xy[1:]:
            if python_body['x'] == python_xy[head]['x'] and python_body['y'] == python_xy[head]['y']:
                reward = -3.5
                brain_input = [signal1, signal2, signal3, signal4, food1, food2, food3, food4, is_closer]
                action = brain.update(reward, brain_input)
                score_var.append(brain.score())
                print(head_var)
                print(apple_var)
                print(distance_var)
                print("r = ", reward)
                print("----------")
                gameover(len(python_xy) - 3)
                return

        print(head_var)
        print(apple_var)
        print(distance(head_var, apple_var))      

        if python_xy[head]['x'] == apple['x'] and python_xy[head]['y'] == apple['y']:
            #reward = 1
            apple = apple_rand()

        else:
            if(distance(head_var, apple_var) < distance_var):
                is_closer = 1
                reward = 2

            elif distance(head_var, apple_var) >= distance_var:
                is_closer = 0
                reward = -2
            del python_xy[-1]

        distance_var = distance(head_var, apple_var)
        print("r = ", reward)
        print("----------") 

        python_xy.insert(0, new_head)
        bg.fill(BG)
        layout()
        draw_python(python_xy, direction, sensor1, sensor2, sensor3, sensor4)
        draw_apple(apple)
        score(len(python_xy) - 3)
        text_display()
        pygame.display.update()
        clock.tick(speed)
        
###############################################################################

import_hiscore()
while True:
    game()