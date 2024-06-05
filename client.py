import socket 
import threading
import time
import pygame, sys
from pygame.locals import *

RED = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE = (  0,   0, 255)
YELLOW = (255,255,0)
BLACK = (0,0,0)
WHITE = (255,255,255)
GRAY = (120,120,120)
LIGHT_GRAY = (200,200,200)

XUB=2350
XLB=50
YUB=550
YLB=50

game_over = -1

pygame.init()
DISPLAY = pygame.display.set_mode((800,800))
pygame.display.set_caption("network death run")

gameoverIMG = list()


gameoverIMG.append(pygame.image.load('img/murder_won_red.png'))
gameoverIMG.append(pygame.image.load('img/runner_won_blue.png'))

boom_IMG = [pygame.image.load(f'img/boom/{str(i).zfill(2)}.png') for i in range(27) ]
boom_IMG = [pygame.transform.scale(img,(200,200)) for img in boom_IMG]

player_IMG = [pygame.image.load(f'img/player_frame/player_frame_0{i}.png') for i in range(1,7) ]
player_IMG = [pygame.transform.scale(img,(100,100)) for img in player_IMG]
player_IMG_o = [img.copy() for img in player_IMG]
player_IMG_f = [img.copy() for img in player_IMG]
player_IMG_f = [ pygame.transform.flip(img, True, False) for img in player_IMG_f]

player_IMG= list()
player_IMG.append(player_IMG_o)
player_IMG.append(player_IMG_f)

FPS = 30 # 設定每秒幾禎
fpsClock = pygame.time.Clock() # Clock

serverAddr, serverPort = "127.0.0.1" ,1234
server_sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Broadcast_sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Broadcast_Port = 5678

screen_dx=0

player_color = [(122,0,122),(195, 255, 147),(255, 219, 92),(255, 175, 97),(255, 112, 171)]

player_state = [0 for i in range(5)]

player_frame = [0 for i in range(5)]
player_dir   = [0 for i in range(5)]

def player_next_frame(x):
    if x == 5:
        return 0
    return x+1

trap = [ [0 for j in range(3)] for i in range(10)]
trap_opened =[0 for i in range(10)]

trap_frame = [ 0 for i in range(10)]


def update_screen():
    DISPLAY.fill((40,40,60))
    
    global screen_dx
    pygame.draw.rect(DISPLAY, LIGHT_GRAY, (0, 610,800,200))
    for i in range(1,12):
        pygame.draw.line(DISPLAY, WHITE, (200*i-screen_dx, 610), (200*i-screen_dx, 800), 10)
    pygame.draw.line(DISPLAY, BLUE, (0, 610), (800, 610), 20)
    pygame.draw.line(DISPLAY, YELLOW, (2300-screen_dx, 0), (2300-screen_dx, 600), 20)
    if player_ID == 0:
        for i in range(10):
            if not trap_opened[i]:
                pygame.draw.rect(DISPLAY, GRAY, (200*(i+1)+85-screen_dx, 605,30,10))
    for i in range(10):
        for j in range(3):
            if trap[i][j] == 0:
                pygame.draw.rect(DISPLAY, GREEN, (200*(i+1)+20-screen_dx, 200*j+20,160,160))
            elif trap[i][j] == 1:
                pygame.draw.rect(DISPLAY, YELLOW, (200*(i+1)+20-screen_dx, 200*j+20,160,160))
            else :
                pygame.draw.rect(DISPLAY, RED, (200*(i+1)+20-screen_dx, 200*j+20,160,160))
                DISPLAY.blit(boom_IMG[trap_frame[i]], (200*(i+1)-screen_dx, 200*j))
    for i in range(5):
        if player_state[i] == 1:
            if i :
                pygame.draw.rect(DISPLAY, player_color[i], (player_x[i]-50-screen_dx, player_y[i]-50,100,100))
            DISPLAY.blit(player_IMG[player_dir[i]][player_frame[i]], (player_x[i]-50-screen_dx, player_y[i]-50))
            # DISPLAY.blit(catImg, (player_x[i], player_y[i])) #繪製覆蓋整個視窗

    if game_over != -1:
        DISPLAY.blit(gameoverIMG[game_over], (20, 340))
    pygame.display.flip()

def BOOM(trap_ID,trap_num):
    for i in range(27):
        trap_frame[trap_ID]=i
        update_screen()
        time.sleep(0.08)

def recvData():
    global screen_dx
    global Broadcast_Port
    global Broadcast_sd
    global game_over
    while True:
        DISPLAY.fill((40,40,60))
        data, addr = Broadcast_sd.recvfrom(1024)
        data=data.decode('big5')
        #print(data)
        while len(data):
            if data[0]=='0':
                if player_x[int(data[1:5])] > int(data[5:9]) :
                    player_dir[int(data[1:5])] = 1
                if player_x[int(data[1:5])] < int(data[5:9]) :
                    player_dir[int(data[1:5])] = 0
                player_x[int(data[1:5])]=int(data[5:9])
                player_y[int(data[1:5])]=int(data[9:13])
                player_state[int(data[1:5])] = 1
                if player_ID == int(data[1:5]):
                    screen_dx = player_x[player_ID]-400
                    if screen_dx < 0:
                        screen_dx = 0
                    elif screen_dx > 1600:
                        screen_dx = 1600
                player_frame[int(data[1:5])]  = player_next_frame(player_frame[int(data[1:5])]) 
                
            if data[0]=='1':
                player_x[int(data[1:5])]=9999
                player_y[int(data[1:5])]=9999
                #print(f'player{int(data[1:5])} disconnect')
            if data[0]=='2':
                if int(data[1:5]) != player_ID :
                    player_x[int(data[1:5])]=9999
                    player_y[int(data[1:5])]=9999
                player_state[int(data[1:5])] = 2
                #print(f'player{int(data[1:5])} was dead!')
            if data[0]=='3':
                #print(f'trap:{data[1:5]} {data[5:9]} Y')
                for i in range(3):
                    if i != int(data[5:9]):
                        trap[int(data[1:5])][i] = 1
            if data[0]=='4':
                #print(f'trap:{data[1:5]} {data[5:9]} R')
                for i in range(3):
                    if i != int(data[5:9]):
                        trap[int(data[1:5])][i] = 2
                threading.Thread(target=BOOM,args=(int(data[1:5]),int(data[5:9]))).start()
            if data[0]=='5':
                #print(f'trap:{data[1:5]} {data[5:9]} G')
                for i in range(3):
                    if i != int(data[5:9]):
                        trap[int(data[1:5])][i] = 0
            if data[0]=='6':
                print("game over")
                if int(data[1:5]) == 0 :
                    game_over = 0
                    print("murder win")
                else :
                    game_over = 1
                    print("runner win")
            data = data[13:]
        update_screen()
        

player_x=[9999 for i in range(5)]
player_y=[9999 for i in range(5)]

server_sd.connect((serverAddr, serverPort))
player_ID = server_sd.recv(1024).decode('utf-8')
player_ID=player_ID[0:len(player_ID)-1]
print(player_ID)
player_ID=int(player_ID)
Broadcast_Port = 5678+player_ID
print(Broadcast_Port)

server_sd.setblocking(False)
Broadcast_sd.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
Broadcast_sd.bind(("0.0.0.0", Broadcast_Port))
threading.Thread(target=recvData).start()

player_x[player_ID]=100
if player_ID:
    player_y[player_ID]=player_ID*150-75
else:
    player_y[player_ID]=725

DATA ="0" + str(player_ID).zfill(4) + str(player_x[player_ID]).zfill(4) + str(player_y[player_ID]).zfill(4)
server_sd.send(DATA.encode())


while True:
    

    # 偵測事件
    for event in pygame.event.get():
        # 按叉叉就退出
        if event.type == QUIT:
            server_sd.close()
            pygame.quit()
            sys.exit()
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player_x[player_ID]-=10
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player_x[player_ID]+=10                
        if player_ID and (keys[pygame.K_w] or keys[pygame.K_UP]):
            player_y[player_ID]-=10
        if player_ID and (keys[pygame.K_s] or keys[pygame.K_DOWN]):
            player_y[player_ID]+=10

        if player_x[player_ID] > XUB:
            player_x[player_ID] = XUB
        if player_x[player_ID] < XLB:
            player_x[player_ID] = XLB
        if player_ID != 0 :
            if player_y[player_ID] < YLB:
                player_y[player_ID] = YLB
            if player_y[player_ID] > YUB:
                player_y[player_ID] = YUB
            
            
        if player_state[player_ID] == 1:
            if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                DATA ="0" + str(player_ID).zfill(4) + str(player_x[player_ID]).zfill(4) + str(player_y[player_ID]).zfill(4)
                server_sd.send(DATA.encode())
        if player_state[player_ID] == 2:
            if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                screen_dx = player_x[player_ID]-400
                if screen_dx < 0:
                    screen_dx = 0
                elif screen_dx > 1600:
                    screen_dx = 1600
                update_screen()
                
        if keys[pygame.K_1] or keys[pygame.K_2] or keys[pygame.K_3] or keys[pygame.K_KP1] or keys[pygame.K_KP2] or keys[pygame.K_KP3] :
            if player_ID == 0 :
                button = player_x[0]//200 - 1
                if 10 > button >= 0 :
                    if not trap_opened[button]:
                        if keys[pygame.K_1] or keys[pygame.K_KP1]:
                            push = 0
                        if keys[pygame.K_2] or keys[pygame.K_KP2]:
                            push = 1
                        if keys[pygame.K_3] or keys[pygame.K_KP3]:
                            push = 2
                        DATA ="1" + str(button).zfill(4) + str(push).zfill(4) + '0000'
                        server_sd.send(DATA.encode())
                        trap_opened[button]=1
            
    fpsClock.tick(FPS)



