import json
import os
from datetime import datetime
from settings import *


class SaveManager:
    def __init__(self):
        self.save_dir = os.path.join(os.environ.get("APPDATA", "."), "AbyssalAscension")
        self.save_file = os.path.join(self.save_dir, "save.json")
        os.makedirs(self.save_dir, exist_ok=True)
        self.autosave_counter = 0
        self.playtime = 0

    def build_save_data(self, game) -> dict:
        player = game.local_player
        return {
            "player": {
                "x": player.x,
                "y": player.y,
                "level": player.level_index,
                "health": player.health,
            },
            "meta": {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "playtime_seconds": int(self.playtime),
            }
        }

    def save(self, game):
        data = self.build_save_data(game)
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Sauvegarde effectuée à {data['meta']['timestamp']}")

    def load(self, game):
        if not os.path.exists(self.save_file):
            print("Aucune sauvegarde trouvée.")
            return False

        with open(self.save_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        p = data["player"]
        level_index = p["level"]

        game.tilemap.load_level(level_index)
        game.colliders = game.tilemap.get_colliders()
        game.current_level_index = level_index
        game.enemies = game._spawn_enemies_from_map()

        game.local_player.reset_position(p["x"], p["y"])
        game.local_player.level_index = p["level"]
        game.local_player.health = p["health"]

        self.playtime = data["meta"].get("playtime_seconds", 0)
        print(f"Sauvegarde chargée ({data['meta']['timestamp']})")
        return True

    def update(self, game, dt: float):
        self.playtime += dt
        self.autosave_counter += 1
        if self.autosave_counter >= AUTOSAVE_INTERVAL:
            self.autosave_counter = 0
            self.save(game)