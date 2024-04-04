"""
Name: Alexander Tran
Student Number: 100788359
CSCI 3010U Course Project: Bullet Simulation
"""

import pygame, sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
from scipy.integrate import ode

#Colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

clock = pygame.time.Clock()

#Real life wind speed data, converted from km/h to m/s
df = pd.read_csv('weather_cleaned.csv')
data = df['wind_speed'].tolist() #Global

#Text class
class MyText():
    def __init__(self, color, background=WHITE, antialias=True, fontname="Times New Roman", fontsize=16):
        pygame.font.init()
        self.font = pygame.font.SysFont(fontname, fontsize)
        self.color = color
        self.background = background
        self.antialias = antialias

    def draw(self, str1, screen, pos):
        text = self.font.render(str1, self.antialias, self.color, self.background)
        screen.blit(text, pos)

#Pygame circle class represents bullets
class Bullet(pygame.sprite.Sprite):
    def __init__(self, color, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([width, height])
        self.rect = self.image.get_rect()
        self.image.fill(WHITE)
        cx = self.rect.centerx
        cy = self.rect.centery
        pygame.draw.circle(self.image, color, (width//2, height//2), cx, cy)
        self.rect = self.image.get_rect()

    def update(self):
        pass

class Simulation:
    def __init__(self):
        self.pos = np.array([0, 10, 0]) #x, y, z
        self.vx = 0 #x direction velocity
        self.vy = 0 #y direction velocity
        self.vz = 0 #z direction velocity

        #Plotting variables
        self.trace_x = 0 
        self.trace_y = 0 
        self.trace_z = 0 #Used for POV 
        
        self.state = np.array([self.vx, self.vy, self.vz, 0, 0, 0]) #Vx, Vy, Vz, ax, ay, az
       
        self.gravity = 9.8
        self.mass = 0.0

        #Variables for air resistance calculation
        self.p = 1.293 #Density of air
        #Drag coefficient, calculated from ballistic
        #coefficient and cross sectional area of bullet
        self.Cd = 0 
        self.A = 0 #Cross sectional area

        #Random wind speed
        self.wind = 0

        #Variables for Coriolis effect calculation
        self.omega = 0.000727 #Angular velocity of the Earth
        self.alpha = -np.sin(43.8971) #Latitude of Oshawa, Ontario
        
        self.cur_time = 0
        self.dt = 0.0033
        
        self.paused = True # starting in paused mode

        self.solver = ode(self.f)
        self.solver.set_integrator('dop853')
        self.solver.set_f_params(self.Cd, self.gravity)

    def f(self, t, state, arg1, arg2):
        #Calculate air resistance
        #Fd = 1/2 * p * Cd * A
        Fd = 0.5 * self.p * self.Cd * (self.A / 1550.0)

        ax = -(Fd * self.vx) / self.mass #Acceleration x
        ay = -arg2 - ((Fd * self.vy) / self.mass) #Acceleration y

        #Calculate coriolis force
        az = (2.0 * np.sqrt((self.vx**2 + self.vy**2)) * self.omega * self.alpha) / self.mass

        #Calculate wind force
        az += self.wind * np.sqrt(self.vx**2 + self.vy**2) / self.mass / 1000.0
        
        dstate = np.array([self.vx, self.vy, self.vz, ax, ay, az])
             
        return dstate           
    
    #Initialize variables
    def setup(self, speed, mass, Bc, A, angle_degrees):
        self.mass = mass
        #Calculate velocity
        self.vx = speed * np.cos(np.deg2rad(angle_degrees))
        self.vy = speed * np.sin(np.deg2rad(angle_degrees))
        self.vz = self.wind * self.mass
        self.trace_x = [self.pos[0]]
        self.trace_y = [self.pos[1]]
        self.trace_z = [self.pos[2]]

        #Calculate drag coefficient
        self.A = A
        self.Cd = (self.mass / 453.6) / (Bc * A)

        #Randomly sample wind from distribution
        self.wind = sample_wind_speed(data)

        self.solver.set_initial_value([self.pos[0], self.pos[1], self.pos[2], self.vx, self.vy, self.vz], self.cur_time)

    def step(self):
        self.cur_time += self.dt

        if self.solver.successful():
            self.solver.integrate(self.cur_time)
            
        self.pos = self.solver.y[0:3]
        self.vx = self.solver.y[3]
        self.vy = self.solver.y[4]
        self.vz = self.solver.y[5]
        
        self.trace_x.append(self.pos[0])
        self.trace_y.append(self.pos[1])
        self.trace_z.append(self.pos[2])

        #DEBUG
        # print("x: ", self.pos[0])
        # print("y: ", self.pos[1])
        # print("z: ", self.pos[2])
        # print(self.vx)
        # print(self.vy)
        # print(self.vz)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        
def sim_to_screen(win_height, x, y):
    '''flipping y, since we want our y to increase as we move up'''
    x += 10
    y += 10

    return x, win_height - y

def sample_wind_speed(data):
    rand_direction = random.choice((-1, 1))
    return rand_direction * random.sample(data, 1)[0]

#Main
def main():    
    #Pygame setup
    pygame.init()
    text = MyText(BLACK)
    win_width = 800
    win_height = 600
    screen = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption('Bullet Simulation')
    bullet = Bullet(RED, 10, 10)
    bullet_pov = Bullet(BLACK, 10, 10)
    my_group = pygame.sprite.Group(bullet, bullet_pov)

    #Simulation setup
    sim = Simulation()

    welcome_str = ("""
------------------------------
BULLET SIMULATION PROJECT
------------------------------
Select a bullet to simulate:
1. 9x19mm Parabellum 124 gr FMJ
2. 5.56x45mm NATO 62 gr FMJ-BT
3. 7.62x51mm NATO 147 gr FMJ
""")
    
    invalid_str = ("""
Select a valid bullet to simulate:
1. 9x19mm Parabellum 124 gr FMJ
2. 5.56x45mm NATO 62 gr FMJ-BT
3. 7.62x51mm NATO 147 gr FMJ
""")
    
    # Get simulation choice from user, setup sim accordingly
    choice = int(input(welcome_str))
    while True:
        match choice:
            case 1:
                sim.setup(385, 8.04, 0.125, 0.0989, 0.3)
                #Muzzle velocity: 385m/s from a 118mm barrel
                #Mass of bullet: 124gr = 8.04g
                #Ballistic coefficient: 0.125
                #Cross sectional area: 0.0989 square inches
                break
            case 2:
                sim.setup(945, 4.01, 0.149, 0.0394, 0.3)
                #Muzzle velocity: 945m/s from a 508mm barrel
                #Mass of bullet: 62gr = 4.01g
                #Ballistic coefficient: 0.149
                #Cross sectional area: 0.0394 square inches
                break
            case 3:
                sim.setup(850, 9.53, 0.209, 0.0745, 0.3)
                #Muzzle velocity: 850m/s from a 559mm barrel
                #Mass of bullet: 147gr = 9.53g
                #Ballistic coefficient: 0.209
                #Cross sectional area: 0.0745 square inches
                break
            case _:
                choice = int(input(invalid_str))

    # sim.setup(850, 9.53, 0.209, 0.0745, 0.3)

    print('--------------------------------')
    print('Usage:')
    print('Press (r) to start/resume simulation')
    print('Press (p) to pause simulation')
    print('Press (q) to quit')
    print('Press (space) to step forward simulation when paused')
    print('--------------------------------')

    while True:
        # 30 fps
        clock.tick(60)

        #Display trajectory
        scale = 0.5
        bullet.rect.x, bullet.rect.y = sim_to_screen(win_height, sim.pos[0], sim.pos[1])
        bullet.rect.x *= scale #Scale x distance to fit on screen

        #Display pov
        scale_pov_x = 10
        scale_pov_y = 1.5
        bullet_pov.rect.x, bullet_pov.rect.y = sim_to_screen(win_height, sim.pos[2], sim.pos[1])
        bullet_pov.rect.x += (sim.pos[2] * scale_pov_x) + 685
        bullet_pov.rect.y -= (sim.pos[1] * scale_pov_y) + 470

        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            sim.pause()
            continue
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            sim.resume()
            continue
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            break
        else:
            pass

        screen.fill(WHITE)
        my_group.update()
        my_group.draw(screen)
        text.draw("Time = %f" % sim.cur_time, screen, (10,10))
        text.draw("x = %f" % sim.pos[0], screen, (10,40))
        text.draw("y = %f" % sim.pos[1], screen, (10,70))
        text.draw("z = %f" % sim.pos[2], screen, (10,100))
        text.draw("Firing POV (Upscaled)", screen, (610,10))
        pygame.draw.line(screen, BLACK, (600,0), (600,200))
        pygame.draw.line(screen, BLACK, (600,200), (800,200))
        pygame.draw.line(screen, BLACK, (600,100), (800,100))
        pygame.draw.line(screen, BLACK, (700,200), (700,0))
        pygame.display.flip()

        if sim.pos[1] <= -1.:
            pygame.quit()
            break

        #Update simulation
        if not sim.paused:
            sim.step()
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                sim.step()


    #Plotting
    fig, axs = plt.subplots(2)
    #Plot trajectory
    axs[0].plot(sim.trace_x, sim.trace_y)
    axs[0].set_xlabel('x')
    axs[0].set_ylabel('y')
    axs[0].set_title('Trajectory')
    axs[0].axis('equal')

    #Plot firing perspective
    axs[1].plot(sim.trace_z, sim.trace_y)
    axs[1].set_xlabel('z')
    axs[1].set_ylabel('y')
    axs[1].set_xlim([-1, 1])
    axs[1].set_title("Trajectory From Firing Perspective")

    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()