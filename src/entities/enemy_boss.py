import pygame
import random
from entities.base_entity import BaseEntity
from settings import *
from typing import Optional, List

class BossState:
    IDLE = "idle" # marche vers le joueur, choisit la prochaine attaque
    SWORD = "sword" # coup d'epee corps a corps
    SLAM = "slam" # saut + ecrasement + onde de choc

class Boss(BaseEntity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, BOSS_WIDTH, BOSS_HEIGHT)

        self.direction = 1
        self.health = BOSS_MAX_HEALTH
        self.is_dead = False
        self.hit_flash_counter = 0

        # Placeholder rectangle violet, a remplacer par des sprites
        self.image = pygame.Surface((BOSS_WIDTH, BOSS_HEIGHT))
        self.image.fill((120, 0, 160))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.target_player = None

        self.state = BossState.IDLE
        self.idle_timer = 90

        # Phase 2 declenchee a 50% de vie
        self.phase2 = False

        # Epee : sword_phase 0 = prep, 1 = hitbox active
        self.sword_phase = 0
        self.sword_timer = 0
        self.sword_hit_this_attack = False

        # Slam : slam_phase 0 = saut, 1 = chute forcee, 2 = onde de choc
        self.slam_phase = 0
        self.shockwave_left = None
        self.shockwave_right = None
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

        # Hitbox epee visible pendant la phase active
        if self.state == BossState.SWORD and self.sword_phase == 1:
            pygame.draw.rect(surface, (255, 220, 0), self.get_sword_rect().move(offset[0], offset[1]), 3)

        # Onde de choc visible (element de gameplay)
        if self.shockwave_left:
            pygame.draw.rect(surface, (255, 140, 0), self.shockwave_left.move(offset[0], offset[1]), 4)
        if self.shockwave_right:
            pygame.draw.rect(surface, (255, 140, 0), self.shockwave_right.move(offset[0], offset[1]), 4)

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

        speed = BOSS_WALK_SPEED
        if self.phase2:
            speed = BOSS_WALK_SPEED * 1.4

        self.velocity_x = self.direction * speed

        if dist < BOSS_MELEE_RANGE:
            self.velocity_x = 0
            self._start_sword()
            return

        self.idle_timer -= 1
        if self.idle_timer <= 0:
            self.state = BossState.SLAM
            self.slam_phase = 0
            self.idle_timer = 90
            if self.phase2:
                self.idle_timer = 50

    def _start_sword(self):
        self.state = BossState.SWORD
        self.sword_phase = 0
        self.sword_timer = BOSS_SWORD_PREP
        self.sword_hit_this_attack = False

    def _state_sword(self, players):
        self.velocity_x = 0

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
            ax = self.x + self.width
        else:
            ax = self.x - BOSS_SWORD_RANGE_W
        ay = self.y + (self.height - BOSS_SWORD_RANGE_H) // 2
        return pygame.Rect(int(ax), int(ay), BOSS_SWORD_RANGE_W, BOSS_SWORD_RANGE_H)

    def _state_slam(self, players):
        if self.slam_phase == 0:
            if self.is_grounded:
                self.velocity_y = BOSS_SLAM_JUMP_FORCE
            if self.velocity_y >= 0:
                self.slam_phase = 1

        elif self.slam_phase == 1:
            self.velocity_y = BOSS_SLAM_FALL_SPEED
            if self.collision_bottom:
                self._create_shockwave()
                self.slam_phase = 2
                self.shockwave_timer = BOSS_SHOCKWAVE_DURATION
                self.shockwave_hit_players = set()

        elif self.slam_phase == 2:
            self.velocity_x = 0
            self.shockwave_timer -= 1

            if players:
                for player in players:
                    if player.health <= 0 or player in self.shockwave_hit_players:
                        continue
                    if not player.is_grounded:
                        continue
                    player_rect = player.get_rect()
                    if ((self.shockwave_left and player_rect.colliderect(self.shockwave_left)) or (self.shockwave_right and player_rect.colliderect(self.shockwave_right))):
                        player.take_damage(BOSS_SHOCKWAVE_DAMAGE)
                        self.shockwave_hit_players.add(player)

            if self.shockwave_timer <= 0:
                self.shockwave_left = None
                self.shockwave_right = None
                self._end_attack()

    def _create_shockwave(self):
        sw_h = 28
        sw_w = BOSS_SHOCKWAVE_WIDTH
        y = self.y + self.height - sw_h
        self.shockwave_left = pygame.Rect(self.x - sw_w, y, sw_w, sw_h)
        self.shockwave_right = pygame.Rect(self.x + self.width, y, sw_w, sw_h)

    def _end_attack(self):
        self.velocity_x = 0
        self.state = BossState.IDLE
        self.idle_timer = 90
        if self.phase2:
            self.idle_timer = 50

    def _find_closest_player(self, players: list):
        closest = None
        closest_dist = float('inf')
        for player in players:
            if player is None or player.health <= 0:
                continue
            dist = abs(player.x - self.x)
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
