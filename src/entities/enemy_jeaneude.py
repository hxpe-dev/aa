# Classe de Jean-Eude avec IA simple de patrouille gauche/droite
import pygame
from entities.base_entity import BaseEntity
from settings import *
from typing import Optional, List


# États de l'IA de Jean-Eude
class EnemyState:
    PATROL = "patrol"   # Patrouille gauche/droite de base
    ALERT = "alert"    # A détecté le joueur, pause avant de charger
    CHASE = "chase"    # Poursuit le joueur
    ATTACK = "attack"   # Attaque (cooldown après un coup)
    RETURN = "return"   # Retourne à l'origine après avoir perdu le joueur

class JeanEude(BaseEntity):

    def __init__(self, x: float, y: float, patrol_range: float = 150.0):
        super().__init__(x, y, JEANEUDE_WIDTH, JEANEUDE_HEIGHT)

        # Apparence
        self.sprite_size = 105
        self.current_sprite_index = 0
        self.sprite_counter = 0
        self.direction = 1 # 1 = droite, -1 = gauche
        
        self.walking_sprites = [
            pygame.transform.scale(pygame.image.load(f'assets\\mobs\\skeleton\\Walking\\Walking-{i}.png').convert_alpha(), (self.sprite_size, self.sprite_size)) for i in range(2)
        ]
        self.sprite = self.walking_sprites[0]
        self.image = self.sprite
        
        # IA de patrouille
        self.patrol_origin_x = x # Centre de la zone de patrouille
        self.patrol_range = patrol_range # Distance max de chaque côté
        
        self.state = EnemyState.PATROL
        
        # Détection : champ de vision horizontal (pixels) et vertical (pixels)
        self.detection_range_x = 220
        self.detection_range_y = 80
        
        # Poursuite : distance à laquelle Jean-Eude abandonne
        self.chase_lose_range = 320
        
        # Attaque
        self.attack_range = 40 # Distance à partir de laquelle il attaque
        self.attack_damage = 10
        self.attack_cooldown = 90
        self.attack_timer = 0
        
        # Alert (pause avant de charger)
        self.alert_duration = 40 # Frames de pause à la détection
        self.alert_timer = 0
        
        # Vitesse de retour au point d'origine
        self.return_speed = JEANEUDE_SPEED * 0.8
        
        # Vie
        self.health = JEANEUDE_MAX_HEALTH
        self.is_dead = False
        self.hit_flash_counter = 0

        # Référence au joueur cible
        self.target_player = None

        # État de collision
        self.collision_left = False
        self.collision_right = False
        self.collision_top = False
        self.collision_bottom = False

    def take_damage(self, damage: int):
        # Inflige des dégâts à Jean-Eude
        self.health = max(0, self.health - damage)
        self.hit_flash_counter = 15 # nb de frames ou on affiche jeaneude en rouge
        if self.health <= 0:
            self.is_dead = True

    def get_net_state(self) -> dict:
        # Retourne l'état pour la synchro réseau
        return {
            'x': self.x,
            'y': self.y,
            'direction': self.direction,
            'state': self.state,
            'anim_frame': self.current_sprite_index,
            'health': self.health,
            'is_dead': self.is_dead,
        }

    def apply_net_state(self, data: dict):
        # Applique un état reçu du serveur
        self.x = data.get('x', self.x)
        self.y = data.get('y', self.y)
        self.direction = data.get('direction', self.direction)
        self.state = data.get('state', self.state)
        if data.get('health', self.health) < self.health:
            self.hit_flash_counter = 15
        self.health = data.get('health', self.health)
        self.is_dead = data.get('is_dead', self.is_dead)
        frame = data.get('anim_frame', 0)
        self.current_sprite_index = frame % len(self.walking_sprites)
        self.sprite = self.walking_sprites[self.current_sprite_index]
        self.rect.topleft = (int(self.x), int(self.y))
        if self.direction == -1:
            self.image = pygame.transform.flip(self.sprite, True, False)
        else:
            self.image = self.sprite

    # Mise à jour principale

    def update(self, dt: float, colliders: Optional[List[pygame.Rect]] = None, players: Optional[list] = None):
        if self.is_dead:
            return

        if colliders is None:
            colliders = []
            
        if players:
            self.target_player = self._find_closest_player(players)
            
        self._run_state_machine()
        
        self._apply_gravity()
        self._move_and_collide(colliders)
        self._update_animation()

        self.rect.topleft = (int(self.x), int(self.y))
        
        # Retourne le sprite en fn de la direction
        if self.direction == -1:
            self.image = pygame.transform.flip(self.sprite, True, False)
        else:
            self.image = self.sprite
            
            
    def _find_closest_player(self, players: list):
        closest = None
        closest_dist = float('inf')
        for player in players:
            if player is None:
                continue
            if player.health <= 0:
                continue
            dx = player.x - self.x
            dist = abs(dx)
            if dist < closest_dist:
                closest_dist = dist
                closest = player
        return closest
    
    def _run_state_machine(self):
        if self.state == EnemyState.PATROL:
            self._state_patrol()
 
        elif self.state == EnemyState.ALERT:
            self._state_alert()
 
        elif self.state == EnemyState.CHASE:
            self._state_chase()
 
        elif self.state == EnemyState.ATTACK:
            self._state_attack()
 
        elif self.state == EnemyState.RETURN:
            self._state_return()

    def _state_patrol(self):
        # Patrouille gauche/droite classique
        if self.x > self.patrol_origin_x + self.patrol_range:
            self.direction = -1
        elif self.x < self.patrol_origin_x - self.patrol_range:
            self.direction = 1
 
        if self.direction == 1 and self.collision_right:
            self.direction = -1
        elif self.direction == -1 and self.collision_left:
            self.direction = 1
 
        self.velocity_x = self.direction * JEANEUDE_SPEED
 
        # Transition -> ALERT si le joueur est détecté
        if self._can_detect_player():
            self.alert_timer = self.alert_duration
            self.velocity_x = 0
            self.state = EnemyState.ALERT
            
    def _state_alert(self):
        # Pause avant de charger (donne un signal visuel au joueur)
        self.velocity_x = 0
        self.alert_timer -= 1
 
        # Se tourne vers le joueur pendant la pause
        if self.target_player:
            self.direction = 1 if self.target_player.x > self.x else -1
 
        if self.alert_timer <= 0:
            self.state = EnemyState.CHASE
            
    def _state_chase(self):
        if not self.target_player:
            self.state = EnemyState.RETURN
            return
 
        dx = self.target_player.x - self.x
        dy = self.target_player.y - self.y
        dist_x = abs(dx)
        dist_y = abs(dy)
 
        # Perd le joueur -> retour
        if dist_x > self.chase_lose_range or dist_y > self.detection_range_y * 2:
            self.state = EnemyState.RETURN
            return
 
        # Assez proche pour attaquer
        if dist_x <= self.attack_range and dist_y <= self.detection_range_y:
            self.state = EnemyState.ATTACK
            return
 
        # Poursuite
        self.direction = 1 if dx > 0 else -1
        self.velocity_x = self.direction * JEANEUDE_SPEED * 1.4 # Un peu plus rapide en chasse
 
        # Demi tour si mur
        if self.direction == 1 and self.collision_right:
            self.direction = -1
        elif self.direction == -1 and self.collision_left:
            self.direction = 1
            
    def _state_attack(self):
        self.velocity_x = 0  # S'arrête pour attaquer
 
        # Décrémente le cooldown
        self.attack_timer = max(0, self.attack_timer - 1)
 
        if self.attack_timer == 0:
            # Inflige des dégâts si le joueur est encore à portée
            if self.target_player:
                dx = abs(self.target_player.x - self.x)
                dy = abs(self.target_player.y - self.y)
                if dx <= self.attack_range and dy <= self.detection_range_y:
                    self.target_player.take_damage(self.attack_damage)
                    print(f"Jean-Eude a attaqué le joueur ! ({self.attack_damage} dégâts)")
            self.attack_timer = self.attack_cooldown
            # Retour en CHASE après l'attaque
            self.state = EnemyState.CHASE
            
    def _state_return(self):
        dx = self.patrol_origin_x - self.x
 
        if abs(dx) < 5:
            # Arrivé a l'origine
            self.x = self.patrol_origin_x
            self.velocity_x = 0
            self.state = EnemyState.PATROL
            return
 
        if dx > 0:
            self.direction = 1
        else:
            self.direction = -1

        self.velocity_x = self.direction * self.return_speed
 
        # Si le joueur se rapproche a nouveau pendant le retour -> redétection
        if self._can_detect_player():
            self.alert_timer = self.alert_duration // 2 # Pause plus courte
            self.state = EnemyState.ALERT
            
    def _can_detect_player(self) -> bool:
        if not self.target_player:
            return False
        dx = abs(self.target_player.x - self.x)
        dy = abs(self.target_player.y - self.y)
        
        # Vérifie que le joueur est dans le champ de vision ET du même côté que la direction
        in_front = (self.target_player.x > self.x) == (self.direction == 1)
        return dx <= self.detection_range_x and dy <= self.detection_range_y and in_front


    # Gravité appliqué a Jean-Eude
    def _apply_gravity(self):
        if not self.is_grounded:
            self.velocity_y += PLAYER_FALL_ACCELERATION # On utilise la meme gravité que le joueur
            self.velocity_y = min(self.velocity_y, PLAYER_MAX_FALL_SPEED)

    # Déplacement et collisions, la même logique que Player
    def _move_and_collide(self, colliders: List[pygame.Rect]):
        # Mouvement horizontal
        self.x += self.velocity_x
        rect = self.get_rect()
        self.collision_left = False
        self.collision_right = False

        for collider in colliders:
            if not rect.colliderect(collider):
                continue
            if self.velocity_x > 0:
                self.x = collider.left - self.width
                self.velocity_x = 0
                self.collision_right = True
            elif self.velocity_x < 0:
                self.x = collider.right
                self.velocity_x = 0
                self.collision_left = True
            rect = self.get_rect()

        # Mouvement vertical
        self.y += self.velocity_y
        rect = self.get_rect()
        self.collision_top = False
        self.collision_bottom = False

        for collider in colliders:
            if not rect.colliderect(collider):
                continue
            if self.velocity_y > 0:
                self.y = collider.top - self.height
                self.velocity_y = 0
                self.collision_bottom = True
                break
            elif self.velocity_y < 0:
                self.y = collider.bottom
                self.velocity_y = 0
                self.collision_top = True
                break
            rect = self.get_rect()

        # Vérifier si Jean-Eude est en contact avec le sol
        self.is_grounded = False
        if self.collision_bottom:
            self.is_grounded = True
        else:
            test_rect = self.get_rect()
            test_rect.y += 1
            for collider in colliders:
                if test_rect.colliderect(collider):
                    self.is_grounded = True
                    break

        self.is_walled_left = self.collision_left
        self.is_walled_right = self.collision_right
        
    def _update_animation(self):
        self.sprite_counter += 1
        if self.sprite_counter >= 8:
            self.current_sprite_index = (self.current_sprite_index + 1) % len(self.walking_sprites)
            self.sprite = self.walking_sprites[self.current_sprite_index]
            self.sprite_counter = 0

    def draw(self, surface: pygame.Surface, offset=(0, 0), show_colliders=True):
        if self.is_dead:
            return

        render_x = self.x + offset[0] - (self.sprite_size - JEANEUDE_WIDTH) // 2
        render_y = self.y + offset[1] - (self.sprite_size - JEANEUDE_HEIGHT)

        if self.hit_flash_counter > 0:
            self.hit_flash_counter -= 1
            img = self.image.copy()
            img.fill((200, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD) # pour ajouter dans le rouge et pas modifier les autres couleurs
        else:
            img = self.image
        surface.blit(img, (render_x, render_y))

        if show_colliders:
            draw_rect = self.rect.copy()
            draw_rect.x += offset[0]
            draw_rect.y += offset[1]
            pygame.draw.rect(surface, (255, 100, 0), draw_rect, 1)