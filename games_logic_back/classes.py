
class Weapon:
    def __init__(self, id: int, x: int, y: int, type: str, max_munition: int, bullet_damage: int):
        self.id = id
        self.x = x
        self.y = y - 35
        self.type = type # submachine, rifle, shotgun, raygun
        self.max_munition = max_munition
        self.remaining_munition = max_munition
        self.bullet_damage = bullet_damage
        self.max_dimensions = {'left': (114, 44), 'right': (114, 44), 'up': (20, 66), 'down': (20, 66)}

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y - 35

class AttackData:
    def __init__(self, id: int, x: int, y: int, damage: int, direction: str, type: str):
        self.id = id
        self.x = x
        self.y = y
        self.damage = damage
        self.direction = direction
        self.type = type  # melee, enemy_3_shoot, final_enemy_shoot, submachine, rifle, shotgun, raygun
        self.alive = True
        if type in ["enemy_3_shoot", "final_enemy_shoot"]:
            self.max_dimensions = {'left': (30, 30), 'right': (30, 30), 'up': (30, 30), 'down': (30, 30)}
        elif type in ["shotgun", "raygun"]:
            self.max_dimensions = {'left': (8, 8), 'right': (8, 8), 'up': (8, 8), 'down': (8, 8)}
        else:
            self.max_dimensions = {'left': (4, 4), 'right': (4, 4), 'up': (4, 4), 'down': (4, 4)}

class PrefabData:
    def __init__(self, x: int, y: int, direction: str, life: int, id: str,
                 frame_direction: str = "right", type: str | None = None, speed: int = 5):
        self.id = id
        self.x = x
        self.y = y
        self.direction = direction
        self.life = life
        self.max_life = life
        if type == "type1":
            self.max_dimensions = {'left': (178, 202), 'right': (178, 202)}
        elif type == "type2":
            self.max_dimensions = {'left': (141, 160), 'right': (141, 160)}
        elif type == "type3":
            self.max_dimensions = {'left': (165, 196), 'right': (165, 196)}
        elif type == "final":
            self.max_dimensions = {'left': (184, 207), 'right': (184, 207)}
        else:
            self.max_dimensions = {'up': (40, 80), 'down': (40, 94), 'left': (112, 72), 'right': (112, 72), 'up_beaten': (40, 80), 'down_beaten': (40, 94), 'left_beaten': (112, 72), 'right_beaten': (112, 72)}
        self.attacks: list[AttackData] = []
        self.weapons: list[Weapon] = []
        self.frame_direction = frame_direction
        self.type = type # tipos: type1, type2, type3, final, (None en caso del jugador)
        self.in_strategy = True
        self.speed = speed
        self.generation_enemies_counter = 0
        self.character_points = 0
        self.total_character_points = 0
        self.current_weapon_index = 0

class StaticObject:
    def __init__(self, id: int, x: int, y: int, chest_type: str | None = None):
        self.id = id
        self.x = x
        self.y = y
        self.chest_type = chest_type # None si es torch
        if chest_type:
            self.max_dimensions = {'base': (62, 64), 'health': (40, 36), 'munition': (40, 32)}
        else:
            self.max_dimensions = {'base': (140, 140)}

class EnvironmentData:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.characters: list[PrefabData] = []
        self.enemies: list[PrefabData] = []
        self.static_objects: list[StaticObject] = []

    def get_observation_space(self) -> list[tuple[int, int, int, int, int, int]]:
        """Devuelve el espacio de observación, para los agentes, pocision y limites de jugadores 
        List[(x, y, x_max, x_min, y_max, y_min)]."""
        space = []
        for character in self.characters:
            x, y = character.x, character.y
            width, height = character.max_dimensions[character.direction]
            max_x, min_x = x + (width//2), x - (width//2)
            max_y, min_y = y + (height//2), y - (height//2)
            space.append((x, y, max_x, min_x, max_y, min_y))
        return space

    def add_enemy(self, enemy: PrefabData) -> None:
        """Agrega un enemigo al entorno."""
        self.enemies.append(enemy)