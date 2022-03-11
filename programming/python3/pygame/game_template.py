#!/usr/bin/env python3

import pygame

pygame.display.set_caption("Title")
WIDTH = 900
HEIGHT = 500
window = pygame.display.set_mode((WIDTH, HEIGHT))
FPS = 60

def draw_window():
    window.fill((255,255,255))
    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        draw_window()


main()
