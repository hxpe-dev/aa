# Classe mère pour toutes les entités du jeu (joueur, ennemis, boss)
# Gère la position, la vélocité, la gravité ...
import pygame
from typing import Tuple


class BaseEntity(pygame.sprite.Sprite):
    # Classe de base pour les entités du jeu    
    
    def __init__(self, x: float, y: float, width: int, height: int):
        # Initialise une entité à position et dimensions données
        super().__init__()
        
        # Position et Dimensions
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        
        # Vélocité
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # État Physique
        self.is_grounded = False  # Au contact du sol
        self.is_falling = False   # En train de tomber
        
        # Affichage
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 0, 255))  # Magenta par défaut (placeholder)
        self.rect = self.image.get_rect(topleft=(x, y))
    
    def get_rect(self) -> pygame.Rect:
        # Retourne le rectangle de collision de l'entité
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def set_position(self, x: float, y: float):
        # Définit la position de l'entité
        self.x = x
        self.y = y
        self.rect.topleft = (int(self.x), int(self.y))
    
    def apply_velocity(self, velocity_x: float, velocity_y: float):
        # Applique une vélocité / vitesse à l'entité
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
    
    def check_collision(self, other_rect: pygame.Rect) -> bool:
        # Vérifie la collision avec un autre rectangle, renvoie True si collision, False sinon
        return self.get_rect().colliderect(other_rect)
    
    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        # Dessine l'entité sur la surface avec un décalage optionnel (décalage caméra)
        draw_rect = self.rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]
        surface.blit(self.image, draw_rect)
