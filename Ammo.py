import pygame


class Ammo(pygame.sprite.Sprite):
    def __init__(self, pos, color=(255, 255, 255)):
        super(Ammo, self).__init__()
        self.image = self.image = pygame.Surface((25, 25))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.pos = pos

    def update(self, player):
        if self.pos == 1:
            self.rect.topright = (player.rect.left - 7, player.rect.top)
        elif self.pos == 2:
            self.rect.topleft = (player.rect.right + 7, player.rect.top)
        elif self.pos == 3:
            self.rect.midright = (player.rect.left - 7, player.rect.centery)
        elif self.pos == 4:
            self.rect.midleft = (player.rect.right + 7, player.rect.centery)
        elif self.pos == 5:
            self.rect.bottomright = (player.rect.left - 7, player.rect.bottom)
        elif self.pos == 6:
            self.rect.bottomleft = (player.rect.right + 7, player.rect.bottom)
