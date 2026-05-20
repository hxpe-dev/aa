import pygame
import random
from entities.base_entity import BaseEntity
from settings import *
from typing import Optional, List

class BossState:
    IDLE = "idle" # Se déplace, évalue la situation et attend le bon moment
    SWORD = "sword" # Coup d'épée au corps-à-corps
    SLAM = "slam" # Saut + écrasement + onde de choc

class Boss(BaseEntity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, BOSS_WIDTH, BOSS_HEIGHT)

        self.direction = 1
        self.health = BOSS_MAX_HEALTH
        self.is_dead = False
        self.hit_flash_counter = 0

        # Placeholder rectangle violet
        self.image = pygame.Surface((BOSS_WIDTH, BOSS_HEIGHT))
        self.image.fill((120, 0, 160))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.target_player = None
        self.state = BossState.IDLE
        
        self.idle_timer = 60
        self.sword_cooldown = 0 # Empêche le spam de l'attaque mêlée
        
        # Phase 2 déclenchée à 50% de vie
        self.phase2 = False

        # Épée
        self.sword_phase = 0
        self.sword_timer = 0
        self.sword_hit_this_attack = False

        # Slam
        self.slam_phase = 0
        self.shockwave_rect = None  
        self.shockwave_timer = 0
        self.shockwave_hit_players = set()

        self.collision_left = False
        self.collision_right = False
        self.collision_top = False
        self.collision_bottom = False

    def take_damage(self, damage: int):
        self.health = max(0, self.health - damage)
        self.hit_flash_counter = 15
        if self.health <= 0:
            self.is_dead = True
        if not self.phase2 and self.health <= BOSS_MAX_HEALTH // 2:
            self.phase2 = True

    def update(self, dt: float, colliders: Optional[List[pygame.Rect]] = None, players: Optional[list] = None):
        if self.is_dead:
            return

        if colliders is None:
            colliders = []

        if players:
            self.target_player = self._find_closest_player(players)

        # Diminution des CD
        if self.sword_cooldown > 0:
            self.sword_cooldown -= 1

        self._run_state_machine(players)
        self._apply_gravity()
        self._move_and_collide(colliders)

        self.rect.topleft = (int(self.x), int(self.y))

    def draw(self, surface: pygame.Surface, offset=(0, 0), show_colliders=True):
        if self.is_dead:
            return

        rx = self.x + offset[0]
        ry = self.y + offset[1]

        if self.hit_flash_counter > 0:
            self.hit_flash_counter -= 1
            img = self.image.copy()
            img.fill((200, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            img = self.image

        surface.blit(img, (rx, ry))

        if self.state == BossState.SWORD and self.sword_phase == 1:
            pygame.draw.rect(surface, (255, 220, 0), self.get_sword_rect().move(offset[0], offset[1]), 3)

        if self.shockwave_rect:
            pygame.draw.rect(surface, (255, 140, 0), self.shockwave_rect.move(offset[0], offset[1]), 4)

        if show_colliders:
            pygame.draw.rect(surface, (200, 0, 255), self.rect.move(offset[0], offset[1]), 2)

    def _run_state_machine(self, players):
        if self.state == BossState.IDLE:
            self._state_idle()
        elif self.state == BossState.SWORD:
            self._state_sword(players)
        elif self.state == BossState.SLAM:
            self._state_slam(players)

    def _state_idle(self):
        if not self.target_player:
            self.velocity_x = 0
            return

        dx = self.target_player.x - self.x
        dist = abs(dx)

        self.direction = 1 
        if dx < 0:
            self.direction = -1

        # Vitesse augmentée en Phase 2
        speed = BOSS_WALK_SPEED
        if self.phase2:
            speed = BOSS_WALK_SPEED * 1.5
        self.velocity_x = self.direction * speed

        if dist < BOSS_MELEE_RANGE:
            # Si le joueur est proche mais que l'épée est en cooldown, le boss prend une décision imprévisible
            if self.sword_cooldown <= 0:
                # 70% de chance de mettre un coup d'épée, 30% de chance de faire un Slam intant
                if random.random() < 0.70:
                    self.velocity_x = 0
                    self._start_sword()
                else:
                    self._start_slam()
                return
            else:
                # L'épée est en cooldown ! Pour éviter de rester passif, il a 40% de chance de punir l'esquive du joueur avec un Slam
                if random.random() < 0.40 and self.is_grounded:
                    self._start_slam()
                    return

        # Gestion du timer de l'état IDLE (comportement à distance)
        self.idle_timer -= 1
        if self.idle_timer <= 0:
            self._start_slam()

    def _start_sword(self):
        self.state = BossState.SWORD
        self.sword_phase = 0
        self.sword_timer = BOSS_SWORD_PREP
        self.sword_hit_this_attack = False
        # cooldown pour le prochain coup (plus court en Phase 2)
        self.sword_cooldown = 45 if self.phase2 else 90

    def _start_slam(self):
        self.state = BossState.SLAM
        self.slam_phase = 0
        self.velocity_x = 0  # Immobilisation au sol avant le saut

    def _state_sword(self, players):
        self.velocity_x = 0

        # Ajuste la direction uniquement pendant la préparation du coup
        if self.target_player and self.sword_phase == 0:
            self.direction = 1 if self.target_player.x > self.x else -1

        self.sword_timer -= 1

        if self.sword_phase == 0 and self.sword_timer <= 0:
            self.sword_phase = 1
            self.sword_timer = BOSS_SWORD_ACTIVE

        elif self.sword_phase == 1:
            if not self.sword_hit_this_attack and players:
                sword_rect = self.get_sword_rect()
                for player in players:
                    if player.health <= 0:
                        continue
                    if sword_rect.colliderect(player.get_rect()):
                        player.take_damage(BOSS_SWORD_DAMAGE)
                        self.sword_hit_this_attack = True
                        break

            if self.sword_timer <= 0:
                self._end_attack()

    def get_sword_rect(self) -> pygame.Rect:
        if self.direction == 1:
            ax = self.rect.right
        else:
            ax = self.rect.left - BOSS_SWORD_RANGE_W
        ay = self.rect.centery - BOSS_SWORD_RANGE_H // 2
        return pygame.Rect(int(ax), int(ay), BOSS_SWORD_RANGE_W, BOSS_SWORD_RANGE_H)

    def _state_slam(self, players):
        if self.slam_phase == 0:
            if self.is_grounded:
                self.velocity_y = BOSS_SLAM_JUMP_FORCE
                
                # saute en bougeant horizontalement pour traquer le joueur
                if self.target_player:
                    dx = self.target_player.x - self.rect.centerx
                    self.velocity_x = (1 if dx > 0 else -1) * min(abs(dx) * 0.08, BOSS_WALK_SPEED * 2)
            
            if self.velocity_y >= 0:
                self.slam_phase = 1

        elif self.slam_phase == 1:
            # Chute forcée vers le sol
            self.velocity_y = BOSS_SLAM_FALL_SPEED
            if self.collision_bottom:
                self._create_shockwave()
                self.slam_phase = 2
                self.shockwave_timer = BOSS_SHOCKWAVE_DURATION
                self.shockwave_hit_players = set()

        elif self.slam_phase == 2:
            self.velocity_x = 0
            self.shockwave_timer -= 1

            if players and self.shockwave_rect:
                for player in players:
                    if player.health <= 0 or player in self.shockwave_hit_players:
                        continue
                    if not player.is_grounded:
                        continue
                    if player.get_rect().colliderect(self.shockwave_rect):
                        player.take_damage(BOSS_SHOCKWAVE_DAMAGE)
                        self.shockwave_hit_players.add(player)

            if self.shockwave_timer <= 0:
                self._end_attack()

    def _create_shockwave(self):
        sw_h = 30
        sw_w = BOSS_SHOCKWAVE_WIDTH
        lx = self.rect.left - sw_w
        y = self.rect.bottom - sw_h
        total_width = sw_w + self.rect.width + sw_w
        self.shockwave_rect = pygame.Rect(int(lx), int(y), total_width, sw_h)

    def _end_attack(self):
        self.velocity_x = 0
        self.state = BossState.IDLE
        self.shockwave_rect = None
        self.idle_timer = 40 if self.phase2 else 75

    def _find_closest_player(self, players: list):
        closest = None
        closest_dist = float('inf')
        for player in players:
            if player is None or player.health <= 0:
                continue
            dist = abs(player.x - self.rect.centerx)
            if dist < closest_dist:
                closest_dist = dist
                closest = player
        return closest

    def _apply_gravity(self):
        if self.is_grounded:
            return
        if self.state == BossState.SLAM and self.slam_phase == 1:
            return
        self.velocity_y += PLAYER_FALL_ACCELERATION
        self.velocity_y = min(self.velocity_y, PLAYER_MAX_FALL_SPEED)

    def _move_and_collide(self, colliders: List[pygame.Rect]):
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

    def get_net_state(self) -> dict:
        return {
            'x': self.x,
            'y': self.y,
            'direction': self.direction,
            'state': self.state,
            'health': self.health,
            'is_dead': self.is_dead,
        }

    def apply_net_state(self, data: dict):
        self.x = data.get('x', self.x)
        self.y = data.get('y', self.y)
        self.direction = data.get('direction', self.direction)
        self.state = data.get('state', self.state)
        self.health = data.get('health', self.health)
        self.is_dead = data.get('is_dead', self.is_dead)
        self.rect.topleft = (int(self.x), int(self.y))