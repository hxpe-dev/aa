import pygame
from typing import List, Tuple, Optional
from world.ldtk_loader import LDtkLoader, LDtkLevel

try:
    from settings import TILE_SIZE
except ImportError:
    TILE_SIZE = 16


class TileMap:
    def __init__(self, ldtk_path: Optional[str] = None, level_index: int = 0, scale: float = 1.0, level_data: List[List[int]] = None, tile_size: int = TILE_SIZE):
        self.tile_size = tile_size
        self._ldtk_level: Optional[LDtkLevel] = None
        self.spawn_point: Tuple[float, float] = (100.0, 100.0)

        if ldtk_path:
            self._load_from_ldtk(ldtk_path, level_index, scale)
        else:
            # Fallback sur l'ancien système si pas de fichier LDtk pask jsp
            self._load_from_grid(level_data)

    def _load_from_ldtk(self, path: str, level_index: int, scale: float):
        self._ldtk_loader = LDtkLoader(path)
        self._ldtk_path = path
        self._scale = scale
        self._ldtk_level = self._ldtk_loader.load_level(level_index, scale=scale)
        self.width = self._ldtk_level.width_px
        self.height = self._ldtk_level.height_px
        self.spawn_point = self._ldtk_level.get_spawn_point()

    def _load_from_grid(self, level_data):
        if level_data is None:
            level_data = self._create_default_level()
        self.level_data = level_data
        self.height = len(level_data) * self.tile_size
        self.width = (len(level_data[0]) if level_data else 0) * self.tile_size
        self.image = self._build_grid_surface(level_data)
        

    def load_level(self, level_index: int):
        # Charge un autre niveau en réutilisant le mm loader
        self._ldtk_level = self._ldtk_loader.load_level(level_index, scale=self._scale)
        self.width = self._ldtk_level.width_px
        self.height = self._ldtk_level.height_px
        self.spawn_point = self._ldtk_level.get_spawn_point()
        
    def find_door_position(self, entity_iid: str):
        return self._ldtk_loader.find_door_position(entity_iid, self._scale)

    def get_level_index_by_iid(self, level_iid: str) -> int:
        return self._ldtk_loader.get_level_index_by_iid(level_iid)
    
    def get_enemy_spawns(self) -> list:
        if self._ldtk_level:
            return self._ldtk_level.get_enemy_spawns()
        return []

    def get_boss_spawns(self) -> list:
        if self._ldtk_level:
            return self._ldtk_level.get_boss_spawns()
        return []

    def get_colliders(self) -> List[pygame.Rect]:
        if self._ldtk_level:
            return self._ldtk_level.get_colliders()
        return self._get_grid_colliders()

    def get_spawn_point(self) -> Tuple[float, float]:
        return self.spawn_point
    
    def get_doors(self):
        if self._ldtk_level:
            return self._ldtk_level.get_doors()
        return []

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        if self._ldtk_level:
            self._ldtk_level.draw(surface, offset)
        else:
            rect = self.image.get_rect(topleft=offset)
            surface.blit(self.image, rect)

    # Ancien système de grille manuelle (au cas ou)

    def _create_default_level(self) -> List[List[int]]:
        # Génère un niveau basique avec des murs sur les bords et un sol
        level = []
        for y in range(15):
            row = []
            for x in range(40):
                if x == 0 or x == 39 or y == 14 or y == 13:
                    row.append(1)
                else:
                    row.append(0)
            level.append(row)
        return level

    def _build_grid_surface(self, level_data) -> pygame.Surface:
        # Dessine tous les tiles solides une seule fois sur une surface statique
        rows = len(level_data)
        cols = len(level_data[0]) if level_data else 0
        surf = pygame.Surface((cols * self.tile_size, rows * self.tile_size))
        surf.fill((20, 20, 30))
        for y, row in enumerate(level_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size,
                                       self.tile_size, self.tile_size)
                    pygame.draw.rect(surf, (100, 100, 100), rect)
                    pygame.draw.rect(surf, (150, 150, 150), rect, 2)
        return surf

    def _get_grid_colliders(self) -> List[pygame.Rect]:
        # Parcourt la grille et retourne un rect pour chaque tile solide
        colliders = []
        for y, row in enumerate(self.level_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    colliders.append(pygame.Rect(
                        x * self.tile_size, y * self.tile_size,
                        self.tile_size, self.tile_size
                    ))
        return colliders

    def get_size(self) -> Tuple[int, int]:
        return (self.width, self.height)