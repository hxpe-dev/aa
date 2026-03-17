import json
import os
from datetime import datetime
from settings import *


class SaveManager:
    def __init__(self):
        os.makedirs(SAVE_DIR, exist_ok=True)  # crée le dossier saves/ si besoin
        self.autosave_counter = 0
        self.playtime = 0  # en secondes

    def build_save_data(self, game) -> dict:
        # Construit le dictionnaire à sauvegarder depuis l'état du jeu
        player = game.local_player
        return {
            "player": {
                "x": player.x,
                "y": player.y,
                "health": player.health,
            },
            #"level": {
            #    "index": game.tilemap.level_index,  # adapte selon ton TileMap
            #},
            "meta": {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "playtime_seconds": int(self.playtime),
            }
        }

    def save(self, game):
        data = self.build_save_data(game)
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Sauvegarde effectuée à {data['meta']['timestamp']}")

    def load(self, game):
        if not os.path.exists(SAVE_FILE):
            print("Aucune sauvegarde trouvée.")
            return False

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Restaure l'état du joueur
        p = data["player"]
        game.local_player.reset_position(p["x"], p["y"])
        game.local_player.health = p["health"]

        self.playtime = data["meta"].get("playtime_seconds", 0)
        print(f"Sauvegarde chargée ({data['meta']['timestamp']})")
        return True

    def update(self, game, dt: float):
        # À appeler chaque frame dans game.update()
        self.playtime += dt
        self.autosave_counter += 1
        if self.autosave_counter >= AUTOSAVE_INTERVAL:
            self.autosave_counter = 0
            self.save(game)