# Classe de Jean-Eude avec IA simple de patrouille gauche/droite
import pygame
from entities.base_entity import BaseEntity
from settings import *
from typing import Optional, List


class JeanEude(BaseEntity):

    def __init__(self, x: float, y: float, patrol_range: float = 150.0):
        super().__init__(x, y, JEANEUDE_WIDTH, JEANEUDE_HEIGHT)

        # Apparence (rouge pour l'instant)
        self.image.fill((220, 50, 50))

        # IA de patrouille
        self.patrol_origin_x = x          # Centre de la zone de patrouille
        self.patrol_range = patrol_range  # Distance max de chaque côté
        self.direction = 1                # 1 = droite, -1 = gauche

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

        self.rect.topleft = (int(self.x), int(self.y))

    # Patrouille gauche/droite de Jean-Eude

    def _update_patrol(self):
        """Avance dans la direction courante ; fait demi-tour aux limites
        de la zone ou si un mur est touché."""

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

    def draw(self, surface: pygame.Surface, offset=(0, 0)):
        draw_rect = self.rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]
        surface.blit(self.image, draw_rect)

        if SHOW_COLLIDERS:
            pygame.draw.rect(surface, (255, 100, 0), draw_rect, 1)