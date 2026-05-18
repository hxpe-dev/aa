import json
import pygame
from typing import List, Tuple, Dict, Optional
import os


class LDtkLoader:
    def __init__(self, filepath: str):
        # On ouvre et lit le fichier .ldtk qui est juste un JSON
        with open(filepath, 'r') as f:
            self.data = json.load(f)
        self.tilesets: Dict[int, pygame.Surface] = {}
        self._load_tilesets(filepath)

    def _load_tilesets(self, ldtk_filepath: str):
        # On récupère le dossier du .ldtk pour résoudre les chemins relatifs des tilesets
        ldtk_dir = os.path.dirname(ldtk_filepath)

        for tileset in self.data.get("defs", {}).get("tilesets", []):
            uid = tileset["uid"]
            rel_path = tileset.get("relPath")
            if not rel_path:
                continue
            # On reconstruit le chemin absolu vers l'image du tileset
            full_path = os.path.join(ldtk_dir, rel_path)
            try:
                img = pygame.image.load(full_path).convert_alpha()
                expected_w = tileset.get("pxWid")
                expected_h = tileset.get("pxHei")
                if expected_w and expected_h and img.get_size() != (expected_w, expected_h):
                    img = pygame.transform.scale(img, (expected_w, expected_h))
                self.tilesets[uid] = img  # On stock l'image avec son uid comme clé
            except Exception as e:
                print(f"Erreur chargement tileset '{full_path}': {e}")

    def get_levels(self) -> list:
        # Retourne la liste de tous les niveaux du projet LDtk
        return self.data.get("levels", [])

    def load_level(self, level_index: int = 0, scale: float = 1.0) -> "LDtkLevel":
        levels = self.get_levels()
        if level_index >= len(levels):
            raise IndexError(f"Level {level_index} existe pas")
        # On crée un objet LDtkLevel à partir des données brutes du niveau
        return LDtkLevel(levels[level_index], self.tilesets, scale=scale)
    
    def find_door_position(self, entity_iid: str, scale: float = 1.0):
        # Trouve la position x y d'une porte à partir de son iid, dans tous les niveaux
        for level_data in self.data.get("levels", []):
            for layer in level_data.get("layerInstances", []):
                if layer["__type"] != "Entities":
                    continue
                for entity in layer.get("entityInstances", []):
                    if entity["iid"] == entity_iid:
                        px = entity["px"]
                        return (float(px[0]) * scale, float(px[1]) * scale)
        return None
    
    
    def get_level_index_by_iid(self, level_iid: str) -> int:
        # Retourne l'index d'un niveau a partir de son iid
        for i, level in enumerate(self.data.get("levels", [])):
            if level["iid"] == level_iid:
                return i
        return -1


class LDtkLevel:
    def __init__(self, level_data: dict, tilesets: Dict[int, pygame.Surface], scale: float = 1.0):
        self.level_data = level_data
        self.tilesets = tilesets
        self.scale = scale  # Facteur de zoom appliqué à toute la map

        # Taille finale de la map en pixels après zoom
        self.width_px = int(level_data["pxWid"] * scale)
        self.height_px = int(level_data["pxHei"] * scale)

        self.render_surface: Optional[pygame.Surface] = None
        self.colliders: List[pygame.Rect] = []
        self.spawn_point: Tuple[float, float] = (100.0, 100.0)
        self.enemy_spawns: List[dict] = []
        self.doors: List[dict] = []

        self._parse_layers()

    def _parse_layers(self):
        layers = self.level_data.get("layerInstances", [])
        if not layers:
            return

        # Surface finale sur laquelle on va tout dessiner
        self.render_surface = pygame.Surface(
            (self.width_px, self.height_px), pygame.SRCALPHA # transparent par défaut
        )

        # LDtk stocke les layers du dessus vers le dessous,
        # donc on inverse pour dessiner le fond en premier
        for layer in reversed(layers):
            layer_type = layer["__type"]

            if layer_type == "Tiles":
                self._render_tile_layer(layer, use_auto=False)

            elif layer_type == "AutoLayer":
                # AutoLayer = LDtk place les tiles automatiquement selon des règles
                self._render_tile_layer(layer, use_auto=True)

            elif layer_type == "IntGrid":
                # IntGrid = grille de valeurs entières, on s'en sert pour les collisions
                self._parse_intgrid_layer(layer)
                # Un IntGrid peut aussi avoir des tiles auto générées par-dessus
                if layer.get("autoLayerTiles"):
                    self._render_tile_layer(layer, use_auto=True)

            elif layer_type == "Entities":
                self._parse_entities_layer(layer)

    # Cette fonction dessine les bonnes tiles au bon endroit
    def _render_tile_layer(self, layer: dict, use_auto: bool = False):
        tileset_uid = layer.get("__tilesetDefUid")
        if tileset_uid is None or tileset_uid not in self.tilesets:
            return

        tileset = self.tilesets[tileset_uid]
        grid_size = layer["__gridSize"]
        # Taille d'une tile après zoom (minimum 1px pour éviter les erreurs)
        grid_size_scaled = max(1, int(grid_size * self.scale))

        # autoLayerTiles pour les layers auto, gridTiles pour les layers manuels
        tiles = None
        if use_auto:
            tiles = layer.get("autoLayerTiles", []) 
        else:
            tiles = layer.get("gridTiles", [])

        for tile in tiles:
            px = tile["px"]   # Position de la tile dans le monde (avant zoom)
            src = tile["src"] # Position du sprite dans le tileset (spritesheet)
            f = tile.get("f", 0)  # Flags de flip: bit 0 = horizontal, bit 1 = vertical

            # On découpe le bon morceau dans la spritesheet
            src_rect = pygame.Rect(src[0], src[1], grid_size, grid_size)
            # Sécurité : on vérifie que le morceau demandé existe bien dans l'image
            if not tileset.get_rect().contains(src_rect):
                continue

            tile_surf = tileset.subsurface(src_rect).copy()

            # On redimensionne la tile selon le zoom
            tile_surf = pygame.transform.scale(tile_surf, (grid_size_scaled, grid_size_scaled))

            # Position finale dans le monde après zoom
            dest_x = int(px[0] * self.scale)
            dest_y = int(px[1] * self.scale)

            self.render_surface.blit(tile_surf, (dest_x, dest_y))

    # IntGrid est utilisé pour les collisions donc on crée des rects de collision ici
    def _parse_intgrid_layer(self, layer: dict):
        grid_size = layer["__gridSize"]
        c_width = layer["__cWid"]  # Largeur de la grille en nombre de cellules
        offset_x = layer.get("__pxTotalOffsetX", 0)
        offset_y = layer.get("__pxTotalOffsetY", 0)

        # intGridCsv = toutes les cellules à plat dans une liste, ligne par ligne
        # L'index i nous permet de retrouver col/row avec un simple modulo/division
        csv = layer.get("intGridCsv", [])
        for i, value in enumerate(csv):
            if value == 0:
                continue  # 0 = vide, on skip
            col = i % c_width
            row = i // c_width

            # On crée un rect de collision en appliquant le zoom + l'offset du layer
            rect = pygame.Rect(
                int((col * grid_size + offset_x) * self.scale),
                int((row * grid_size + offset_y) * self.scale),
                int(grid_size * self.scale),
                int(grid_size * self.scale)
            )
            self.colliders.append(rect)

    def _parse_entities_layer(self, layer: dict):
        for entity in layer.get("entityInstances", []):
            identifier = entity["__identifier"]
            px = entity["px"]
            if identifier == "PlayerSpawn":
                self.spawn_point = (float(px[0]) * self.scale, float(px[1]) * self.scale)
            elif identifier == "Door":
                dest_iid = None
                dest_level_iid = None
                for field in entity.get("fieldInstances", []):
                    if field["__identifier"] == "Entity_ref" and field["__value"]:
                        dest_iid = field["__value"].get("entityIid")
                        dest_level_iid = field["__value"].get("levelIid")
                self.doors.append({
                    "iid": entity["iid"],
                    "rect": pygame.Rect(
                        int((px[0] - entity["width"] / 2) * self.scale),
                        int(px[1] * self.scale),
                        int(entity["width"] * self.scale),
                        int(entity["height"] * self.scale),
                    ),
                    "dest_entity_iid": dest_iid,
                    "dest_level_iid": dest_level_iid,
                })
            elif identifier == "JEAN_EUD":
                self.enemy_spawns.append({
                    "x": float(px[0]) * self.scale,
                    "y": float(px[1]) * self.scale,
                })

    def get_enemy_spawns(self) -> List[dict]:
        return self.enemy_spawns

    def get_colliders(self) -> List[pygame.Rect]:
        return self.colliders

    def get_spawn_point(self) -> Tuple[float, float]:
        return self.spawn_point
    
    def get_doors(self) -> List[dict]:
        return self.doors

    def draw(self, surface: pygame.Surface, offset: Tuple[float, float] = (0, 0)):
        if self.render_surface:
            surface.blit(self.render_surface, offset)