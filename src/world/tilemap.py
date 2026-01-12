import pygame
from typing import List, Tuple

try:
    from settings import TILE_SIZE
except ImportError:
    TILE_SIZE = 32


class TileMap:    
    def __init__(self, level_data: List[List[int]] = None, tile_size: int = TILE_SIZE):
        # Initilise un tilemap à partir de données
        # level_data: Données 2D du niveau (0 = vide, 1 = solide)
        # tile_size: Taille des tiles en pixels
        self.tile_size = tile_size
        
        if level_data is None:
            # Créer un niveau par défaut
            level_data = self._create_default_level()
        
        self.level_data = level_data
        self.height = len(level_data)
        self.width = len(level_data[0]) if level_data else 0
        
        # Créer une surface contenant le rendu du tilemap
        self.image = pygame.Surface((
            self.width * self.tile_size,
            self.height * self.tile_size
        ))
        self.image.fill((20, 20, 30))  # Fond sombre
        
        # Dessiner tous les tiles
        self._draw_tiles()
    
    def _create_default_level(self) -> List[List[int]]:
        # Créer un niveau de test par défaut
        level = []
        for y in range(15):
            row = []
            for x in range(40):
                # Bordures (gauche et droite)
                if x == 0 or x == 39:
                    row.append(1)
                # Sol et plafond
                elif y == 14 or y == 13:
                    row.append(1)
                # Plateformes de test
                elif y == 12 and 6 <= x <= 8:
                    row.append(1)
                elif y == 10 and 22 <= x <= 24:
                    row.append(1)
                elif y == 8 and 3 <= x <= 4:
                    row.append(1)
                elif y == 8 and 32 <= x <= 33:
                    row.append(1)
                else:
                    row.append(0)
            level.append(row)
        return level
    
    def _draw_tiles(self):
        # Dessine tous les tiles solides sur l'image du tilemap
        for y, row in enumerate(self.level_data):
            for x, tile in enumerate(row):
                if tile == 1:  # Tile solide
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    # Remplir le tile avec couleur grise
                    pygame.draw.rect(self.image, (100, 100, 100), rect)
                    # Ajouter une bordure claire pour visibilité
                    pygame.draw.rect(self.image, (150, 150, 150), rect, 2)
    
    def get_colliders(self) -> List[pygame.Rect]:
        # Retourne la liste des rectangles de collision pour les tiles solides
        colliders = []
        
        for y, row in enumerate(self.level_data):
            for x, tile in enumerate(row):
                if tile == 1:  # Tile solide
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    colliders.append(rect)
        
        return colliders
    
    def get_size(self) -> Tuple[int, int]:
        # Retourne la taille totale du tilemap en pixels
        return (self.width * self.tile_size, self.height * self.tile_size)
    
    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        # Dessine le tilemap sur une surface
        rect = self.image.get_rect(topleft=offset)
        surface.blit(self.image, rect)
