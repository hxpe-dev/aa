# Abyssal Ascension


## Structure du projet SVP SUIVEZ LA QU'ON COMPRENNE QUELQUE CHOSE LA TEAM

```bash
aa/
│
├── src/
│   ├── launcher.py # Point d’entrée. Initialise pygame, charge le jeu et lance la boucle principale
│   │
│   ├── settings.py # Toutes les constantes du jeu : tailles, FPS, couleurs, chemins vers assets, vitesses, gravité
│   │
│   ├── core/
│   │   ├── game.py # Classe principale : met à jour la scène active, gère les inputs, collisions globales
│   │   │
│   │   ├── scene.py # Classe mère de toutes les scènes (menu, niveaux…), avec update() et draw()
│   │   │
│   │   ├── camera.py # Caméra qui suit le joueur. Décale l’affichage du level et des entités
│   │   │
│   │   └── utils.py # Fonctions utilitaires : chargement d’images, debug messages, helpers généraux
│   │
│   ├── world/
│   │   ├── tilemap.py # Gestion des maps de niveaux: chargement Tiled / CSV / JSON + collisions
│   │   │
│   │   ├── tiles.py # Définition des types de tiles (sol, plateformes, décor…)
│   │   │
│   │   └── level.py # Classe Level : contient les tiles, entités du niveau, triggers, zones.
│   │
│   ├── entities/
│   │   ├── base_entity.py # Classe mère pour Player / Enemy : position, vitesse, gravité, collisions
│   │   │
│   │   ├── player.py # Joueur : déplacements, jump, attaques, animation states, etc
│   │   │
│   │   ├── enemy.py # Ennemis : IA simple, patrouille, agro, attaques
│   │   │
│   │   ├── boss.py # Boss : patterns, phases, gestion avancée
│   │   │
│   │   └── projectiles.py # (?) Projectiles : coups, sorts, particules interactives.
│   │
│   ├── animation/
│   │   ├── sprite_sheet.py # Extraction d’animations depuis des spritesheets
│   │   │
│   │   └── animator.py # Système d’animation : états, cadence, changement auto, transitions
│   │
│   ├── scenes/
│   │   ├── menu.py # Menu principal : boutons start, options, quit. (pour l'instant directement implémenté dans launcher.py)
│   │   │
│   │   ├── loading_screen.py # Écran de chargement si besoin
│   │   │
│   │   ├── level_scene.py # Scène principale du gameplay. Contient un Level et le Player. (pour l'instant directement implémenté dans game.py)
│   │   │
│   │   └── pause.py # Menu pause : reprise, options, quitter.
│   │
│   ├── server/
│   │   ├── server_main.py
│   │   ├── game_state.py
│   │   └── protocol.py
│   │
│   ├── ui/
│   │   ├── health_bar.py # Barre de vie du joueur et des boss.
│   │   │
│   │   └── button.py # Boutons GRR c'est transparent
│   │
│   ├── effects/
│   │   ├── particles.py # Effets visuels (poussière, sang, éclairs, dash trail).
│   │   │
│   │   └── screenshake.py # Effet de screenshake (important pour l’impact des coups).
│   │
│   └── assets/
│       ├── player/ # Spritesheets joueurs
│       │
│       ├── sounds/ # Bruitages + SFX : ost, impacts, dash, ennemis...
│       │
│       └── fonts/ # Polices d'écriture du jeu
│
├── requirements.txt # Dépendances : pygame, pytmx (si Tiled), json, etc.
│
├── README.md
└── .gitignore
```