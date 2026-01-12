import socket
import json
import threading
from typing import Optional, Dict
from enum import Enum


class NetworkMode(Enum):
    SERVER = "server"
    CLIENT = "client"
    OFFLINE = "offline"


class PlayerState:
    # Etat du joueur pour la synchronisation réseau
    
    def __init__(self, player_id: int, x: float = 0, y: float = 0):
        self.player_id = player_id
        self.x = x
        self.y = y
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.health = 100
        self.direction = 1
    
    def to_dict(self) -> Dict:
        return {
            'player_id': self.player_id,
            'x': self.x,
            'y': self.y,
            'velocity_x': self.velocity_x,
            'velocity_y': self.velocity_y,
            'health': self.health,
            'direction': self.direction
        }
    
    def from_dict(self, data: Dict):
        # Met à jour l'état du joueur à partir d'un dictionnaire
        # On récupère chaque valeur du dictionnaire data (param), si elle existe pas on garde l'ancienne
        self.x = data.get('x', self.x)
        self.y = data.get('y', self.y)
        self.velocity_x = data.get('velocity_x', self.velocity_x)
        self.velocity_y = data.get('velocity_y', self.velocity_y)
        self.health = data.get('health', self.health)
        self.direction = data.get('direction', self.direction)


class NetworkServer:
    # Serveur multijoueur, gère les connexions clients et la synchronisation d'états
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5555):
        # Initialise le serveur sur host et port (host:port)
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.clients: Dict[int, socket.socket] = {}  # Dictionnaire {id_joueur: socket}
        self.player_states: Dict[int, PlayerState] = {}  # Dictionnaire {id_joueur: état}
        self.next_player_id = 1  # Le prochain ID qu'on va donner à un joueur
        self.lock = threading.Lock()  # Pour éviter que 2 threads modifient les données en même temps
        
        # Listes simples pour savoir qui a rejoint/quitté, tu les check dans ta boucle de jeu
        self.new_players = []  # Les joueurs qui viennent d'arriver
        self.left_players = []  # Les joueurs qui viennent de partir
    
    def start(self) -> bool:
        # Start du serv
        try:
            # Crée le socket (c'est comme une "prise" réseau pour se connecter)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # SO_REUSEADDR permet de réutiliser le port immédiatement (sinon faut attendre parfois)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # On attache le socket à notre adresse et port
            self.socket.bind((self.host, self.port))
            # On écoute, max 5 connexions en attente
            self.socket.listen(5)
            self.running = True
            
            # Lance un thread séparé qui va accepter les connexions en continu
            # daemon=True = le thread meurt quand le programme principal meurt
            threading.Thread(target=self._accept_connections, daemon=True).start()
            return True
        except Exception as e:
            print(f"Server error: {e}")
            return False
    
    def stop(self):
        # Stop le serv
        self.running = False
        with self.lock: # On verrouille pour éviter les problèmes de threads (plusieurs modifications en même temps)
            # Ferme tous les sockets des clients proprement
            for client in self.clients.values():
                try:
                    client.close()
                except:
                    pass
        if self.socket:
            self.socket.close()
    
    def get_new_players(self):
        # Donne la liste des joueurs qui ont rejoint depuis le dernier check
        with self.lock:  # On verrouille pour éviter les problèmes de threads
            new = self.new_players.copy()  # On copie la liste
            self.new_players.clear()  # On vide la liste originale
            return new
    
    def get_left_players(self):
        # Donne la liste des joueurs qui ont quitté depuis le dernier check
        with self.lock:
            left = self.left_players.copy()
            self.left_players.clear()
            return left
    
    def _accept_connections(self):
        # Accepte les connections entrantes
        while self.running:
            try:
                # Bloque ici jusqu'à ce qu'un client se connecte
                client_socket, address = self.socket.accept()

                # Si un client se connecte alors le code continue ici
                
                # Donne un ID unique au nouveau joueur
                player_id = self.next_player_id
                self.next_player_id += 1
                
                with self.lock:
                    # Enregistre le client et crée son état initial
                    self.clients[player_id] = client_socket
                    self.player_states[player_id] = PlayerState(player_id)
                    self.new_players.append(player_id)  # Ajoute à la liste des nouveaux
                
                # Envoie son ID au client pour qu'il sache qui il est
                try:
                    identification = json.dumps({'__player_id__': player_id})
                    client_socket.send(identification.encode('utf-8'))
                except:
                    pass
                
                # Lance un thread qui va gérer ce client en continu
                threading.Thread(
                    target=self._handle_client,
                    args=(player_id, client_socket),
                    daemon=True
                ).start()
            except:
                pass
    
    def _handle_client(self, player_id: int, client_socket: socket.socket):
        # Gère les messages reçus d'un client
        try:
            while self.running:
                # Attend de recevoir des données du client (bloque ici)
                data = client_socket.recv(1024).decode('utf-8')
                if not data:  # Si on reçoit rien = connexion coupée
                    break
                
                # Convertit le JSON reçu en dictionnaire Python
                message = json.loads(data)
                
                with self.lock:
                    # Met à jour l'état du joueur avec les données reçues
                    if player_id in self.player_states:
                        self.player_states[player_id].from_dict(message)
        except:
            pass
        finally:
            # Quand le client se déconnecte, on nettoie tout
            with self.lock:
                if player_id in self.clients:
                    try:
                        self.clients[player_id].close()
                    except:
                        pass
                    del self.clients[player_id]
                if player_id in self.player_states:
                    del self.player_states[player_id]
                self.left_players.append(player_id)  # Marque qu'il est parti
    
    def broadcast_state(self):
        # Envoie l'état de tous les joueurs à tous les clients
        with self.lock:
            # Convertit tous les états en dictionnaires pour l'envoi
            states = {pid: state.to_dict() for pid, state in self.player_states.items()}
        
        # Convertit le tout en JSON (format texte)
        message = json.dumps(states)
        with self.lock:
            # Envoie à tous les clients connectés
            for player_id, client in list(self.clients.items()):
                try:
                    client.send(message.encode('utf-8'))
                except:
                    pass
    
    def get_player_states(self) -> Dict[int, PlayerState]:
        # Retourne l'état de tous les joueurs
        with self.lock:
            return dict(self.player_states)  # Retourne une copie du dictionnaire


class NetworkClient:
    # Client réseau pour se connecter au serveur et synchroniser l'état
    
    def __init__(self, server_ip: str, port: int = 5555):
        # Initiliase le client avec l'IP et port du serveur
        self.server_ip = server_ip
        self.server_port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.player_id: Optional[int] = None  # Notre ID sera donné par le serveur
        self.local_player_state: Optional[PlayerState] = None
        self.remote_player_states: Dict[int, PlayerState] = {}  # États de tous les autres joueurs
        self.lock = threading.Lock()
    
    def connect(self) -> bool:
        # Connexion au serveur
        try:
            # Crée un socket et se connecte au serveur
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.connected = True
            
            # Lance un thread qui va recevoir les messages du serveur en continu
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
        except Exception as e:
            print(f"Client connection error: {e}")
            return False
    
    def disconnect(self):
        # Déconnexion du serveur
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def is_connected(self) -> bool:
        # Vérifie si le client est toujours connecté
        return self.connected
    
    def _receive_messages(self):
        # Réception des mises à jour d'état du serveur
        try:
            while self.connected:
                # Attend de recevoir des données du serveur (bloque ici)
                data = self.socket.recv(4096).decode('utf-8')
                if not data:  # Connexion coupée
                    self.disconnect()
                    break
                
                # Convertit le JSON en dictionnaire
                all_states = json.loads(data)
                
                # Cas spécial : le serveur nous envoie notre ID
                if '__player_id__' in all_states:
                    with self.lock:
                        self.player_id = all_states['__player_id__']
                    continue  # On passe au prochain message
                
                # Sinon c'est une mise à jour des états de tous les joueurs
                with self.lock:
                    for player_id_str, state_data in all_states.items():
                        player_id = int(player_id_str)  # Convertit la clé en int
                        # Crée l'état du joueur s'il existe pas encore
                        if player_id not in self.remote_player_states:
                            self.remote_player_states[player_id] = PlayerState(player_id)
                        # Met à jour l'état du joueur
                        self.remote_player_states[player_id].from_dict(state_data)
        except:
            self.disconnect()
    
    def send_state(self, player_state: PlayerState):
        # Envoie l'état local du joueur au serveur
        if not self.connected:
            return
        
        try:
            # Convertit notre état en JSON et l'envoie au serveur
            message = json.dumps(player_state.to_dict())
            self.socket.send(message.encode('utf-8'))
        except:
            self.disconnect()
    
    def get_remote_player_states(self) -> Dict[int, PlayerState]:
        # Retourne l'état de tous les joueurs
        with self.lock:
            return dict(self.remote_player_states)  # Retourne une copie