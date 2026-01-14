import pygame
from settings import *
from entities.player import Player
from world.tilemap import TileMap
from network.network_manager import NetworkMode, NetworkServer, NetworkClient, PlayerState
from typing import Dict, Optional


class MultiplayerGame:    
    def __init__(self, screen, network_mode: NetworkMode = NetworkMode.OFFLINE, 
                 server_ip: Optional[str] = None):
        # Initialisation du jeu multijouieur
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 16)
        self.running = True
        self.network_mode = network_mode
        
        # Composants Network
        self.server: Optional[NetworkServer] = None
        self.client: Optional[NetworkClient] = None
        self.local_player_id: Optional[int] = None  # Notre propre ID
        self.local_player: Optional[Player] = None  # Notre joueur local
        self.remote_players: Dict[int, Player] = {}  # Les joueurs des autres dictionnaire du type {id: Player}
        
        # World
        self.tilemap = TileMap()
        self.colliders = self.tilemap.get_colliders()
        
        # Spawn Point
        self.spawn_x = 100
        self.spawn_y = 100
        
        # Timing Sync 
        self.sync_counter = 0
        self.sync_interval = 3  # On envoie notre état toutes les 3 frames (~50ms à 60 FPS)
        
        # Network Info Display
        self.connection_status = "Initializing..."
        
        self._initialize_network()
    
    def _initialize_network(self):
        """Initialize network based on mode"""
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
            
            # Met à jour la position et l'état du joueur distant
            remote_player = self.remote_players[player_id] # ceci est une référence donc si on modifie remote_player ça modifie le self.remove_players
            remote_player.x = state.x
            remote_player.y = state.y
            remote_player.velocity_x = state.velocity_x
            remote_player.velocity_y = state.velocity_y
            remote_player.health = state.health
            remote_player.direction = state.direction
            # Met à jour le rect pour l'affichage
            remote_player.rect.topleft = (int(remote_player.x), int(remote_player.y))
    
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
            
            remote_player = self.remote_players[player_id] # ceci est une référence donc si on modifie remote_player ça modifie le self.remove_players
            remote_player.x = state.x
            remote_player.y = state.y
            remote_player.velocity_x = state.velocity_x
            remote_player.velocity_y = state.velocity_y
            remote_player.health = state.health
            remote_player.direction = state.direction
            remote_player.rect.topleft = (int(remote_player.x), int(remote_player.y))
    
    def handle_event(self, event):
        # Events pygame
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_r:
                # Reset la position du joueur au spawn
                if self.local_player:
                    self.local_player.reset_position(self.spawn_x, self.spawn_y)
    
    def handle_input(self):
        # Inputs clavier
        if self.local_player:
            keys = pygame.key.get_pressed()
            self.local_player.handle_input(keys)
    
    def update(self, dt: float):
        # Logique d'update de la syncrho
        
        # Met à jour notre joueur local
        if self.local_player:
            self.local_player.update(dt, self.colliders)
        
        # Vérifie les événements réseau et met à jour les joueurs distants
        if self.server:
            self._check_server_events()  # Check qui a rejoint/quitté
            self._update_server_players()  # Met à jour les positions des autres
        elif self.client:
            self._update_client_players()  # Met à jour les positions depuis le serveur
        
        # Synchronisation réseau, on envoie pas à chaque frame pour économiser la bande passante
        self.sync_counter += 1
        if self.sync_counter >= self.sync_interval:
            self.sync_counter = 0
            self._sync_network()  # Envoie notre état sur le réseau
    
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
        
        if self.server:
            # Si on est serveur : on met à jour notre propre état et on broadcast à tous
            if self.local_player_id is not None:
                self.server.player_states[self.local_player_id] = local_state
            self.server.broadcast_state()  # Envoie à tous les clients
        
        elif self.client:
            # Si on est client : on envoie juste notre état au serveur
            self.client.send_state(local_state)
    
    def check_global_collisions(self):
        # Check les collisions globales (pas encore implementé TODO)
        pass
    
    def draw(self):
        # Rendu graphique du jeu
        
        # Background
        self.screen.fill(BLACK)
        
        # Dessine la carte
        self.tilemap.draw(self.screen, offset=(0, 0))
        
        # Dessine notre joueur local
        if self.local_player:
            self.local_player.draw(self.screen, offset=(0, 0))
        
        # Dessine les joueurs distants en cyan pour les distinguer
        for player_id, player in self.remote_players.items():
            player.draw(self.screen, offset=(0, 0))
        
        # Dessine les infos de debug
        self._draw_debug_info()
        
        pygame.display.flip()
    
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
            f"Grounded: {state['is_grounded']}",
        ]
        
        for i, text in enumerate(debug_texts):
            surf = self.font.render(text, True, WHITE)
            self.screen.blit(surf, (10, 10 + i * 20))
    
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