import os

# Dimensions de la fenêtre
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 960
FPS = 60

# Couleurs (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

# Paramètres du joueur - Mouvement
PLAYER_WIDTH = 35
PLAYER_HEIGHT = 75
PLAYER_SPEED = 7  # Vitesse de marche horizontale
PLAYER_ACCELERATION = 0.5  # Accélération horizontale
PLAYER_DECELERATION = 0.6  # Décélération horizontale
PLAYER_JUMP_FORCE = -12  # Force du saut (négative = vers le haut)
PLAYER_FALL_ACCELERATION = 0.6  # Accélération de chute (alias gravité)
PLAYER_MAX_FALL_SPEED = 16  # Vitesse max de chute
PLAYER_COYOTE_TIME = 6  # frames après quitter le sol pour pouvoir sauter
PLAYER_JUMP_BUFFER_TIME = 4  # frames avant atterrissage pour enregistrer le saut
PLAYER_DOUBLE_JUMP_ENABLED = True  # Double saut
PLAYER_DASH_SPEED = 18
PLAYER_DASH_DURATION = 12  # frames
PLAYER_DASH_COOLDOWN = 50  # frames
PLAYER_MAX_HEALTH = 100
WALL_JUMP_LOCK_DURATION = 10

# Paramètres des ennemis
ENEMY_SPEED = 2
ENEMY_PATROL_DISTANCE = 100
ENEMY_AGGRO_RANGE = 200

# Taille des tiles (pour tilemap grille)
TILE_SIZE = 32

# Debug
SHOW_COLLIDERS = True
