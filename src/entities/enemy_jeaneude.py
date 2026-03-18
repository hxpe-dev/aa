# Classe de Jean-Eude avec IA simple de patrouille gauche/droite
import pygame
from entities.base_entity import BaseEntity
from settings import *
from typing import Optional, List


class JeanEude(BaseEntity):

    def __init__(self, x: float, y: float, patrol_range: float = 150.0):
        super().__init__(x, y, JEANEUDE_WIDTH, JEANEUDE_HEIGHT)

        # Apparence
        self.sprite_size = 105
        self.current_sprite_index = 0
        self.sprite_counter = 0
        self.direction = 1 # 1 = droite, -1 = gauche
        
        self.walking_sprites = [
            pygame.transform.scale(pygame.image.load(f'src\\assets\\mobs\\skeleton\\Walking\\Walking-{i}.png').convert_alpha(), (self.sprite_size, self.sprite_size)) for i in range(2)
        ]
        self.sprite = self.walking_sprites[0]
        self.image = self.sprite
        
        # IA de patrouille
        self.patrol_origin_x = x          # Centre de la zone de patrouille
        self.patrol_range = patrol_range  # Distance max de chaque côté

        # État de collision
        self.collision_left = False
        self.collision_right = False
        self.collision_top = False
        self.collision_bottom = False

    # Mise à jour principale

    def update(self, dt: float, colliders: Optional[List[pygame.Rect]] = None):
        if colliders is None:
            colliders = []

        self._update_patrol()
        self._apply_gravity()
        self._move_and_collide(colliders)
        self._update_animation()

        self.rect.topleft = (int(self.x), int(self.y))
        
        # Retourne le sprite en fn de la direction
        if self.direction == -1:
            self.image = pygame.transform.flip(self.sprite, True, False)
        else:
            self.image = self.sprite


    # Patrouille gauche/droite de Jean-Eude

    def _update_patrol(self):
        # Avance dans la direction courante. fait demi-tour aux limites de la zone ou si un mur est touché.

        # Demi-tour si on dépasse la zone de patrouille
        if self.x > self.patrol_origin_x + self.patrol_range:
            self.direction = -1
        elif self.x < self.patrol_origin_x - self.patrol_range:
            self.direction = 1

        # Demi-tour si mur devant
        if self.direction == 1 and self.collision_right:
            self.direction = -1
        elif self.direction == -1 and self.collision_left:
            self.direction = 1

        self.velocity_x = self.direction * JEANEUDE_SPEED

    # Gravité appliqué a Jean-Eude

    def _apply_gravity(self):
        if not self.is_grounded:
            self.velocity_y += PLAYER_FALL_ACCELERATION         # On utilise la meme gravité que le joueur
            self.velocity_y = min(self.velocity_y, PLAYER_MAX_FALL_SPEED)

    # Déplacement et collisions, la même logique que Player

    def _move_and_collide(self, colliders: List[pygame.Rect]):
        # Mouvement horizontal
        self.x += self.velocity_x
        rect = self.get_rect()
        self.collision_left = False
        self.collision_right = False

        for collider in colliders:
            if not rect.colliderect(collider):
                continue
            if self.velocity_x > 0:
                self.x = collider.left - self.width
                self.velocity_x = 0
                self.collision_right = True
            elif self.velocity_x < 0:
                self.x = collider.right
                self.velocity_x = 0
                self.collision_left = True
            rect = self.get_rect()

        # Mouvement vertical
        self.y += self.velocity_y
        rect = self.get_rect()
        self.collision_top = False
        self.collision_bottom = False

        for collider in colliders:
            if not rect.colliderect(collider):
                continue
            if self.velocity_y > 0:
                self.y = collider.top - self.height
                self.velocity_y = 0
                self.collision_bottom = True
                break
            elif self.velocity_y < 0:
                self.y = collider.bottom
                self.velocity_y = 0
                self.collision_top = True
                break
            rect = self.get_rect()

        # Vérifier si Jean-Eude est en contact avec le sol
        self.is_grounded = False
        if self.collision_bottom:
            self.is_grounded = True
        else:
            test_rect = self.get_rect()
            test_rect.y += 1
            for collider in colliders:
                if test_rect.colliderect(collider):
                    self.is_grounded = True
                    break

        self.is_walled_left = self.collision_left
        self.is_walled_right = self.collision_right
        
    def _update_animation(self):
        self.sprite_counter += 1
        if self.sprite_counter >= 8:
            self.current_sprite_index = (self.current_sprite_index + 1) % len(self.walking_sprites)
            self.sprite = self.walking_sprites[self.current_sprite_index]
            self.sprite_counter = 0

    def draw(self, surface: pygame.Surface, offset=(0, 0)):
        render_x = self.x + offset[0] - (self.sprite_size - JEANEUDE_WIDTH) // 2
        render_y = self.y + offset[1] - (self.sprite_size - JEANEUDE_HEIGHT)
        surface.blit(self.image, (render_x, render_y))

        if SHOW_COLLIDERS:
            draw_rect = self.rect.copy()
            draw_rect.x += offset[0]
            draw_rect.y += offset[1]
            pygame.draw.rect(surface, (255, 100, 0), draw_rect, 1)