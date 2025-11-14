from classes import PrefabData, EnvironmentData, AttackData, StaticObject, Weapon
from markov import MarkovNode, MarkovChain
from waiting_lines import WaitingLinesArrival
from random_walk import random_choice
from montecarlo import montecarlo
from typing import Callable, Awaitable
import math
import random
from asyncio import sleep, Lock

class GameManager:
    def __init__(self, width: int, height: int):
        self.environment = EnvironmentData(width, height)
        self.terminate = False
        self.enemies_counter = 0
        self.default_enemies = 5
        self.waves = 3
        self.waves_waiting_time = 4
        self.__init_markov_chain()
        self.static_objects_index = 0
        self.attack_count_id = 0
        self.weapons_counter = 0
        self.leaved_weapons: list[Weapon] = []
        self.waiting_lines_arrival = WaitingLinesArrival(5) # valor default 5 de lamda en llegadas/minuto
        self.__init_data()
        self.enemies_lock = Lock()
        self.static_objects_lock = Lock()
        self.characters_attacks_locks = {}

    def __init_data(self):
        self.torch_generation_points = [
            (self.environment.width*0.2, self.environment.height*0.07),
            (self.environment.width*0.4, self.environment.height*0.07), 
            (self.environment.width*0.6, self.environment.height*0.07),
            (self.environment.width*0.8, self.environment.height*0.07),
            (self.environment.width*0.04, self.environment.height*0.25),
            (self.environment.width*0.04, self.environment.height*0.5),
            (self.environment.width*0.04, self.environment.height*0.75),
            (self.environment.width*0.96, self.environment.height*0.25),
            (self.environment.width*0.96, self.environment.height*0.5),
            (self.environment.width*0.96, self.environment.height*0.75)
        ]
        self.chest_generation_points = [
            (self.environment.width*0.11, self.environment.height*0.22),
            (self.environment.width*0.5, self.environment.height*0.22),
            (self.environment.width*0.89, self.environment.height*0.22),
            (self.environment.width*0.11, self.environment.height*0.5),
            (self.environment.width*0.36, self.environment.height*0.5),
            (self.environment.width*0.63, self.environment.height*0.5),
            (self.environment.width*0.89, self.environment.height*0.5),
            (self.environment.width*0.11, self.environment.height*0.83),
            (self.environment.width*0.5, self.environment.height*0.83),
            (self.environment.width*0.89, self.environment.height*0.83)
        ]
        self.players_restricted_limits = [
            self.environment.width*0.09,
            self.environment.width*0.91,
            self.environment.height*0.2,
            self.environment.height*0.88
        ]
        self.__generate_torches()

    def add_player(self, id: str):
        x, y = int(self.__get_ni_number(self.players_restricted_limits[0], 
                                    self.players_restricted_limits[1])), int(self.__get_ni_number(
                                        self.players_restricted_limits[2], 
                                        self.players_restricted_limits[3]))
        player = PrefabData(x, y, 'right', 1500, id)
        self.environment.characters.append(player)
        self.characters_attacks_locks[id] = Lock()

    def generate_player_weapons(self):
        for character in self.environment.characters:
            sub_mun, sub_dm = self.munition_info['submachine']
            rifle_mun, rifle_dm = self.munition_info['rifle']
            shotgun_mun, shotgun_dm = self.munition_info['shotgun']
            raygun_mun, raygun_dm = self.munition_info['raygun']
            id1, id2, id3, id4 = self.weapons_counter, self.weapons_counter + 1, self.weapons_counter + 2, self.weapons_counter + 3
            self.weapons_counter += 4
            character.weapons.extend([
                Weapon(id1, character.x, character.y, 'submachine', sub_mun, sub_dm),
                Weapon(id2, character.x, character.y, 'rifle', rifle_mun, rifle_dm),
                Weapon(id3, character.x, character.y, 'shotgun', shotgun_mun, shotgun_dm),
                Weapon(id4, character.x, character.y, 'raygun', raygun_mun, raygun_dm)
            ])

    def change_player_weapon(self, id: str):
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                character.current_weapon_index = (character.current_weapon_index + 1) % 4
                weapon = character.weapons[character.current_weapon_index]
                weapon.set_position(character.x, character.y)
                return weapon

    def add_weapon_to_player(self, id: str):
        player = None
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                player = character
                break
        else:
            return None
        weapons_leaved : list[Weapon] = list(filter(lambda x: (((x.x - player.x)**2 + (x.y - player.y)**2)**0.5) <= 70, 
                                     self.leaved_weapons))
        if len(weapons_leaved) > 0 and len(player.weapons) < 4:
            weapon = weapons_leaved[0]
            self.leaved_weapons.remove(weapon)
            player.weapons.append(weapon)
            weapon.set_position(player.x, player.y)
            return weapon
        return None
    
    def leave_player_weapon(self, id: str):
        player = None
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                player = character
                break
        else:
            return None
        weapon = player.weapons[player.current_weapon_index]
        player.weapons.remove(weapon)
        self.leaved_weapons.append(weapon)
        if player.current_weapon_index >= len(player.weapons):
            player.current_weapon_index = player.current_weapon_index - 1
        return weapon

    async def open_chest(self, id: str):
        player = None
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                player = character
                break
        else:
            return None
        async with self.static_objects_lock:
            static_ob_list = self.environment.static_objects.copy()
        chests = list(filter(lambda x: x.chest_type is not None and (
            ((x.x - player.x)**2 + (x.y - player.y)**2)**0.5) <= 70, 
            static_ob_list))
        if len(chests) > 0:
            chest = chests[0]
            async with self.static_objects_lock:
                self.environment.static_objects.remove(chest)
            res = self.__get_and_put_reward(chest.chest_type, player, chest.x, chest.y)
            return chest, res
        return None
    
    munition_info = {
        "submachine": (250, 5),
        "rifle": (175, 7),
        "shotgun": (90, 30),
        "raygun": (50, 80)
    }
    
    def __get_and_put_reward(self, chest_type: str, player: PrefabData, x: int, y: int):
        if chest_type == 'munition':
            current_weapon = player.weapons[player.current_weapon_index]
            to_add = 60 if current_weapon.remaining_munition + 60 <= current_weapon.max_munition else current_weapon.max_munition - current_weapon.remaining_munition
            current_weapon.remaining_munition += to_add
            return current_weapon
        elif chest_type == 'health':
            to_add = 40 if player.life + 40 <= player.max_life else player.max_life - player.life
            player.life += to_add
            return player
        else:
            max_mn, bullet_dm = self.munition_info[chest_type]
            weapon = Weapon(self.weapons_counter, x, y, chest_type, max_mn, bullet_dm)
            self.weapons_counter += 1
            self.leaved_weapons.append(weapon)
            return weapon

    def move_player(self, id: str, direction: str) -> PrefabData | None:
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                restriccions = [
                    character.x < self.players_restricted_limits[0],
                    character.x > self.players_restricted_limits[1],
                    character.y < self.players_restricted_limits[2],
                    character.y > self.players_restricted_limits[3]
                ]
                self.__move_prefab(character, direction, restriccions)
                character.weapons[character.current_weapon_index].set_position(character.x, character.y)
                return character
        return None

    def __move_enemy(self, id: str, direction: str):
        for enemy in self.environment.enemies:
            if enemy.id == id:
                restriccions = [
                    enemy.x < enemy.speed,
                    enemy.x > self.environment.width - enemy.speed,
                    enemy.y < enemy.speed,
                    enemy.y > self.environment.height - enemy.speed
                ]
                enemy.frame_direction = direction
                if direction != 'right' and direction != 'left':
                    enemy.frame_direction = "right" if "right" == enemy.direction else "left"
                self.__move_prefab(enemy, direction, restriccions)
                break

    def __move_prefab(self, prefab: PrefabData, direction: str, restriccions : list[bool]):
        prefab.direction = direction
        if direction == "up" and (not restriccions[2]):
            prefab.y -= prefab.speed
        elif direction == "down" and (not restriccions[3]):
            prefab.y += prefab.speed
        elif direction == "left" and (not restriccions[0]):
            prefab.x -= prefab.speed
        elif direction == "right" and (not restriccions[1]):
            prefab.x += prefab.speed

    def __generate_torches(self):
        indices = set()
        while len(indices) < 4:
            idx = int(self.__get_ni_number(0, len(self.torch_generation_points) - 1))
            if idx not in indices:
                indices.add(idx)
        for idx in indices:
            point = self.torch_generation_points[idx]
            torch = StaticObject(self.static_objects_index, int(point[0]), int(point[1]))
            self.environment.static_objects.append(torch)
            self.static_objects_index += 1

    async def __generate_chest(self, chest_generation_function: Callable[[StaticObject], Awaitable[None]]):
        if len(self.environment.static_objects) - 4 < len(self.chest_generation_points):
            type = self.__get_chest_type()
            x, y = self.chest_generation_points[int(self.__get_ni_number(0, len(self.chest_generation_points)))]
            async with self.static_objects_lock:
                static_ob_list = self.environment.static_objects.copy()
            chests = list(filter(lambda x: x.chest_type is not None and x.x == int(x) and x.y == int(y), static_ob_list))
            while len(chests) > 0:
                x, y = self.chest_generation_points[int(self.__get_ni_number(0, len(self.chest_generation_points)))]
                async with self.static_objects_lock:
                    static_ob_list = self.environment.static_objects.copy()
                chests = list(filter(lambda x: x.chest_type is not None and x.x == int(x) and x.y == int(y), static_ob_list))
            chest = StaticObject(self.static_objects_index, int(x), int(y), type)
            self.static_objects_index += 1
            async with self.static_objects_lock:
                self.environment.static_objects.append(chest)
            await chest_generation_function(chest)

    async def generate_waves_and_enemies(self, enemy_generation_function: Callable[[PrefabData], Awaitable[None]],
                          new_wave_function: Callable[[int, bool, list[PrefabData] | None, list[StaticObject] | None], Awaitable[None]], 
                          game_won_function: Callable[[], Awaitable[None]]):
        await new_wave_function(1, False, self.environment.characters.copy(), 
                                self.environment.static_objects.copy())
        for i in range(1, self.waves + 1):
            await sleep(self.waves_waiting_time)
            enemies_amount = self.default_enemies
            enemies_amount += int(self.__get_ni_number(i, i*3))
            await self.__waiting_lines_enemies_generation(enemy_generation_function, enemies_amount)
            if self.terminate:
                return
            while len(self.environment.enemies) > 0:
                if self.terminate:
                    return
            else:
                await new_wave_function(i + 1, i + 1 > self.waves, None, None)
        await sleep(60)
        async with self.static_objects_lock:
            self.environment.static_objects.clear()#
            self.__generate_torches()#
            await new_wave_function(4, False, self.environment.characters.copy(), #
                                self.environment.static_objects.copy())
        await enemy_generation_function(self.__generate_final_enemy())
        while len(self.environment.enemies) > 0:
            if self.terminate:
                return
        await game_won_function()

    async def __waiting_lines_enemies_generation(self, enemy_generation_function: Callable[[PrefabData], Awaitable[None]], enemies_amount: int):
        enemy_counter = 0
        while enemy_counter < enemies_amount:
            if self.terminate:
                return
            en= self.__generate_enemy()
            await enemy_generation_function(en)
            enemy_counter += 1
            ri = random.random()
            segs = self.waiting_lines_arrival.next_arrival_interval_time(ri) * 60 # minutos a segundos
            await sleep(segs)

    def __generate_enemy(self):
        type, life, speed = self.__get_montecarlo_enemy()
        self.enemies_counter += 1
        id = f"{self.enemies_counter}"
        x, y = self.__get_montecarlo_enemy_position()
        enemy = PrefabData(x, y, 'right', life, type=type, speed=speed, id=id)
        self.environment.add_enemy(enemy)
        return enemy

    def __get_montecarlo_enemy_position(self):
        num = random.random()
        height = self.environment.height
        width = self.environment.width
        position_distribution = [
            (lambda: (0, int(self.__get_ni_number(0, height))), 0.25),
            (lambda: (width, int(self.__get_ni_number(0, height))), 0.25),
            (lambda: (int(self.__get_ni_number(0, width)), height), 0.25),
            (lambda: (int(self.__get_ni_number(0, width)), 0), 0.25)
        ]
        selected_position = montecarlo(position_distribution, num)
        return selected_position()

    def __get_montecarlo_enemy(self):
        num = random.random()
        enemy_distribution = [
            (("type1", 150, 7), 0.45),
            (("type2", 125, 9), 0.35),
            (("type3", 100, 4), 0.20)
        ]
        return montecarlo(enemy_distribution, num)

    def __generate_final_enemy(self):
        life = 2000
        speed = 6
        id = "0"
        x, y = self.__get_montecarlo_enemy_position()
        enemy = PrefabData(x, y, 'right', life, type="final", speed=speed, id=id)
        self.environment.add_enemy(enemy)
        return enemy

    def do_player_shoot(self, id: str):
        for character in self.environment.characters:
            if character.id == id and character.life > 0:
                current_weapon = character.weapons[character.current_weapon_index]
                if current_weapon.remaining_munition == 0:
                    return None, None
                data = self.__do_prefab_attack(character, "shoot", current_weapon.bullet_damage, is_enemy=False)
                current_weapon.remaining_munition -= 1
                return data, character
        return None, None

    def __do_prefab_attack(self, prefab: PrefabData, type: str, damage: int, is_enemy: bool = True):
        if type == "melee":
            width, _ = prefab.max_dimensions[prefab.frame_direction]
            x = prefab.x + (width // 2) if "right" in prefab.frame_direction else prefab.x - (width // 2)
            data = AttackData(self.attack_count_id, x, prefab.y, damage, prefab.direction, "melee")
            prefab.attacks.append(data)
            self.attack_count_id += 1
        else:
            x = (prefab.x + (40 if "right" in prefab.frame_direction else -40)) if is_enemy else prefab.x
            y = prefab.y - (40 if is_enemy else 35)
            data = AttackData(self.attack_count_id, x, y, damage, prefab.direction, type)
            prefab.attacks.append(data)
            self.attack_count_id += 1
        return data

    async def move_shoots_attacks(self, shoots_move_func: Callable[[list[AttackData], list[AttackData]], Awaitable[None]]):
        enemies_shoots_list = []
        async with self.enemies_lock:
            enemies_list = self.environment.enemies.copy()
        for prefab in enemies_list:
            attacks = list(filter(lambda x: x.alive and x.type != "melee", prefab.attacks))
            for attack in attacks:
                self.__do_shoot_attack_move(attack)
            enemies_shoots_list.extend(attacks)
        players_shoots_list = []
        for prefab in self.environment.characters:
            async with self.characters_attacks_locks[prefab.id]:
                attacks_list = prefab.attacks.copy()
            attacks = list(filter(lambda x: x.alive, attacks_list))
            for attack in attacks:
                self.__do_shoot_attack_move(attack)
            players_shoots_list.extend(attacks)
        await shoots_move_func(enemies_shoots_list, players_shoots_list)

    def __do_shoot_attack_move(self, attack: AttackData):
        if attack.direction == "right":
            attack.x += 50
        elif attack.direction == "left":
            attack.x -= 50
        elif attack.direction == "up":
            attack.y -= 50
        elif attack.direction == "down":
            attack.y += 50

    async def evaluate_character_position_action(self, attack_function: Callable[[str, AttackData], Awaitable[None]], 
                                           move_function: Callable[[PrefabData], Awaitable[None]],
                                           enemy_generation_function: Callable[[PrefabData], Awaitable[None]]):
        ob_sp = self.environment.get_observation_space()
        async with self.enemies_lock:
            enemies_list = self.environment.enemies.copy()
        for en in enemies_list:
            type = en.type
            if type == "type1":
                action, type_action = self.__do_enemy_type1_action_policy(en, ob_sp)
            elif type == "type2":
                action, type_action = self.__do_enemy_type2_action_policy(en, ob_sp)
            elif type == "type3":
                action, type_action = self.__do_enemy_type3_action_policy(en, ob_sp)
            elif type == "final":
                action, type_action = await self.__do_final_enemy_action_policy(en, ob_sp, enemy_generation_function)
                if action is None:
                    continue
            if action == "attack":
                damage = 15 if type_action == "melee" else 25 if type_action == "enemy_3_shoot" else 40 
                data = self.__do_prefab_attack(en, type_action, damage, is_enemy=True)
                await attack_function(en.id, data)
            else:
                self.__move_enemy(en.id, type_action)
                await move_function(en)

    def __get_nearlest_player(self, observation_space: list[tuple[int, int, int, int, int, int]], 
                              pos_x: int, pos_y: int) -> tuple[int, int, int, int, int, int]:
        return min(observation_space, key=lambda x: ((x[0] - pos_x)**2 + (x[1] - pos_y)**2))

    def __do_enemy_type1_action_policy(self, enemy: PrefabData, 
                                       observation_space: list[tuple[int, int, int, int, int, int]]):
        action, ob_x, ob_y, x, x_width = self.__calculate_melee_attack(enemy, observation_space)
        if action == "attack":
            return action, "melee"
        x_diff = ob_x - x
        y_diff = ob_y - enemy.y
        move = self.__calculate_move_direction(x_diff, y_diff, x_width, speed=enemy.speed)
        return "move", move if move else enemy.frame_direction

    def __do_enemy_type2_action_policy(self, enemy: PrefabData, 
                                       observation_space: list[tuple[int, int, int, int, int, int]]):
        action, ob_x, ob_y, x, x_width = self.__calculate_melee_attack(enemy, observation_space)
        if action == "attack":
            return action, "melee"
        enemy.in_strategy = (enemy.life / enemy.max_life) > 0.7 and not self.__is_close_to_player(ob_x, ob_y, x, enemy.y, x_width)
        if enemy.in_strategy:
            return "move", self.__two_dimension_random_walk()
        else:
            x_diff = ob_x - x
            y_diff = ob_y - enemy.y
            move = self.__calculate_move_direction(x_diff, y_diff, x_width, speed=enemy.speed)
            return "move", move if move else enemy.frame_direction

    def __do_enemy_type3_action_policy(self, enemy: PrefabData, 
                                       observation_space: list[tuple[int, int, int, int, int, int]]):
        action, ob_x, ob_y, x, x_width = self.__calculate_shoot_attack(enemy, observation_space)
        if action == "attack":
            return action, "enemy_3_shoot"
        x_diff = ob_x - x
        y_diff = ob_y - enemy.y + 40
        move = self.__calculate_move_direction(x_diff, y_diff, x_width, speed=enemy.speed)
        return "move", move if move else enemy.frame_direction

    async def __do_final_enemy_action_policy(self, enemy: PrefabData, 
                                       observation_space: list[tuple[int, int, int, int, int, int]],
                                       enemy_generation_function: Callable[[PrefabData], Awaitable[None]]):
        action, ob_x, ob_y, x_melee, x_width = self.__calculate_melee_attack(enemy, observation_space)
        if action == "attack":
            return action, "melee"
        action, ob_x, ob_y, _, _ = self.__calculate_shoot_attack(enemy, observation_space)
        if action == "attack":
            return action, "final_enemy_shoot"
        if enemy.generation_enemies_counter == 200:
            en = self.__generate_enemy()
            await enemy_generation_function(en)
            enemy.generation_enemies_counter = 0
            return None, None
        enemy.generation_enemies_counter += 1
        enemy.in_strategy = (enemy.life / enemy.max_life) > 0.7 and not self.__is_close_to_player(ob_x, ob_y, x_melee, enemy.y, x_width)
        if enemy.in_strategy:
            return "move", self.__two_dimension_random_walk()
        else:
            x_diff = ob_x - x_melee
            y_diff = ob_y - enemy.y
            move = self.__calculate_move_direction(x_diff, y_diff, x_width, speed=enemy.speed)
            return "move", move if move else enemy.frame_direction

    directions = ["left", "up", "right", "down"]
    
    def __two_dimension_random_walk(self):
        return random_choice(self.directions, rand_num=random.random())

    def __calculate_melee_attack(self, enemy: PrefabData, 
                                 observation_space: list[tuple[int, int, int, int, int, int]]):
        ob_x, ob_y, ob_max_x, ob_min_x, ob_max_y, ob_min_y = self.__get_nearlest_player(observation_space, enemy.x, enemy.y)
        x_width, _ = enemy.max_dimensions[enemy.frame_direction] if enemy.max_dimensions else (0, 0)
        x = enemy.x - (x_width // 2) if enemy.frame_direction == "left" else enemy.x + (x_width // 2)
        if x >= ob_min_x and x <= ob_max_x and enemy.y >= ob_min_y and enemy.y <= ob_max_y:
            return "attack", ob_x, ob_y, x, x_width
        return "move", ob_x, ob_y, x, x_width
    
    def __calculate_shoot_attack(self, enemy: PrefabData, 
                                 observation_space: list[tuple[int, int, int, int, int, int]]):
        ob_x, ob_y, ob_max_x, ob_min_x, ob_max_y, ob_min_y = self.__get_nearlest_player(observation_space, enemy.x, enemy.y)
        x_width, _ = enemy.max_dimensions[enemy.frame_direction] if enemy.max_dimensions else (0, 0)
        x, y = enemy.x + 40 if enemy.frame_direction == "right" else enemy.x - 40, enemy.y - 40
        direction = enemy.direction
        lim = enemy.speed * 2
        on_x = x >= ob_min_x + lim and x <= ob_max_x - lim
        on_y = y >= ob_min_y + lim and y <= ob_max_y - lim
        if (direction == "right" and x <= ob_min_x + lim and on_y) or \
            (direction == "left" and x >= ob_max_x - lim and on_y) or \
            (direction == "up" and y >= ob_max_y - lim and on_x) or \
            (direction == "down" and y <= ob_min_y + lim and on_x):
            return "attack", ob_x, ob_y, x, x_width
        return "move", ob_x, ob_y, x, x_width

    def __calculate_move_direction(self, x_diff, y_diff, value, speed=5):
        abs_x_diff = abs(x_diff)
        abs_y_diff = abs(y_diff)
        if abs_x_diff > abs_y_diff and abs_x_diff > value:
            if x_diff > 0:
                return "right"
            else:
                return "left"
        else:
            if abs_y_diff <= speed:
                return None
            if y_diff > 0:
                return "down"
            else:
                return "up"
        
    def __is_close_to_player(self, ob_x: int, ob_y: int, x: int, y: int, x_width: int):
        euclidean_distance = math.sqrt((ob_x - x) ** 2 + (ob_y - y) ** 2)
        return euclidean_distance <= x_width * 1.5

    async def evaluate_attacks(self, chest_generation_function: Callable[[StaticObject], Awaitable[None]], 
                         enemy_defeted_function: Callable[[PrefabData, str], Awaitable[None]], 
                         character_death_function: Callable[[PrefabData], Awaitable[None]], 
                         game_over_function: Callable[[], Awaitable[None]], 
                         damage_function: Callable[[PrefabData, bool, AttackData, str], Awaitable[None]]):
        characters = list(filter(lambda x: x.life > 0, self.environment.characters))
        for character in characters:
            # verificar disparos a jugador
            async with self.enemies_lock:
                enemies_list = self.environment.enemies.copy()
            for en in enemies_list:
                en_shoots = list(filter(lambda x: x.alive, en.attacks))
                for shoot in en_shoots:
                    if self.__verify_shoot_damage(shoot, character, False):
                        shoot.alive = False
                        await damage_function(character, False, shoot, en.id)
                    elif shoot.type == "melee":
                        shoot.alive = False
                    elif shoot.x > self.environment.width or shoot.x < 0 or shoot.y > self.environment.height or shoot.y < 0:
                        shoot.alive = False
                    if character.life <= 0:
                        await character_death_function(character)
                        list_characters = list(filter(lambda x: x.life > 0, self.environment.characters))
                        if len(list_characters) == 0:
                            self.terminated = True
                            await game_over_function()
                            return
                        break
                if character.life <= 0:
                    break
            # verificar disparos a enemigos
            async with self.characters_attacks_locks[character.id]:
                attacks_list = character.attacks.copy()
            character_shoots = list(filter(lambda x: x.alive, attacks_list))
            for shoot in character_shoots:
                async with self.enemies_lock:
                    enemies_list = self.environment.enemies.copy()
                for en in enemies_list:
                    if self.__verify_shoot_damage(shoot, en, True):
                        shoot.alive = False
                        await damage_function(en, True, shoot, character.id)
                        if en.life <= 0:
                            async with self.enemies_lock:
                                self.environment.enemies.remove(en)
                            await enemy_defeted_function(en, character.id)
                            character.character_points += 10
                            character.total_character_points += 10          
                            if character.character_points == 20:
                                await self.__generate_chest(chest_generation_function)
                                character.character_points = 0
                        break
                    elif shoot.x > self.environment.width or shoot.x < 0 or shoot.y > self.environment.height or shoot.y < 0:
                        shoot.alive = False
    
    def __get_ni_number(self, a, b):
        ri = random.random()
        return a + (b - a) * ri
    
    def __verify_shoot_damage(self, shoot: AttackData, to: PrefabData, is_enemy: bool)-> bool:
        if is_enemy:
            direction_to = to.frame_direction
        else:
            direction_to = to.direction
        X, Y = to.max_dimensions[direction_to]
        if shoot.direction == "left" or shoot.direction == "right":
            if to.x - (X * 0.5) <= shoot.x and to.x + (X * 0.5) >= shoot.x:
                is_hit, interval = self.__verify_and_get_shoot_interval(Y, to.y, shoot.y)
            else:
                return False
        else:
            if to.y - (Y * 0.5) <= shoot.y and to.y + (Y * 0.5) >= shoot.y:
                is_hit, interval = self.__verify_and_get_shoot_interval(X, to.x, shoot.x)
            else:
                return False
        if is_hit:
            value = to.life - (shoot.damage - interval - self.__get_montecarlo_damage())
            to.life = value if value >= 0 else 0
            return True
        return False

    def __verify_and_get_shoot_interval(self, dim: int, pos: int, shoot_pos: int)-> tuple[bool, int]:
        a_min, a_max = pos - (dim * 0.05), pos + (dim * 0.05)
        b_min, b_max = pos - (dim * 0.25), pos + (dim * 0.25)
        c_min, c_max = pos - (dim * 0.5), pos + (dim * 0.5)
        if shoot_pos >= a_min and shoot_pos <= a_max:
            return True, 0
        elif shoot_pos >= b_min and shoot_pos <= b_max:
            return True, 1
        elif shoot_pos >= c_min and shoot_pos <= c_max:
            return True, 2
        return False, 0
    
    def __get_montecarlo_damage(self):
        num = random.random()
        damage_distribution = [
            (2, 0.5),   # 50% probabilidad de hacer 2 de daño
            (1, 0.35),  # 35% probabilidad de hacer 1 de daño
            (0, 0.15)   # 15% probabilidad de no hacer daño
        ]
        return montecarlo(damage_distribution, num)
        
    def __get_montecarlo_weapon(self):
        num = random.random()
        weapon_distribution = [
            ("submachine", 0.5),
            ("rifle", 0.3),
            ("shotgun", 0.15),
            ("raygun", 0.05)
        ]
        return montecarlo(weapon_distribution, num)
        
    def __init_markov_chain(self):
    # Crea la matriz de nodos (cada fila representa el estado actual)
        munition_row = [
            MarkovNode(value="munition", state=1, probability=0.3),
            MarkovNode(value="health", state=2, probability=0.3),
            MarkovNode(value="weapon", state=3,probability=0.4),
        ]
        health_row = [
            MarkovNode(value="munition", state=1, probability=0.3),
            MarkovNode(value="health", state=2, probability=0.2),
            MarkovNode(value="weapon", state=3, probability=0.5),
        ]
        weapon_row = [
            MarkovNode(value="munition", state=1, probability=0.35),
            MarkovNode(value="health", state=2, probability=0.55),
            MarkovNode(value="weapon", state=3, probability=0.1),
        ]

        self.chain = MarkovChain(
            markov_nodes=[munition_row, health_row, weapon_row],
            initial_state=munition_row[0]  # puede ser cualquiera
        )

    def __get_reward(self):
        num = random.random()
        self.chain.set_state(num)
        return self.chain.current_state.value
        
    def __get_chest_type(self):
        type = self.__get_reward()
        if type == "weapon":
            type = self.__get_montecarlo_weapon()
        return type