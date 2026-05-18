import pygame
from settings import *
from entities.player import Player
from world.tilemap import TileMap
from network.network_manager import NetworkMode, NetworkServer, NetworkClient, PlayerState
from typing import Dict, Optional
from entities.enemy_jeaneude import JeanEude
from core.save_manager import SaveManager

class PauseMenu:
    RESOLUTIONS = [
        (960, 480),
        (1280, 640),
        (1600, 800),
        (1920, 960),
        None,  # None = plein ecran
    ]

    def __init__(self):
        self.main_options = ["Reprendre", "Changer la resolution", "Debug info", "Colliders", "Nametags", "Volume musique", "Quitter"]
        self.selected = 0
        self.show_resolutions = False
        self.music_volume = 1.0
        self.selected_res = 3 # 1920x960 par defaut parceque pourquoi pas

    def reset(self):
        self.selected = 0
        self.show_resolutions = False

    def handle_event(self, event):
        # Retourne "resume", "quit", ("resolution", w, h), ou None
        if event.type != pygame.KEYDOWN:
            return None

        if not self.show_resolutions:
            if event.key == pygame.K_ESCAPE:
                return "resume"
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.main_options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.main_options)
            elif event.key == pygame.K_LEFT:
                if self.selected == 5:
                    self.music_volume = max(0.0, self.music_volume - 0.1)
                    pygame.mixer.music.set_volume(self.music_volume)
            elif event.key == pygame.K_RIGHT:
                if self.selected == 5:
                    self.music_volume = min(1.0, self.music_volume + 0.1)
                    pygame.mixer.music.set_volume(self.music_volume)
            elif event.key == pygame.K_RETURN:
                if self.selected == 0:
                    return "resume"
                elif self.selected == 1:
                    self.show_resolutions = True
                elif self.selected == 2:
                    return "toggle_debug"
                elif self.selected == 3:
                    return "toggle_colliders"
                elif self.selected == 4:
                    return "toggle_nametags"
                elif self.selected == 6:
                    return "quit"
        else:
            if event.key == pygame.K_ESCAPE:
                self.show_resolutions = False
            elif event.key in (pygame.K_UP,):
                self.selected_res = (self.selected_res - 1) % len(self.RESOLUTIONS)
            elif event.key in (pygame.K_DOWN,):
                self.selected_res = (self.selected_res + 1) % len(self.RESOLUTIONS)
            elif event.key == pygame.K_RETURN:
                self.show_resolutions = False
                res = self.RESOLUTIONS[self.selected_res]
                if res is None:
                    return "fullscreen"
                w, h = res
                return ("resolution", w, h)

        return None

    def draw(self, screen, show_debug, show_colliders, show_nametags):
        sw = screen.get_width()
        sh = screen.get_height()
        scale = min(sw / WINDOW_WIDTH, sh / WINDOW_HEIGHT)

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        cx = sw // 2
        cy = sh // 2

        font_title = pygame.font.Font(None, max(16, int(80 * scale)))
        font_option = pygame.font.Font(None, max(12, int(50 * scale)))

        title = font_title.render("MENU", True, WHITE)
        screen.blit(title, title.get_rect(center=(cx, cy - int(150 * scale))))

        if not self.show_resolutions:
            for i, opt in enumerate(self.main_options):
                color = YELLOW
                if i != self.selected:
                    color = WHITE
                if i == 2:
                    if show_debug:
                        label = "Debug info : ON"
                    else:
                        label = "Debug info : OFF"
                elif i == 3:
                    if show_colliders:
                        label = "Colliders : ON"
                    else:
                        label = "Colliders : OFF"
                elif i == 4:
                    if show_nametags:
                        label = "Nametags : ON"
                    else:
                        label = "Nametags : OFF"
                elif i == 5:
                    label = f"Volume musique : {int(self.music_volume * 100)}%"
                else:
                    label = opt
                text = font_option.render(label, True, color)
                screen.blit(text, text.get_rect(center=(cx, cy + int((-40 + i * 60) * scale))))
        else:
            title2 = font_option.render("Choisir une resolution :", True, WHITE)
            screen.blit(title2, title2.get_rect(center=(cx, cy - int(80 * scale))))
            for i, res in enumerate(self.RESOLUTIONS):
                color = YELLOW
                if i != self.selected_res:
                    color = WHITE
                label = f"{res[0]} x {res[1]}" if res is not None else "Plein ecran"
                text = font_option.render(label, True, color)
                screen.blit(text, text.get_rect(center=(cx, cy + int((-20 + i * 55) * scale))))


class MultiplayerGame:    
    def __init__(self, screen, network_mode: NetworkMode = NetworkMode.OFFLINE, server_ip: Optional[str] = None):
        # Initialisation du jeu multijouieur
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 16)
        self.font_player_name = pygame.font.Font(None, 22)
        self.running = True
        self.network_mode = network_mode
        

        # Composants Network
        self.server: Optional[NetworkServer] = None
        self.client: Optional[NetworkClient] = None
        self.local_player_id: Optional[int] = None  # Notre propre ID
        self.local_player: Optional[Player] = None  # Notre joueur local
        self.remote_players: Dict[int, Player] = {}  # Les joueurs des autres dictionnaire du type {id: Player}
        
        # World        
        self.tilemap = TileMap(ldtk_path="src/world/world_design.ldtk", level_index=0, scale=2.0)
        self.colliders = self.tilemap.get_colliders()
        self.current_level_index = 0

        # Ennemi Jean-Eude
        self.enemies = self._spawn_enemies_from_map()
        
        # Spawn Point
        self.spawn_x = 200
        self.spawn_y = 200
        
        # Timing Sync
        self.sync_counter = 0

        # Game over
        self.game_over = False
        self.all_players_dead = False
        self.respawn_cooldown = 0

        # Menu pause (au final ça s'appelle pause mais ca fait pas de pause mais tkt)
        self.paused = False
        self.pause_menu = PauseMenu()
        self.show_debug_info = SHOW_DEBUG_INFO
        self.show_colliders = SHOW_COLLIDERS
        self.show_nametags = SHOW_NAMETAGS
        self.is_fullscreen = False
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)

        # Surface de rendu a taille fixe (1920x960), le jeu est toujours rendu a cette resolution, puis scale vers la fenetre reelle (choisie par le joueur dans les params)
        self.game_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

        #sauvegarde
        self.save_manager = SaveManager()
        
        # Network Info Display
        self.connection_status = "Initializing..."
        
        self._initialize_network()

    
    def _initialize_network(self):
        # init du system multi
        if self.network_mode == NetworkMode.SERVER:
            # Mode serveur : on crée un serveur
            self.server = NetworkServer(host='0.0.0.0', port=5555)
            
            if self.server.start():
                self.local_player_id = 0  # Le serveur est toujours le joueur 0
                self.local_player = Player(self.spawn_x, self.spawn_y)
                self.connection_status = "Server running, waiting for clients..."
            else:
                self.connection_status = "Server failed to start!"
        
        elif self.network_mode == NetworkMode.CLIENT:
            # Mode client : sera initialisé par connect_as_client()
            pass
        
        else:  # OFFLINE
            # Mode solo : pas de réseau
            self.local_player_id = 0
            self.local_player = Player(self.spawn_x, self.spawn_y)
            self.connection_status = "Offline mode"
            self.save_manager.load(self)  # charge si une save existe
    
    def connect_as_client(self, server_ip: str) -> bool:
        # Renvoie True si connexion réussie, False sinon
        self.client = NetworkClient(server_ip, port=5555)
        
        if self.client.connect():
            self.local_player_id = -1  # -1 temporaire, le serveur va nous donner notre vrai ID
            self.local_player = Player(self.spawn_x, self.spawn_y)
            self.connection_status = "Connecting to server..."
            return True
        else:
            self.connection_status = f"Failed to connect to {server_ip}"
            return False
    
    
    # Applique un PlayerState (position + animation) a un objet Player remote
    def _apply_state_to_player(self, player: Player, state: PlayerState):
        player.x = state.x
        player.y = state.y
        player.velocity_x = state.velocity_x
        player.velocity_y = state.velocity_y
        player.health = state.health
        player.direction = state.direction
        player.level_index = state.level_index
        player.rect.topleft = (int(player.x), int(player.y))
 
        # Applique l'etat d'animation reçu
        player.dash_active = state.dash_active
        player.is_wall_sliding = state.is_wall_sliding
        player.is_grounded = state.is_grounded
 
        # Choisit le bon sprite selon l'état reçu
        anim = state.anim_state
        frame = state.anim_frame
 
        sprites_map = {
            "running": player.running_sprites,
            "jumping": player.jumping_sprites,
            "falling": player.falling_sprites,
            "dashing": player.dashing_sprites,
            "sliding": player.sliding_sprites,
            "standing": [player.standing_sprite],
        }
        sprite_list = sprites_map.get(anim, [player.standing_sprite])
        safe_frame = frame % len(sprite_list)
        player.sprite = sprite_list[safe_frame]
 
        if player.direction == -1:
            player.image = pygame.transform.flip(player.sprite, True, False)
        else:
            player.image = player.sprite
    
    def _check_server_events(self):
        # On check pour de nouveaux joueurs qui rejoignent/quittent (côté serveur)
        if not self.server:
            return
        
        # Récupère la liste des joueurs qui viennent d'arriver
        new_players = self.server.get_new_players()
        for player_id in new_players:
            print(f"Player {player_id} joined!")
            # +1 car on compte le serveur lui-même
            self.connection_status = f"Players connected: {len(self.server.clients) + 1}"
        
        # Récupère la liste des joueurs qui viennent de partir
        left_players = self.server.get_left_players()
        for player_id in left_players:
            print(f"Player {player_id} left!")
            # Supprime le joueur de notre liste locale
            if player_id in self.remote_players:
                del self.remote_players[player_id]
            self.connection_status = f"Players connected: {len(self.server.clients) + 1}"
    
    def _update_server_players(self):
        # Mets à jour les joueurs (clients) à partir de l'état du serveur (côté serveur)
        if not self.server:
            return
        
        # Récupère les états de tous les joueurs depuis le serveur
        player_states = self.server.get_player_states()
        
        for player_id, state in player_states.items():
            # On skip notre propre joueur, on le gère nous-mêmes
            if player_id == self.local_player_id:
                continue
            
            # Si c'est un nouveau joueur distant, on le crée
            if player_id not in self.remote_players:
                self.remote_players[player_id] = Player(state.x, state.y)
                
            self._apply_state_to_player(self.remote_players[player_id], state)
    
    def _update_client_players(self):
        # Mets à jour les joueurs à partir de l'état du client (côté client)
        if not self.client:
            return
        
        # Vérifie si on s'est fait déconnecter
        if not self.client.is_connected():
            self.connection_status = "Disconnected from server"
            self.running = False
            return
        
        # Si on avait -1 comme ID temporaire et qu'on a reçu notre vrai ID du serveur
        if self.local_player_id == -1 and self.client.player_id is not None:
            self.local_player_id = self.client.player_id
            self.connection_status = "Connected to server!"
        
        # Récupère les états de tous les joueurs distants
        remote_states = self.client.get_remote_player_states()
        
        for player_id, state in remote_states.items():
            # On skip notre propre joueur
            if self.local_player_id is not None and player_id == self.local_player_id:
                continue
            
            # Crée ou met à jour le joueur distant
            if player_id not in self.remote_players:
                self.remote_players[player_id] = Player(state.x, state.y)
                
            self._apply_state_to_player(self.remote_players[player_id], state)
            
    def handle_event(self, event):
        # Events pygame
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type != pygame.KEYDOWN:
            return

        # ESC ouvre le menu pause (si le jeu tourne normalement)
        if event.key == pygame.K_ESCAPE and not self.paused:
            self.paused = True
            self.pause_menu.reset()
            return

        # Quand le menu pause est ouvert on lui envoie les events
        if self.paused:
            result = self.pause_menu.handle_event(event)
            if result == "resume":
                self.paused = False
            elif result == "quit":
                self.running = False
            elif result is not None and result[0] == "resolution":
                _, w, h = result
                self.windowed_size = (w, h)
                self.is_fullscreen = False
                self.screen = pygame.display.set_mode((w, h))
            elif result == "fullscreen":
                if self.is_fullscreen:
                    self.screen = pygame.display.set_mode(self.windowed_size)
                    self.is_fullscreen = False
                else:
                    self.windowed_size = (self.screen.get_width(), self.screen.get_height())
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    self.is_fullscreen = True
            elif result == "toggle_debug":
                self.show_debug_info = not self.show_debug_info
            elif result == "toggle_colliders":
                self.show_colliders = not self.show_colliders
            elif result == "toggle_nametags":
                self.show_nametags = not self.show_nametags
            return

        # Events normaux du jeu (seulement quand non pause)
        if event.key == pygame.K_r:
            if self.game_over and (self.respawn_cooldown <= 0 or self.all_players_dead):
                self._restart_game()
            elif self.local_player:
                self.local_player.reset_position(self.spawn_x, self.spawn_y)
        elif event.key == pygame.K_F5:
            self.save_manager.save(self)   #sauvegarde manuelle
        elif event.key == pygame.K_F9:
            self.save_manager.load(self)   #chargement manuel
    
    def handle_input(self):
        # Inputs clavier (bloque les inputs joueur quand le menu pause est ouvert)
        if self.paused:
            return
        if self.local_player:
            keys = pygame.key.get_pressed()
            self.local_player.handle_input(keys)
    
    def update(self, dt: float):
        # Logique d'update de la syncrho

        # Vérifie si le joueur est mort
        if self.local_player and self.local_player.health <= 0 and not self.game_over:
            self.game_over = True
            if self.network_mode != NetworkMode.OFFLINE:
                self.respawn_cooldown = RESPAWN_COOLDOWN

        if self.game_over and self.respawn_cooldown > 0:
            self.respawn_cooldown -= 1

        # Vérifie si tous les joueurs sont morts (multi seulement)
        if self.game_over and self.remote_players and not self.all_players_dead:
            if all(p.health <= 0 for p in self.remote_players.values()):
                self.all_players_dead = True

        if not self.game_over:
            # Met à jour notre joueur local
            if self.local_player:
                self.local_player.update(dt, self.colliders)

            # Check attaque du joueur vs ennemis (une seule fois par attaque)
            if self.local_player:
                attack_rect = self.local_player.get_attack_rect()
                if attack_rect:
                    for i, enemy in enumerate(self.enemies):
                        if not enemy.is_dead and enemy not in self.local_player.attack_hit_enemies:
                            if attack_rect.colliderect(enemy.get_rect()):
                                self.local_player.attack_hit_enemies.append(enemy)
                                if self.client:
                                    # Client : on envoie l'attaque au serveur, lui applique les dégâts
                                    self.client.send_attack(i, PLAYER_ATTACK_DAMAGE)
                                else:
                                    # Offline ou serveur : on applique directement
                                    enemy.take_damage(PLAYER_ATTACK_DAMAGE)

            self._check_door_transitions()

        # Passe tous les joueurs visibles aux ennemis pour la détection
        all_players = []
        if self.local_player:
            all_players.append(self.local_player)
        for p in self.remote_players.values():
            if p.level_index == self.current_level_index:
                all_players.append(p)

        # Met à jour l'ennemi Jean-Eude
        for enemy in self.enemies:
            enemy.update(dt, self.colliders, all_players)

        # Serveur : applique les attaques reçues des clients
        if self.server:
            for attack in self.server.get_pending_attacks():
                idx = attack.get('enemy_index', -1)
                dmg = attack.get('damage', 0)
                if 0 <= idx < len(self.enemies):
                    self.enemies[idx].take_damage(dmg)

        # Vérifie les événements réseau et met à jour les joueurs distants
        if self.server:
            self._check_server_events()  # Check qui a rejoint/quitté
            self._update_server_players()  # Met à jour les positions des autres
        elif self.client:
            self._update_client_players()  # Met à jour les positions depuis le serveur
            # Applique les états des ennemis reçus du serveur
            enemy_states = self.client.get_enemy_states()
            if enemy_states:
                for state in enemy_states:
                    idx = state.get('index', -1)
                    if 0 <= idx < len(self.enemies):
                        self.enemies[idx].apply_net_state(state)

        # Synchronisation réseau, on envoie pas à chaque frame pour économiser la bande passante
        self.sync_counter += 1
        if self.sync_counter >= NETWORK_SYNC_INTERVAL:
            self.sync_counter = 0
            self._sync_network()  # Envoie notre état sur le réseau

        if self.network_mode == NetworkMode.OFFLINE:
            self.save_manager.update(self, dt)  # autosave + playtime

    
    def _sync_network(self):
        # Envoie l'état du joueur local sur le réseau
        if not self.local_player:
            return
        
        # Crée un objet PlayerState avec notre état actuel
        local_state = PlayerState(
            player_id=self.local_player_id or 0,
            x=self.local_player.x,
            y=self.local_player.y
        )
        local_state.velocity_x = self.local_player.velocity_x
        local_state.velocity_y = self.local_player.velocity_y
        local_state.health = self.local_player.health
        local_state.direction = self.local_player.direction
        local_state.level_index = self.current_level_index
        
        local_state.anim_state = self.local_player.current_anim_state
        local_state.anim_frame = self.local_player.current_sprite_index
        local_state.is_grounded = self.local_player.is_grounded
        local_state.dash_active = self.local_player.dash_active
        local_state.is_wall_sliding = self.local_player.is_wall_sliding
        
        if self.server:
            # Si on est serveur : on met à jour notre propre état et on broadcast à tous
            if self.local_player_id is not None:
                self.server.player_states[self.local_player_id] = local_state
            
            
            # Collecte les états des ennemis pour la synchro
            enemy_states = []

            for index, enemy in enumerate(self.enemies):
                current_state = enemy.get_net_state()
                new_state_dict = {"index": index}
                new_state_dict.update(current_state)
                enemy_states.append(new_state_dict)                

            self.server.broadcast_state(enemy_states=enemy_states)  # Envoie à tous les clients
        
        elif self.client:
            # Si on est client : on envoie juste notre état au serveur
            self.client.send_state(local_state)
            
    def _spawn_enemies_from_map(self) -> list:
        enemies = []
        for spawn in self.tilemap.get_enemy_spawns():
            enemies.append(JeanEude(x=spawn["x"], y=spawn["y"], patrol_range=150))
        return enemies
            
    def _check_door_transitions(self):
        # Vérifie si le joueur touche une porte et change de niveau
        if not self.local_player:
            return

        player_rect = self.local_player.get_rect()

        for door in self.tilemap.get_doors():
            if not player_rect.colliderect(door["rect"]):
                continue

            dest_iid = door["dest_entity_iid"]
            dest_level_iid = door["dest_level_iid"]

            if dest_iid is None or dest_level_iid is None:
                continue

            # Trouve l'index du niveau cible
            level_index = self.tilemap.get_level_index_by_iid(dest_level_iid)
            if level_index == -1:
                print(f"Niveau introuvable pour iid {dest_level_iid}")
                return

            # Charge le nouveau niveau
            self.tilemap.load_level(level_index)
            self.colliders = self.tilemap.get_colliders()
            self.enemies = self._spawn_enemies_from_map()
            self.current_level_index = level_index
            self.local_player.level_index = level_index

            self.local_player.velocity_x = 0
            self.local_player.velocity_y = 0

            # Positionne le joueur a la porte d'arrivee
            dest_pos = self.tilemap.find_door_position(dest_iid)
            if dest_pos:
                door_x, door_y = dest_pos
                level_width = self.tilemap.width
                level_height = self.tilemap.height
                source_rect = door["rect"]

                if source_rect.width > source_rect.height:
                    # porte large (porte verticale)

                    # Decale verticalement si la porte est sur un bord haut/bas
                    if door_y < 50:
                        spawn_y = door_y + 80
                        self.local_player.reset_position(door_x, spawn_y)
                    elif door_y > level_height - 50:
                        spawn_y = door_y - 80
                        self.local_player.reset_position(door_x, spawn_y)
                        self.local_player.velocity_y = PLAYER_JUMP_FORCE
                    else:
                        spawn_y = door_y + 80
                        self.local_player.reset_position(door_x, spawn_y)
                else:
                    # porte haute (porte horizontale)
                    y_offset = self.local_player.y - source_rect.y
                    spawn_y = door_y + y_offset

                    # Decale horizontalement si la porte est sur un bord gauche/droit
                    if door_x < 50:
                        spawn_x = door_x + 80
                    elif door_x > level_width - 50:
                        spawn_x = door_x - 80
                    else:
                        spawn_x = door_x

                    self.local_player.reset_position(spawn_x, spawn_y)
            else:
                spawn = self.tilemap.get_spawn_point()
                self.local_player.reset_position(spawn[0], spawn[1])

            print(f"Transition vers niveau {level_index}")
            return
    
    def check_global_collisions(self):
        # Check les collisions globales (pas encore implementé TODO)
        pass

    def _draw_player_name(self, player, player_id):
        name = f"Player {player_id + 1}"
        label = self.font_player_name.render(name, True, WHITE)
        x = int(player.x + PLAYER_WIDTH // 2)
        y = int(player.y + PLAYER_HEIGHT + 6)
        self.game_surface.blit(label, label.get_rect(center=(x, y)))
    
    def _draw_game_over(self):
        # Ecran de fin quand le joueur est mort
        cx = self.game_surface.get_width() // 2
        cy = self.game_surface.get_height() // 2
        self.game_surface.fill(BLACK)
        font_big = pygame.font.Font(None, 120)
        font_small = pygame.font.Font(None, 40)
        text = font_big.render("GAME OVER", True, RED)
        self.game_surface.blit(text, text.get_rect(center=(cx, cy - 60)))
        if self.respawn_cooldown > 0:
            secondes = (self.respawn_cooldown + 59) // 60
            sub = font_small.render(f"Reapparition dans {secondes} secondes...", True, GRAY)
        else:
            sub = font_small.render("R pour reapparaitre", True, WHITE)
        self.game_surface.blit(sub, sub.get_rect(center=(cx, cy + 40)))

    def _draw_all_dead(self):
        # Ecran special quand tous les joueurs sont morts en multi
        cx = self.game_surface.get_width() // 2
        cy = self.game_surface.get_height() // 2
        self.game_surface.fill((20, 0, 0))
        font_big = pygame.font.Font(None, 100)
        font_small = pygame.font.Font(None, 40)
        text = font_big.render("DEFAITE TOTALE", True, (200, 50, 50))
        self.game_surface.blit(text, text.get_rect(center=(cx, cy - 80)))
        sub1 = font_small.render("Tous les joueurs sont morts (vous êtes peut-être pas fait pour ça).", True, WHITE)
        self.game_surface.blit(sub1, sub1.get_rect(center=(cx, cy + 10)))
        sub2 = font_small.render("R pour recommencer", True, GRAY)
        self.game_surface.blit(sub2, sub2.get_rect(center=(cx, cy + 55)))

    def _restart_game(self):
        # Remet le jeu a zero apres game over
        self.game_over = False
        all_dead = self.all_players_dead
        self.all_players_dead = False
        self.respawn_cooldown = 0

        # Recharge la zone de depart pour eviter de spawner dans un mur ;-;
        self.tilemap.load_level(0)
        self.colliders = self.tilemap.get_colliders()
        self.current_level_index = 0

        if self.local_player:
            self.local_player.level_index = 0
            self.local_player.reset_position(self.spawn_x, self.spawn_y)
            self.local_player.health = PLAYER_MAX_HEALTH
        # Respawn les ennemis en offline ou si tout le monde est mort en multi
        if self.network_mode == NetworkMode.OFFLINE or all_dead:
            self.enemies = self._spawn_enemies_from_map()

    def draw(self):
        # Rendu graphique du jeu vers game_surface (resolution fixe 1920x960)
        if self.all_players_dead:
            self._draw_all_dead()
        elif self.game_over:
            self._draw_game_over()
        else:
            # Background
            self.game_surface.fill(BLACK)

            # Dessine la carte
            self.tilemap.draw(self.game_surface, offset=(0, 0))

            if self.show_colliders:
                for door in self.tilemap.get_doors():
                    pygame.draw.rect(self.game_surface, (0, 200, 255), door["rect"], 2)

            # Dessine notre joueur local
            if self.local_player:
                self.local_player.draw(self.game_surface, offset=(0, 0), show_colliders=self.show_colliders)
                # Dessine le pseudo en dessous du joueur si en multi
                if self.network_mode != NetworkMode.OFFLINE:
                    if self.local_player_id is not None and self.local_player_id >= 0:
                        if self.show_nametags:
                            self._draw_player_name(self.local_player, self.local_player_id or 0)

            # Dessine les joueurs distants (seulement si ils sont vivants)
            for player_id, player in self.remote_players.items():
                if player.level_index == self.current_level_index and player.health > 0:
                    player.draw(self.game_surface, offset=(0, 0), show_colliders=self.show_colliders)
                    if self.show_nametags:
                        self._draw_player_name(player, player_id)

            # Dessine les ennemis Jean-Eude
            for enemy in self.enemies:
                enemy.draw(self.game_surface, offset=(0, 0), show_colliders=self.show_colliders)

            # Dessine les infos de debug
            if self.show_debug_info:
                self._draw_debug_info()

            # Dessine le HUD (seulement barre de vie pour le moment )
            self._draw_hud()

        # Scale game_surface en conservant le ratio (letterbox si necessaire, cad avec les bandes noires sinon le jeu est déformé)
        game_w = self.game_surface.get_width()
        game_h = self.game_surface.get_height()
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        scale = min(screen_w / game_w, screen_h / game_h)
        scaled_w = int(game_w * scale)
        scaled_h = int(game_h * scale)
        offset_x = (screen_w - scaled_w) // 2
        offset_y = (screen_h - scaled_h) // 2
        scaled = pygame.transform.scale(self.game_surface, (scaled_w, scaled_h))
        self.screen.fill(BLACK)
        self.screen.blit(scaled, (offset_x, offset_y))

        # Dessine le menu pause par dessus (en coordonnees ecran, pas game_surface)
        if self.paused:
            self.pause_menu.draw(self.screen, self.show_debug_info, self.show_colliders, self.show_nametags)

        pygame.display.flip()
    
    def _draw_hud(self):
        if not self.local_player:
            return

        bar_x = 20
        bar_y = self.game_surface.get_height() - 45
        bar_w = 200
        bar_h = 20

        ratio = max(0, self.local_player.health / PLAYER_MAX_HEALTH)

        # Couleur selon le niveau de vie en rgb
        if ratio > 0.6:
            bar_color = (60, 200, 60)
        elif ratio > 0.3:
            bar_color = (220, 180, 0)
        else:
            bar_color = (200, 40, 40)

        # Fond de la barre
        pygame.draw.rect(self.game_surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        # Remplissage
        pygame.draw.rect(self.game_surface, bar_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        # Bordure
        pygame.draw.rect(self.game_surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

        font = pygame.font.Font(None, 22)
        label = font.render(f"PV {self.local_player.health} / {PLAYER_MAX_HEALTH}", True, WHITE)
        self.game_surface.blit(label, (bar_x, bar_y - 18))

    def _draw_debug_info(self):
        # Affiche les infos de debug sur l'écran
        
        if not self.local_player:
            return
        
        state = self.local_player.get_state()
        
        debug_texts = [
            f"Mode: {self.network_mode.value.upper()}",
            f"Status: {self.connection_status}",
            f"Remote Players: {len(self.remote_players)}",
            f"ID: {self.local_player_id}",
            f"FPS: {int(self.clock.get_fps())}",
            f"Position: ({state['position'][0]:.1f}, {state['position'][1]:.1f})",
            f"Velocity: ({state['velocity'][0]:.2f}, {state['velocity'][1]:.2f})",
            f"Health: {state['health']}",
            f"WL: {state['is_walled_left']}",
            f"WR: {state['is_walled_right']}",
            f"Grounded: {state['is_grounded']}",
        ]
        
        for i, text in enumerate(debug_texts):
            surf = self.font.render(text, True, WHITE)
            self.game_surface.blit(surf, (10, 10 + i * 20))
    
    def run(self):
        # Boucle principale du jeu
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.handle_input()
            self.update(1 / FPS)
            self.check_global_collisions()
            self.draw()
            
            self.clock.tick(FPS)
        
        # Nettoyage à la fin, ferme les connexions proprement
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()