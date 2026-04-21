import math
import random

from game.constants import ARENA_CENTER_X, ARENA_CENTER_Y, ARENA_RADIUS


class AIController:
    """AI-related controls extracted from Game."""

    def __init__(self, game):
        self.game = game

    def auto_test_ai_control(self, player, opponent, is_player1=True):
        ai_keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "weapon_a": False,
            "weapon_b": False,
            "hyper": False,
            "dash": False,
            "special": False,
            "shield": False,
        }

        ai_timer = self.game.ai_move_timer1 if is_player1 else self.game.ai_move_timer2
        ai_direction = (
            self.game.ai_move_direction1 if is_player1 else self.game.ai_move_direction2
        )

        projectile_data = self.predict_projectile_collision(player)
        if projectile_data:
            proj, time_to_hit, _, _ = projectile_data

            proj_dir_x = math.cos(proj.angle)
            proj_dir_y = math.sin(proj.angle)

            perp_x = -proj_dir_y
            perp_y = proj_dir_x

            arena_dx = ARENA_CENTER_X - player.x
            arena_dy = ARENA_CENTER_Y - player.y
            arena_distance = (arena_dx**2 + arena_dy**2) ** 0.5

            if arena_distance > ARENA_RADIUS * 0.7:
                to_center_x = arena_dx / (arena_distance or 1)
                to_center_y = arena_dy / (arena_distance or 1)

                dot_product = to_center_x * perp_x + to_center_y * perp_y
                if dot_product < 0:
                    perp_x = -perp_x
                    perp_y = -perp_y
            elif random.random() < 0.5:
                perp_x = -perp_x
                perp_y = -perp_y

            ai_keys["right"] = perp_x > 0
            ai_keys["left"] = perp_x < 0
            ai_keys["down"] = perp_y > 0
            ai_keys["up"] = perp_y < 0
            ai_keys["dash"] = True

            if time_to_hit < 15:
                ai_keys["shield"] = random.random() < 0.7

            if is_player1:
                self.game.ai_move_timer1 = 0
                self.game.ai_move_direction1 = {
                    "up": ai_keys["up"],
                    "down": ai_keys["down"],
                    "left": ai_keys["left"],
                    "right": ai_keys["right"],
                    "dash": ai_keys["dash"],
                }
            else:
                self.game.ai_move_timer2 = 0
                self.game.ai_move_direction2 = {
                    "up": ai_keys["up"],
                    "down": ai_keys["down"],
                    "left": ai_keys["left"],
                    "right": ai_keys["right"],
                    "dash": ai_keys["dash"],
                }

            return ai_keys

        if ai_timer >= self.game.ai_move_interval:
            self.decide_movement_style(player, opponent, is_player1)
            if is_player1:
                self.game.ai_move_timer1 = 0
            else:
                self.game.ai_move_timer2 = 0

        ai_keys["up"] = ai_direction["up"]
        ai_keys["down"] = ai_direction["down"]
        ai_keys["left"] = ai_direction["left"]
        ai_keys["right"] = ai_direction["right"]
        ai_keys["dash"] = ai_direction["dash"]

        if random.random() < 0.4:
            ai_keys["weapon_a"] = True
        if random.random() < 0.3:
            ai_keys["weapon_b"] = True
        if random.random() < 0.1:
            ai_keys["special"] = True

        shield_chance = 0.1
        if self.is_projectile_nearby(player, 70):
            shield_chance = 0.7
        ai_keys["shield"] = random.random() < shield_chance

        if player.hyper_gauge >= 100 and random.random() < 0.3:
            ai_keys["hyper"] = True

        return ai_keys

    def decide_movement_style(self, player, opponent, is_player1):
        dx = opponent.x - player.x
        dy = opponent.y - player.y
        distance = (dx**2 + dy**2) ** 0.5

        arena_dx = ARENA_CENTER_X - player.x
        arena_dy = ARENA_CENTER_Y - player.y

        movement = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "dash": random.random() < 0.4,
        }

        move_style = random.randint(0, 10)

        if move_style <= 5:
            if distance > 150:
                movement["right"] = dx > 0
                movement["left"] = dx < 0
                movement["down"] = dy > 0
                movement["up"] = dy < 0
            else:
                movement["left"] = dx > 0
                movement["right"] = dx < 0
                movement["up"] = dy > 0
                movement["down"] = dy < 0
        elif move_style <= 7:
            clockwise = random.random() < 0.5
            if clockwise:
                movement["left"] = dy > 0
                movement["right"] = dy < 0
                movement["up"] = dx > 0
                movement["down"] = dx < 0
            else:
                movement["left"] = dy < 0
                movement["right"] = dy > 0
                movement["up"] = dx < 0
                movement["down"] = dx > 0
        elif move_style <= 8:
            movement["right"] = arena_dx > 0
            movement["left"] = arena_dx < 0
            movement["down"] = arena_dy > 0
            movement["up"] = arena_dy < 0
        else:
            vertical = random.choice(["up", "down", "none"])
            horizontal = random.choice(["left", "right", "none"])
            if vertical != "none":
                movement[vertical] = True
            if horizontal != "none":
                movement[horizontal] = True
            if not any([movement["up"], movement["down"], movement["left"], movement["right"]]):
                movement[random.choice(["up", "down", "left", "right"])] = True

        if is_player1:
            self.game.ai_move_direction1 = movement
        else:
            self.game.ai_move_direction2 = movement

    def predict_projectile_collision(self, player):
        closest_hit_time = float("inf")
        closest_projectile = None
        hit_position = None

        for proj in self.game.projectiles:
            if proj.owner == player:
                continue

            proj_vx = math.cos(proj.angle) * proj.speed
            proj_vy = math.sin(proj.angle) * proj.speed

            dx = player.x - proj.x
            dy = player.y - proj.y

            a = proj_vx * proj_vx + proj_vy * proj_vy
            b = 2 * (proj_vx * dx + proj_vy * dy)
            c = dx * dx + dy * dy - (player.radius + proj.radius) * (player.radius + proj.radius)

            discriminant = b * b - 4 * a * c
            if discriminant < 0 or a <= 0:
                continue

            t1 = (-b - math.sqrt(discriminant)) / (2 * a)
            t2 = (-b + math.sqrt(discriminant)) / (2 * a)

            hit_time = None
            if t1 > 0:
                hit_time = t1
            elif t2 > 0:
                hit_time = t2

            if hit_time is not None and hit_time < closest_hit_time and hit_time < 60:
                closest_hit_time = hit_time
                closest_projectile = proj
                hit_position = (proj.x + proj_vx * hit_time, proj.y + proj_vy * hit_time)

        if closest_projectile and hit_position:
            return (closest_projectile, closest_hit_time, hit_position[0], hit_position[1])
        return None

    def is_projectile_nearby(self, player, distance_threshold):
        for proj in self.game.projectiles:
            if proj.owner == player:
                continue
            dx = player.x - proj.x
            dy = player.y - proj.y
            if (dx**2 + dy**2) ** 0.5 < distance_threshold:
                return True
        return False

    def simple_ai_control(self):
        ai_keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "weapon_a": False,
            "weapon_b": False,
            "hyper": False,
            "dash": False,
            "special": False,
            "shield": False,
        }

        dx = self.game.player1.x - self.game.player2.x
        dy = self.game.player1.y - self.game.player2.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance > 150:
            ai_keys["right"] = dx > 0
            ai_keys["left"] = dx <= 0
            ai_keys["down"] = dy > 0
            ai_keys["up"] = dy <= 0
            if self.game.current_time % 60 == 0:
                ai_keys["weapon_a"] = True
        else:
            ai_keys["left"] = dx > 0
            ai_keys["right"] = dx <= 0
            ai_keys["up"] = dy > 0
            ai_keys["down"] = dy <= 0
            if self.game.current_time % 30 == 0:
                ai_keys["weapon_a"] = True
            if self.game.current_time % 90 == 0:
                ai_keys["weapon_b"] = True
            if self.game.current_time % 120 == 0:
                ai_keys["dash"] = True
            if self.game.player2.hyper_gauge >= 100 and self.game.current_time % 180 == 0:
                ai_keys["hyper"] = True

        return ai_keys
