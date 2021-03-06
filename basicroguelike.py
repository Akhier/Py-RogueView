import libtcodpy as libtcod
import math
import textwrap
import shelve
from Console import Console
from Panel import Panel

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

MAP_WIDTH = 80
MAP_HEIGHT = 43

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

LIMIT_FPS = 20

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)


class Tile:

    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        self.explored = False

        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


class Rect:

    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Object:

    def __init__(self, x, y, char, name, color, blocks=False,
                 always_visible=False, fighter=None, ai=None,
                 item=None, equipment=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self

            self.item = Item()
            self.item.owner = self

    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def draw(self):
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or
                (self.always_visible and map[self.x][self.y].explored)):
            # libtcod.console_set_default_foreground(con, self.color)
            # libtcod.console_put_char(con, self.x, self.y, self.char,
            #                          libtcod.BKGND_NONE)
            console.set_default_foreground(self.color)
            console.write(self.x, self.y, self.char)

    def clear(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            # libtcod.console_put_char_ex(con, self.x, self.y, '.',
            #                             libtcod.white, color_light_ground)
            console.write_ex(self.x, self.y, '.', libtcod.white,
                             color_light_ground)


class Fighter:

    def __init__(self, hp, defense, power, xp, death_function=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.death_function = death_function

    @property
    def power(self):
        bonus = sum(equipment.power_bonus for
                    equipment in get_all_equipped(self.owner))
        return self.base_power + bonus

    @property
    def defense(self):
        bonus = sum(equipment.defense_bonus for
                    equipment in get_all_equipped(self.owner))
        return self.base_defense + bonus

    @property
    def max_hp(self):
        bonus = sum(equipment.max_hp_bonus for
                    equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    def attack(self, target):
        damage = self.power - target.fighter.defense

        if damage > 0:
            print(self.owner.name.capitalize() + ' attacks ' +
                  target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            print(self.owner.name.capitalize() + ' attacks ' +
                  target.name + ' but it has no effect.')

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
                if self.owner != player:
                    player.fighter.xp += self.xp

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp


class BasicMonster:

    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)


class ConfusedMonster:

    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:
            self.owner.move(libtcod.random_get_int(0, -1, 1),
                            libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else:
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name +
                    ' is no longer confused.', libtcod.red)


class Item:

    def __init__(self, use_function=None):
        self.use_function = use_function

    def pick_up(self):
        if len(inventory) >= 26:
            message('Your inventory is full, you cannot pick up ' +
                    self.owner.name + '.', libtcod.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '.', libtcod.green)

            equipment = self.owner.equipment
            if equipment and get_equipped_in_slot(equipment.slot) is None:
                equipment.equip()

    def drop(self):
        if self.owner.equipment:
            self.owner.equipment.dequip()

        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

    def use(self):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)


class Equipment:

    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.slot = slot
        self.is_equipped = False

    def toggle_equip(self):
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()

    def equip(self):
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()

        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on ' +
                self.slot + '.', libtcod.light_green)

    def dequip(self):
        if not self.is_equipped:
            return
        self.is_equipped = False
        message('Dequipped ' + self.owner.name + ' from ' +
                self.slot + '.', libtcod.yellow)


def get_equipped_in_slot(slot):
    for obj in inventory:
        if (obj.equipment and obj.equipment.slot == slot and
                obj.equipment.is_equipped):
            return obj.equipment


def get_all_equipped(obj):
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []


def is_blocked(x, y):
    if map[x][y].blocked:
        return True

    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False


def create_room(room):
    global map
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def make_map():
    global map, objects, stairs

    objects = [player]

    map = [[Tile(True) for y in range(MAP_HEIGHT)]
           for x in range(MAP_WIDTH)]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        new_room = Rect(x, y, w, h)

        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            create_room(new_room)
            place_objects(new_room)
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else:
                (prev_x, prev_y) = rooms[num_rooms - 1].center()
                if libtcod.random_get_int(0, 0, 1) == 1:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            rooms.append(new_room)
            num_rooms += 1

    stairs = Object(new_x, new_y, '<', 'stairs',
                    libtcod.white, always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()


def random_choice_index(chances):
    dice = libtcod.random_get_int(0, 1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if dice <= running_sum:
            return choice
        choice += 1


def random_choice(chances_dict):
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[random_choice_index(chances)]


def from_dungeon_level(table):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0


def place_objects(room):
    max_monster = from_dungeon_level([[2, 1], [3, 4], [5, 6]])

    monster_chances = {}
    monster_chances['orc'] = 80
    monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])

    max_items = from_dungeon_level([[1, 1], [2, 4]])

    item_chances = {}
    item_chances['heal'] = 35
    item_chances['lightning'] = from_dungeon_level([[25, 4]])
    item_chances['fireball'] = from_dungeon_level([[25, 6]])
    item_chances['confuse'] = from_dungeon_level([[10, 2]])
    item_chances['sword'] = from_dungeon_level([[5, 4]])
    item_chances['shield'] = from_dungeon_level([[15, 8]])

    num_monsters = libtcod.random_get_int(0, 0, max_monster)

    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            if choice == 'orc':
                fighter_component = Fighter(hp=10, defense=0, power=3, xp=35,
                                            death_function=monster_death)
                ai_component = BasicMonster()

                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                                 blocks=True, fighter=fighter_component,
                                 ai=ai_component)
            elif choice == 'troll':
                fighter_component = Fighter(hp=16, defense=1, power=4, xp=100,
                                            death_function=monster_death)
                ai_component = BasicMonster()

                monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                                 blocks=True, fighter=fighter_component,
                                 ai=ai_component)

            objects.append(monster)

    num_items = libtcod.random_get_int(0, 0, max_items)

    for i in range(num_items):
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
                item_component = Item(use_function=cast_heal)
                item = Object(x, y, '!', 'healing potion',
                              libtcod.violet, item=item_component)
            elif choice == 'lightning':
                item_component = Item(use_function=cast_lightning)
                item = Object(x, y, '#', 'scroll of lightning bolt',
                              libtcod.light_yellow, item=item_component)
            elif choice == 'fireball':
                item_component = Item(use_function=cast_fireball)
                item = Object(x, y, '#', 'scroll of fireball',
                              libtcod.light_yellow, item=item_component)
            elif choice == 'confuse':
                item_component = Item(use_function=cast_confuse)
                item = Object(x, y, '#', 'scroll of confusion',
                              libtcod.light_yellow, item=item_component)
            elif choice == 'sword':
                equipment_component = Equipment(slot='right hand',
                                                power_bonus=3)
                item = Object(x, y, '/', 'sword', libtcod.sky,
                              equipment=equipment_component)
            elif choice == 'shield':
                equipment_component = Equipment(slot='right hand',
                                                defense_bonus=1)
                item = Object(x, y, '[', 'shield', libtcod.darker_orange,
                              equipment=equipment_component)
            objects.append(item)
            item.send_to_back()
            item.always_visible = True


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)

    # libtcod.console_set_default_background(panel, back_color)
    # libtcod.console_rect(panel, x, y, total_width, 1,
    #                      False, libtcod.BKGND_SCREEN)
    panel.set_default_background(back_color)
    panel.color_rect(x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    # libtcod.console_set_default_background(panel, bar_color)
    panel.set_default_background(bar_color)
    if bar_width > 0:
        # libtcod.console_rect(panel, x, y, bar_width, 1,
        #                      False, libtcod.BKGND_SCREEN)
        panel.color_rect(x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    # libtcod.console_set_default_foreground(panel, libtcod.white)
    # libtcod.console_print_ex(panel, x + total_width / 2, y,
    #                          libtcod.BKGND_NONE, libtcod.CENTER,
    #                          name + ': ' + str(value) + '/' + str(maximum))
    panel.set_default_foreground(libtcod.white)
    panel.write(x + total_width / 2, y,
                name + ': ' + str(value) + '/' + str(maximum),
                align=libtcod.CENTER)


def get_name_under_mouse():
    global mouse

    (x, y) = (mouse.cx, mouse.cy)
    names = [obj.name for obj in objects if obj.x == x and obj.y == y and
             libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
    names = ', '.join(names)
    return names.capitalize()


def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute

    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y,
                                TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible:
                    if map[x][y].explored:
                        if wall:
                            # libtcod.console_put_char_ex(con, x, y, '#',
                            #                             libtcod.white,
                            #                             color_dark_wall)
                            console.write_ex(x, y, '#', libtcod.white,
                                             color_dark_wall)
                        else:
                            # libtcod.console_put_char_ex(con, x, y, '.',
                            #                             libtcod.white,
                            #                             color_dark_ground)
                            console.write_ex(x, y, '.', libtcod.white,
                                             color_dark_ground)
                else:
                    if wall:
                        # libtcod.console_put_char_ex(con, x, y, '#',
                        #                             libtcod.white,
                        #                             color_light_wall)
                        console.write_ex(x, y, '#', libtcod.white,
                                         color_light_wall)
                    else:
                        # libtcod.console_put_char_ex(con, x, y, '.',
                        #                             libtcod.white,
                        #                             color_light_ground)
                        console.write_ex(x, y, '.', libtcod.white,
                                         color_light_ground)
                    map[x][y].explored = True

    for object in objects:
        if object != player:
            object.draw()
    player.draw()

    # libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    console.blit()

    # libtcod.console_set_default_background(panel, libtcod.black)
    # libtcod.console_clear(panel)
    panel.set_default_background(libtcod.black)
    panel.clear

    y = 1
    for (line, color) in game_msgs:
        # libtcod.console_set_default_foreground(panel, color)
        # libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE,
        #                          libtcod.LEFT, line)
        panel.set_default_foreground(color)
        panel.write(MSG_X, y, line)
        y += 1

    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp,
               player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
    # libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT,
    #                          'Dungeon level ' + str(dungeon_level))
    panel.write(1, 3, 'Dungeon level ' + str(dungeon_level))

    # libtcod.console_set_default_foreground(con, libtcod.white)
    # libtcod.console_print_ex(0, 1, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE,
    #                          libtcod.LEFT, 'HP: ' + str(player.fighter.hp) +
    #                          '/' + str(player.fighter.max_hp))
    console.set_default_foreground(libtcod.white)
    root.write(1, SCREEN_HEIGHT - 2, 'HP: ' + str(player.fighter.hp) +
               '/' + str(player.fighter.max_hp))

    # libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    # libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
    #                          get_name_under_mouse())
    panel.set_default_foreground(libtcod.light_gray)
    panel.write(1, 0, get_name_under_mouse())

    # libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT,
    #                      0, 0, PANEL_Y)
    panel.blit(w=SCREEN_WIDTH, h=PANEL_HEIGHT, ydst=PANEL_Y)


def message(new_msg, color=libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        game_msgs.append((line, color))


def player_move_or_attack(dx, dy):
    global fov_recompute

    x = player.x + dx
    y = player.y + dy

    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options')

    # header_height = libtcod.console_get_height_rect(con, 0, 0, width,
    #                                                 SCREEN_HEIGHT, header)
    header_height = libtcod.console_get_height_rect(console.body, 0, 0, width,
                                                    SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    # window = libtcod.console_new(width, height)
    window = Panel(0, 0, width, height)

    # libtcod.console_set_default_foreground(window, libtcod.white)
    # libtcod.console_print_rect_ex(window, 0, 0, width, height,
    #                               libtcod.BKGND_NONE, libtcod.LEFT, header)
    window.set_default_foreground(libtcod.white)
    window.write_wrap_ex(0, 0, width, height, header, libtcod.LEFT)

    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        # libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE,
        #                          libtcod.LEFT, text)
        window.write(0, y, text)
        y += 1
        letter_index += 1

    x = SCREEN_WIDTH / 2 - width / 2
    y = SCREEN_HEIGHT / 2 - height / 2
    # libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    window.x = x
    window.y = y
    window.blit(bfade=0.7)

    # libtcod.console_flush()
    root.flush
    key = libtcod.console_wait_for_keypress(True)

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    index = key.c - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def inventory_menu(header):
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in inventory:
            text = item.name
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)

    index = menu(header, options, INVENTORY_WIDTH)

    if index is None or len(inventory) == 0:
        return None
    return inventory[index].item


def msgbox(text, width=50):
    menu(text, [], width)


def handle_keys():
    global key
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'

    if game_state == 'playing':
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
        elif key.vk == libtcod.KEY_KP5:
            pass

        else:
            key_char = chr(key.c)

            if key_char == 'g':
                for object in objects:
                    if object.x == player.x and \
                       object.y == player.y and object.item:
                        object.item.pick_up()
                        break

            if key_char == 'i':
                chosen_item = inventory_menu('Press the key next to an ' +
                                             'item to use it, or any ' +
                                             'other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

            if key_char == 'd':
                chosen_item = inventory_menu('Press the key next to an ' +
                                             'to drop it, or any ' +
                                             'other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()

            if key_char == 'c':
                level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                msgbox('Character information\n\nLevel: ' + str(player.level) +
                       '\nExperiance: ' + str(player.fighter.xp) +
                       '\nExperiance to level up: ' + str(level_up_xp) +
                       '\nMaximum HP: ' + str(player.fighter.max_hp) +
                       '\nAttack: ' + str(player.fighter.power) +
                       '\nDefense: ' + str(player.fighter.defense),
                       CHARACTER_SCREEN_WIDTH)

            if key_char == '<':
                if stairs.x == player.x and stairs.y == player.y:
                    next_level()

            return 'didnt-take-turn'


def check_level_up():
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your battle skills grow stronger. You reached level ' +
                str(player.level) + '.', libtcod.yellow)

        choice = None
        while choice is None:
            choice = menu('Level up! Choose a stat to raise:\n',
                          ['Constitution (+20 HP, from ' +
                           str(player.fighter.max_hp) + ')',
                           'Strength (+1 attack, from ' +
                           str(player.fighter.power) + ')',
                           'Agility (+1 defense, from ' +
                           str(player.fighter.defense) + ')'],
                          LEVEL_SCREEN_WIDTH)

        if choice == 0:
            player.fighter.max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.power += 1
        elif choice == 2:
            player.fighter.defense += 1


def player_death(player):
    global game_state
    print('you died.')
    game_state = 'dead'

    player.char = '%'
    player.color = libtcod.dark_red


def monster_death(monster):
    message('The ' + monster.name + ' is dead. You gain ' +
            str(monster.fighter.xp) + ' experiance points.',
            libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()


def target_tile(max_range=None):
    global key, mouse
    while True:
        # libtcod.console_flush()
        root.flush
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE, key, mouse)
        render_all()

        (x, y) = (mouse.cx, mouse.cy)

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
                (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)


def target_monster(max_range=None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None:
            return None

        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj


def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1

    for object in objects:
        if object.fighter and not object == player and \
           libtcod.map_is_in_fov(fov_map, object.x, object.y):
            dist = player.distance_to(object)
            if dist < closest_dist:
                closest_enemy = object
                closest_dist = dist
    return closest_enemy


def cast_heal():
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', libtcod.red)
        return 'cancel'

    message('Your wounds start to feel better.', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)


def cast_lightning():
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    message('A lightning bolt strikes the ' + monster.name +
            ' with a loud thunder! the damage is ' +
            str(LIGHTNING_DAMAGE) + ' hit points.',
            libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)


def cast_fireball():
    message('Left-click a target tile for the fireball,' +
            ' or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None:
        return 'cancelled'
    message('The fireball explodes, burning everything within ' +
            str(FIREBALL_RADIUS) + ' tiles.', libtcod.orange)

    for obj in objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' +
                    str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE)


def cast_confuse():
    monster = closest_monster(CONFUSE_RANGE)
    message('Left-click an enemy to confuse it, or right-click to cancel.',
            libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None:
        return 'cancelled'

    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster
    message('The eyes of the ' + monster.name +
            ' look vacant, as he starts to stumble around.',
            libtcod.light_green)


def save_game():
    file = shelve.open('savegame.save', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairs_index'] = objects.index(stairs)
    file['dungeon_level'] = dungeon_level
    file.close()


def load_game():
    global map, objects, player, stairs, inventory, game_msgs, \
        game_state, dungeon_level

    file = shelve.open('savegame.save', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()

    initialize_fov()


def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level

    fighter_component = Fighter(hp=30, defense=2, power=5,
                                xp=0, death_function=player_death)
    player = Object(0, 0, '@', 'player', libtcod.white, blocks=True,
                    fighter=fighter_component)

    player.level = 1
    dungeon_level = 1
    make_map()
    initialize_fov()

    game_state = 'playing'
    inventory = []

    game_msgs = []

    message('Welcome stranger. Prepare to perish in the ' +
            'Tombs of the Ancient Kings.', libtcod.red)

    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky,
                 equipment=equipment_component)
    inventory.append(obj)
    equipment_component.equip()
    obj.always_visible = True


def next_level():
    global dungeon_level
    message('You take a moment to rest, and recover your strength',
            libtcod.light_violet)
    player.fighter.heal(player.fighter.max_hp / 2)

    dungeon_level += 1
    message('After a rare moment of peace, you descend deeper into ' +
            'the heart of the dungeon...', libtcod.red)
    make_map()
    initialize_fov()


def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True

    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y,
                                       not map[x][y].block_sight,
                                       not map[x][y].blocked)

    # libtcod.console_clear(con)
    console.clear


def play_game():
    global key, mouse

    player_action = None

    mouse = libtcod.Mouse()
    key = libtcod.Key()
    # while not libtcod.console_is_window_closed():
    while not root.is_window_closed:
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE,
                                    key, mouse)
        render_all()

        # libtcod.console_flush()
        root.flush

        check_level_up()

        for object in objects:
            object.clear()

        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break

        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()


def main_menu():
    # while not libtcod.console_is_window_closed():
    while not root.is_window_closed:
        root.clear
        console.set_default_background(libtcod.black)

        # libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        # libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 4,
        #                          libtcod.BKGND_NONE, libtcod.CENTER,
        #                          'Tomb of the Ancient Kings')
        # libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 2,
        #                         libtcod.BKGND_NONE, libtcod.CENTER, 'Author')
        root.set_default_foreground(libtcod.light_yellow)
        root.write(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 4,
                   'Toom of the Ancient Kings', align=libtcod.CENTER)
        root.write(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 2,
                   'Author', align=libtcod.CENTER)

        choice = menu('', ['Play a new game',
                           'Continue last game', 'Quit'], 24)

        if choice == 0:
            new_game()
            play_game()
        if choice == 1:
            try:
                load_game()
            except:
                msgbox('\n No saved game to load. \n', 24)
                continue
            play_game()
        elif choice == 2:
            break

# libtcod.console_set_custom_font('terminal12x12_gs_ro.png',
#                                 libtcod.FONT_TYPE_GREYSCALE |
#                                 libtcod.FONT_LAYOUT_ASCII_INROW)
# libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
#                           'basicroguelike', False)
# libtcod.sys_set_fps(LIMIT_FPS)
# con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
# panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
root = Console(SCREEN_WIDTH, SCREEN_HEIGHT, 'basicroguelike')
console = Panel(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
panel = Panel(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

main_menu()
