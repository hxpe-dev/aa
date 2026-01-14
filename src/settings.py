import os

# Dimensions de la fenêtre
WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 800
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

# Physique du jeu
GRAVITY = 0.8
TERMINAL_VELOCITY = 15

# Paramètres du joueur - Mouvement
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 56
PLAYER_SPEED = 7  # Vitesse de marche horizontale
PLAYER_ACCELERATION = 0.5  # Accélération horizontale
PLAYER_DECELERATION = 0.6  # Décélération horizontale
PLAYER_JUMP_FORCE = -12  # Force du saut (négative = vers le haut)
PLAYER_FALL_ACCELERATION = 0.6  # Accélération de chute
PLAYER_MAX_FALL_SPEED = 16  # Vitesse max de chute
PLAYER_COYOTE_TIME = 6  # frames après quitter le sol pour pouvoir sauter
PLAYER_JUMP_BUFFER_TIME = 4  # frames avant atterrissage pour enregistrer le saut
PLAYER_DOUBLE_JUMP_ENABLED = True  # Double saut
PLAYER_DASH_SPEED = 18
PLAYER_DASH_DURATION = 12  # frames
PLAYER_DASH_COOLDOWN = 50  # frames
PLAYER_MAX_HEALTH = 100

# Paramètres des ennemis
ENEMY_SPEED = 2
ENEMY_PATROL_DISTANCE = 100
ENEMY_AGGRO_RANGE = 200

# Taille des tiles (pour tilemap)
TILE_SIZE = 32

# Chemins vers les assets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')

# Animation
ANIMATION_SPEED = 0.15  # Vitesse par défaut des animations

# Camera
CAMERA_SMOOTHING = 0.1  # Plus c'est petit, plus c'est smooth

# Debug
DEBUG_MODE = True
SHOW_HITBOXES = False
SHOW_FPS = True