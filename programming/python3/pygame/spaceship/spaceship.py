#!/usr/bin/env python3

import pygame

pygame.display.set_caption("Spaceship")
WIDTH = 900
HEIGHT = 500
window = pygame.display.set_mode((WIDTH, HEIGHT))
border = pygame.Rect(((WIDTH/2)-5), 0, 10, HEIGHT)
FPS = 60

space_width, space_height = 55, 40
velocity = 5

yellow_space = pygame.image.load("./Assets/spaceship_yellow.png")
yellow_space = pygame.transform.scale(yellow_space, (space_width, space_height))
yellow_space = pygame.transform.rotate(yellow_space, 90)
red_space = pygame.image.load("./Assets/spaceship_red.png")
red_space = pygame.transform.scale(red_space, (space_width, space_height))
red_space = pygame.transform.rotate(red_space, 270)


def yellow_movement(keys, yellow):
    if keys[pygame.K_a] and yellow.x - velocity >= 0:
        yellow.x -= velocity
    if keys[pygame.K_d] and yellow.x + velocity + yellow.width < border.x + border.width:
        yellow.x += velocity
    if keys[pygame.K_w] and yellow.y - velocity > 0:
        yellow.y -= velocity
    if keys[pygame.K_s] and yellow.y + velocity + yellow.height < HEIGHT - 15:
        yellow.y += velocity

def red_movement(keys, red):
    if keys[pygame.K_LEFT] and red.x - velocity > border.x + border.width:
        red.x -= velocity
    if keys[pygame.K_RIGHT] and red.x + velocity + red.width < WIDTH + 15:
        red.x += velocity
    if keys[pygame.K_UP] and red.y - velocity > 0:
        red.y -= velocity
    if keys[pygame.K_DOWN] and red.y + velocity + red.height < HEIGHT - 15:
        red.y += velocity


def draw_window(red, yellow):
    window.fill((255,255,255))
    pygame.draw.rect(window, (0,0,0), border)
    window.blit(yellow_space, (yellow.x, yellow.y))
    window.blit(red_space, (red.x, red.y))

    pygame.display.update()


def main():
    red = pygame.Rect(700, 300, space_width, space_height)
    yellow = pygame.Rect(100, 300, space_width, space_height)

    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        keys = pygame.key.get_pressed()
        yellow_movement(keys, yellow)
        red_movement(keys, red)

        draw_window(red, yellow)

main()
