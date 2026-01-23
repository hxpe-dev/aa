import struct
import json
import socket

def send_json(sock: socket.socket, data: dict):
    # Cette fonction envoie un dictionnaire Python sur un socket TCP de façon SÉCURISÉE
    
    # TCP n'est PAS basé sur des messages mais sur un flux de bytes
    # Donc on ne peut PAS faire sock.send(json) directement
    
    # 1) On convertit le dictionnaire Python en texte JSON
    # 2) On convertit ce texte en bytes (UTF-8)
    message_bytes = json.dumps(data).encode("utf-8")
    
    # On calcule la taille du message en bytes
    # Cette taille sera envoyée AVANT le message
    message_length = len(message_bytes)
    
    # On transforme la taille en 4 bytes
    # !  -> ordre réseau (big endian)
    # I  -> entier non signé (4 bytes)
    length_prefix = struct.pack("!I", message_length)
    
    # sendall() garantit que TOUS les bytes sont envoyés
    # Contrairement à send() qui peut envoyer seulement une partie
    sock.sendall(length_prefix + message_bytes)


def recv_json(sock: socket.socket):
    # Cette fonction reçoit un message JSON depuis un socket TCP
    
    # Étape 1 : lire les 4 premiers bytes
    # Ces bytes contiennent la taille du message
    raw_length = recvall(sock, 4)
    
    # Si on ne reçoit rien, cela veut dire que la connexion est fermée
    if raw_length is None:
        return None
    
    # On reconvertit les 4 bytes en entier (taille du message)
    message_length = struct.unpack("!I", raw_length)[0]
    
    # Étape 2 : lire EXACTEMENT le nombre de bytes du message
    message_bytes = recvall(sock, message_length)
    
    # Si la connexion s'est fermée pendant la réception
    if message_bytes is None:
        return None
    
    # Étape 3 : convertir les bytes en texte JSON
    # puis le texte JSON en dictionnaire Python
    return json.loads(message_bytes.decode("utf-8"))

def recvall(sock: socket.socket, size: int):
    # Cette fonction reçoit EXACTEMENT "size" bytes depuis un socket TCP
    
    # IMPORTANT :
    # sock.recv(n) peut retourner MOINS de n bytes
    # Il faut donc boucler jusqu'à tout recevoir
    
    data = b""  # Buffer vide pour stocker les bytes reçus
    
    while len(data) < size:
        # On demande les bytes manquants
        packet = sock.recv(size - len(data))
        
        # Si recv() retourne b"" → la connexion est fermée
        if not packet:
            return None
        
        # On ajoute les bytes reçus au buffer
        data += packet
    
    # Quand on a reçu exactement "size" bytes, on les retourne
    return data

