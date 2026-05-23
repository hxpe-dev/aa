import os

# Dimensions de la fenêtre (NE PAS CHANGER)
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
PLAYER_ACCELERATION = 0.4  # Accélération horizontale
PLAYER_DECELERATION = 0.7  # Décélération horizontale
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
PLAYER_WALL_SLIDE_SPEED = 3

# Attaque du joueur
PLAYER_ATTACK_DAMAGE = 20
PLAYER_ATTACK_DURATION = 15
PLAYER_ATTACK_COOLDOWN = 25
PLAYER_ATTACK_RANGE_W = 55
PLAYER_ATTACK_RANGE_H = 60

# Paramètres des ennemis
ENEMY_SPEED = 2
ENEMY_PATROL_DISTANCE = 100
ENEMY_AGGRO_RANGE = 200

# Boss
BOSS_MAX_HEALTH = 500
BOSS_WIDTH = 192
BOSS_HEIGHT = 192
BOSS_WALK_SPEED = 3
BOSS_MELEE_RANGE = 150
BOSS_SLAM_JUMP_FORCE = -22
BOSS_SLAM_FALL_SPEED = 22
BOSS_SHOCKWAVE_DAMAGE = 20
BOSS_SHOCKWAVE_DURATION = 18  # frames
BOSS_SHOCKWAVE_WIDTH = 67
BOSS_SWORD_DAMAGE = 30
BOSS_SWORD_PREP = 35  # frames de preparation avant le coup (pour que le joueur ait le temps de réagir)
BOSS_SWORD_ACTIVE = 12  # frames ou la hitbox existe
BOSS_SWORD_RANGE_W = 120  # largeur de la hitbox épée
BOSS_SWORD_RANGE_H = 80  # hauteur de la hitbox épée

# Vie de Jean-Eude
JEANEUDE_MAX_HEALTH = 50

# Taille des tiles (pour tilemap grille)
TILE_SIZE = 32

# Debug
SHOW_COLLIDERS = False
SHOW_DEBUG_INFO = False
SHOW_NAMETAGS = True

# Paramètres de l'IA de Jean-Eude
JEANEUDE_WIDTH  = 48
JEANEUDE_HEIGHT = 48
JEANEUDE_SPEED  = 2.0   # pixels/frame

# Synchro réseau
NETWORK_SYNC_INTERVAL = 2

RESPAWN_COOLDOWN = 300

# sauvegarde
AUTOSAVE_INTERVAL = 300  # toutes les 300 frames (environ 5 secondes à 60 FPS)


