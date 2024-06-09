import pygame

HEIGHT = 800


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, width, way_side, way_length=HEIGHT, speed=10, color=(255, 255, 255)):
        super(Bullet, self).__init__()
        self.image = pygame.Surface((width, width))
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.send_it = False
        self.speed = speed
        self.way_length = way_length
        self.way_side = way_side

    def movement(self):
        if self.way_side == 'up':
            self.rect.top -= self.speed
        else:
            self.rect.bottom += self.speed

        self.way_length -= self.speed

        if self.rect.top < -self.rect.height:
            self.send_it = True

        if self.way_length <= 0:
            self.kill()

    def update(self):
        self.movement()
