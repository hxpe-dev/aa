# Classe du joueur avec système de mouvement complet
# Gère les déplacements, sauts, double saut, dash et collisions
import pygame
from entities.base_entity import BaseEntity
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_ACCELERATION,
    PLAYER_DECELERATION, PLAYER_JUMP_FORCE, PLAYER_FALL_ACCELERATION,
    PLAYER_MAX_FALL_SPEED, PLAYER_COYOTE_TIME, PLAYER_JUMP_BUFFER_TIME,
    PLAYER_DOUBLE_JUMP_ENABLED, PLAYER_DASH_SPEED,
    PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN, PLAYER_MAX_HEALTH
)
from typing import Optional, List


class Player(BaseEntity):    
    def __init__(self, x: float, y: float):
        # Initialise le joueur à la position donnée

        super().__init__(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        
        # État du joueur
        self.health = PLAYER_MAX_HEALTH
        self.direction = 1  # 1 = droite, -1 = gauche
        
        # Mouvement Horizontal
        self.input_direction = 0  # -1 (gauche), 0 (arrêt), ou 1 (droite)
        self.target_velocity_x = 0.0  # Vélocité cible vers laquelle accélérer
        
        # Saut et Physique Verticale
        self.jump_pressed = False  # Le bouton de saut est-il actuellement pressé
        self.coyote_counter = 0  # Frames restantes pour sauter après quitter le sol
        self.jump_buffer_counter = 0  # Enregistrement anticipé du saut avant atterrissage
        self.double_jump_available = True  # Double saut disponible
        
        # Dash
        self.dash_active = False  # Le dash est-il actuellement actif
        self.dash_direction = 1  # Direction du dash (1 = droite, -1 = gauche)
        self.dash_counter = 0  # Frames restantes du dash courant
        self.dash_cooldown_counter = 0  # Cooldown avant prochain dash
        self.dash_available = True  # Peut démarrer un nouveau dash
        
        # État de Collision
        self.collision_left = False
        self.collision_right = False
        self.collision_top = False
        self.collision_bottom = False
        
        # Apparence (bleu par défaut, à remplacer par sprite)
        self.image.fill((100, 149, 237))
    
    def handle_input(self, keys):
        # Traite les entrées du clavier pour le mouvement
        # keys = état des touches du clavier (pygame.key.get_pressed())
        
        # Mouvement horizontal (Q/D ou flèches)
        self.input_direction = 0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            self.input_direction = -1
            self.direction = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.input_direction = 1
            self.direction = 1
        
        # Saut (Z/Espace ou flèche haut)
        if keys[pygame.K_z] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
            if not self.jump_pressed:
                self.jump_pressed = True
                self.jump_buffer_counter = PLAYER_JUMP_BUFFER_TIME
        else:
            self.jump_pressed = False
        
        # Dash (Shift gauche ou droit)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.start_dash()
    
    def update(self, dt: float, colliders: Optional[List[pygame.Rect]] = None):
        # Met à jour le jouer chaque frame
        # dt = delta time (temps écoulé)
        # colliders = liste des rectangles de collision

        if colliders is None:
            colliders = []
        
        # Mise à jour des compteurs de temps
        self._update_timers()
        
        # Calcul des nouvelles vélocités
        self._update_horizontal_movement()
        self._update_jump()
        self._update_dash()
        self._apply_gravity()
        
        # Appliquer le mouvement et gérer les collisions
        self._move_and_collide(colliders)
        
        # Mise à jour du rect pour le rendu
        self.rect.topleft = (int(self.x), int(self.y))
    
    def _move_and_collide(self, colliders: List[pygame.Rect]):
        # Déplace le joueur et gère les collisions séparément pour X et Y
        # colliders = liste des rectangles de collision

        # Mouvement Horizontal
        self.x += self.velocity_x
        player_rect = self.get_rect()
        
        # Vérifier collisions horizontales et corriger position
        for collider in colliders:
            if not player_rect.colliderect(collider):
                continue
            
            if self.velocity_x > 0:
                # Collision à droite: pousser à gauche du collider
                self.x = collider.left - self.width
                self.velocity_x = 0
                self.collision_right = True
            elif self.velocity_x < 0:
                # Collision à gauche: pousser à droite du collider
                self.x = collider.right
                self.velocity_x = 0
                self.collision_left = True
            
            # Recalculer rect pour la prochaine collision
            player_rect = self.get_rect()
        
        # Mouvement Vertical
        self.y += self.velocity_y
        player_rect = self.get_rect()
        
        # Réinitialiser les flags de collision verticale
        self.collision_top = False
        self.collision_bottom = False
        
        # Vérifier collisions verticales et corriger position
        for collider in colliders:
            if not player_rect.colliderect(collider):
                continue
            
            if self.velocity_y > 0:
                # Collision par le bas (atterrissage)
                self.y = collider.top - self.height
                self.velocity_y = 0
                self.collision_bottom = True
                self.double_jump_available = True  # Récupérer le double saut
                # Ne pas traiter d'autres collisions verticales une fois au sol
                break
            elif self.velocity_y < 0:
                # Collision par le haut (cogner la tête)
                self.y = collider.bottom
                self.velocity_y = 0
                self.collision_top = True
                # Ne pas traiter d'autres collisions verticales une fois frappé au-dessus
                break
            
            # Recalculer rect pour la prochaine collision
            player_rect = self.get_rect()
        
        # Déterminer si au sol
        # Vérifier si le joueur est en contact avec le sol (collision_bottom ou velocity_y == 0 et grounded avant)
        player_rect = self.get_rect()
        self.is_grounded = False
        
        if self.collision_bottom:
            self.is_grounded = True
        else:
            # Vérifier si on est assis sur quelque chose sans tomber
            test_rect = player_rect.copy()
            test_rect.y += 1  # Vérifier juste en-dessous
            for collider in colliders:
                if test_rect.colliderect(collider):
                    self.is_grounded = True
                    break
    
    def _update_timers(self):
        # Mets à jour les compteurs de délai

        # Gestion du coyote time (grace period pour sauter après quitter le sol)
        if self.is_grounded:
            self.coyote_counter = PLAYER_COYOTE_TIME
        else:
            self.coyote_counter = max(0, self.coyote_counter - 1)
        
        # Gestion du jump buffer (enregistrement anticipé du saut)
        self.jump_buffer_counter = max(0, self.jump_buffer_counter - 1)
        
        # Gestion du dash actif
        if self.dash_active:
            self.dash_counter -= 1
            if self.dash_counter <= 0:
                self.dash_active = False
        
        # Gestion du cooldown du dash
        self.dash_cooldown_counter = max(0, self.dash_cooldown_counter - 1)
        if self.dash_cooldown_counter == 0: 
            self.dash_available = True
    
    def _update_horizontal_movement(self):
        # Mets à jour le mouvement horizontal avec accélération et décélération

        # Déterminer la vélocité cible en fonction de l'input
        if self.input_direction != 0:
            self.target_velocity_x = self.input_direction * PLAYER_SPEED
        else:
            self.target_velocity_x = 0.0
        
        # Appliquer accélération ou décélération progressive
        if abs(self.velocity_x) < abs(self.target_velocity_x):
            # Accélérer vers la vélocité cible
            self.velocity_x += self.target_velocity_x * PLAYER_ACCELERATION
            self.velocity_x = max(-PLAYER_SPEED, min(PLAYER_SPEED, self.velocity_x))
        elif self.target_velocity_x == 0:
            # Décélérer vers zéro
            self.velocity_x *= PLAYER_DECELERATION
            if abs(self.velocity_x) < 0.1:
                self.velocity_x = 0
        else:
            # Changer de direction (accélération rapide)
            self.velocity_x = self.target_velocity_x
    
    def _update_jump(self):
        # Gère la logique du jump

        # Vérifier si le joueur peut sauter maintenant
        peut_sauter_au_sol = self.coyote_counter > 0
        peut_double_sauter = PLAYER_DOUBLE_JUMP_ENABLED and self.double_jump_available
        peut_sauter = peut_sauter_au_sol or peut_double_sauter
        
        # Exécuter le saut si le buffer est actif et conditions remplies
        if self.jump_buffer_counter > 0 and peut_sauter:
            self.perform_jump()
            self.jump_buffer_counter = 0
    
    def perform_jump(self):
        # Effectue le saut du joueur en appliquant les forces

        self.velocity_y = PLAYER_JUMP_FORCE
        self.is_grounded = False
        
        # Si on saute en l'air, on utilise le double saut
        if self.coyote_counter <= 0:
            self.double_jump_available = False
        
        # Consommer le coyote time
        self.coyote_counter = 0
    
    def _apply_gravity(self):
        # Applique la gravité avec une accélération

        if not self.is_grounded:
            # Appliquer la gravité
            self.velocity_y += PLAYER_FALL_ACCELERATION
            
            # Limiter la vitesse maximale de chute pour éviter les bugs
            if self.velocity_y > PLAYER_MAX_FALL_SPEED:
                self.velocity_y = PLAYER_MAX_FALL_SPEED
    
    def _update_dash(self):
        # Gère le mouvement du dash actif
        if self.dash_active:
            # Le dash annule la gravité
            self.velocity_x = self.dash_direction * PLAYER_DASH_SPEED
            self.velocity_y = 0
    
    def start_dash(self):
        # Démarre un dash dans la direction du joueur
        if not self.dash_available or self.dash_active:
            return
        
        self.dash_active = True
        self.dash_counter = PLAYER_DASH_DURATION
        self.dash_direction = self.direction if self.direction != 0 else 1
        self.dash_available = False
        self.dash_cooldown_counter = PLAYER_DASH_COOLDOWN
    
    def take_damage(self, damage: int) -> bool:
        # Inflige des dégâts au joueur
        self.health = max(0, self.health - damage)
        return self.health <= 0
    
    def heal(self, amount: int):
        # Soigne le joueur HAHA
        self.health = min(PLAYER_MAX_HEALTH, self.health + amount)
    
    def draw(self, surface: pygame.Surface, offset=(0, 0)):
        # Dessine le joueur avec indicateurs de debug

        # Dessiner le rectangle du joueur
        draw_rect = self.rect.copy()
        draw_rect.x += offset[0]
        draw_rect.y += offset[1]
        surface.blit(self.image, draw_rect)
        
        # Dessiner un indicateur de direction
        indicator_x = draw_rect.centerx + (self.direction * 10)
        indicator_y = draw_rect.centery
        pygame.draw.circle(surface, (255, 0, 0), (int(indicator_x), int(indicator_y)), 3)
        
        # Afficher ligne verte si au sol (debug)
        if self.is_grounded:
            pygame.draw.line(surface, (0, 255, 0), 
                           (draw_rect.left, draw_rect.bottom),
                           (draw_rect.right, draw_rect.bottom), 2)
    
    def reset_position(self, x: float, y: float):
        # Reset la position du joueur aux coordonnées données
        self.set_position(x, y)
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_grounded = False
        self.double_jump_available = True
        self.dash_available = True
    
    def get_state(self) -> dict:
        # Retourne l'état complet du joueur (pour debug ou infos)
        return {
            'position': (self.x, self.y),
            'velocity': (self.velocity_x, self.velocity_y),
            'health': self.health,
            'is_grounded': self.is_grounded,
            'is_falling': self.is_falling,
            'double_jump_available': self.double_jump_available,
            'dash_available': self.dash_available,
            'dash_active': self.dash_active,
        }
