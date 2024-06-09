import pygame
from Ammo import Ammo
from Bullet import Bullet

WIDTH = 1540
HEIGHT = 800


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.image = pygame.image.load("player.png").convert_alpha()
        self.rect = self.image.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        self.speed = 7
        self.life = 6
        self.stack = [Ammo(6), Ammo(5), Ammo(4), Ammo(3), Ammo(2), Ammo(1)]
        self.ammoG = pygame.sprite.Group(self.stack)
        self.bullets = 6

    def animation_state(self):
        rect = self.rect
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and rect.left >= 0:
            rect.centerx -= self.speed
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and rect.top >= 0:
            rect.centery -= self.speed
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and rect.right <= WIDTH:
            rect.centerx += self.speed
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and rect.bottom <= HEIGHT:
            rect.centery += self.speed

    def create_bullet(self, width_level, direction='up'):
        self.ammo(width_level)
        if width_level == 1:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 20, direction)
        elif width_level == 2:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 30, direction, HEIGHT + 100)
        elif width_level == 3:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 40, direction, HEIGHT + 200)
        elif width_level == 4:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 50, direction, HEIGHT + 300)
        elif width_level == 5:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 60, direction, HEIGHT + 400)
        elif width_level == 6:
            return Bullet(self.rect.midtop[0], self.rect.midtop[1], 70, direction, HEIGHT + 500)

    def ammo(self, bullets_shot):
        if self.bullets > 0:
            self.bullets -= bullets_shot

    def add_ammo(self):
        if self.bullets < 6:
            self.stack.append(Ammo(6 - self.bullets))
            self.bullets += 1

    def delete_ammo(self):
        self.stack.pop()

    def update(self, screen):
        self.animation_state()
        self.ammoG = pygame.sprite.Group(self.stack)
        self.ammoG.draw(screen)
        self.ammoG.update(self)
