import requests
from ml import *
from random import randint
from random import choice

def create_campaign():
    story = create_initial_stories('')
    size = randint(50, 300)
    payload = {
        "name": ['soft skills test campaign'],
        'initial_story': [story],
        'size_x': [size],
        'size_y': [size],
        'create_campaign': [True]
    }
    response = requests.post("http://localhost:7000/campaignselection_json", data=payload)
    print(response.status_code)
    print(response.json())
    return response.json()['campaign_id']

race_list = ['Alien', 'Angel', 'Basilisk', 'Centaur', 'Chicken', 'Chimera', 'Cyclop', 'Demon', 'Dragon', 'Druid', 'Dwarf', 'Elf', 'Fairy', 'Fox', 'Ghost', 'Giant', 'Goblin', 'Golem', 'Harpy', 'Human', 'Hydra', 'Indigenous', 'Kiwi', 'Medusa', 'Mermaid', 'Mimic', 'Minotaur', 'Moai', 'Mummy', 'Orc', 'Rat', 'Scorpion', 'Skeleton', 'Spider', 'Troll', 'Unicorn', 'Vampire', 'Werewolf', 'Wolf', 'Zombie']
class_list = ['Alchemist', 'Archer', 'Artificer', 'Assassin', 'Barbarian', 'Bard', 'Blacksmith', 'Brute', 'Cleric', 'Cowboy', 'Farmer', 'Fighter', 'Hunter', 'Knight', 'Lancer', 'Mage', 'Merchant', 'Monk', 'Ninja', 'Overlord', 'Paladin', 'Pirate', 'Ranger', 'Rogue', 'Samurai', 'Soldier', 'Spartan', 'Tribal', 'Viking', 'Warrior', 'Witch', 'Wizard']
weapon_list = [54, 55, 89, 57, 58, 59, 60, 4, 61, 62, 63, 64, 65, 66, 67, 68, 69, 90, 71, 80, 72, 73, 74, 75, 76, 77]

def create_player_dnd(room_id, telegram_id):
    race = choice(race_list)
    class_ = choice(class_list)
    weapon_id = str(choice(weapon_list))
    vitality = 5
    str_ = 5
    int_ = 5
    dex = 5
    description = ''
    phyres = 5
    magres = 5
    con = 5
    story = create_initial_stories('')
    payload = {
        'campaign_id': [str(room_id)],
        'name': [telegram_id],
        'create_player': [True],
        'physical_description': [story],
        'weapon_id': [weapon_id],
        'max_health': [10],
        'race': [race],
        'class': [class_],
        'vitality': [vitality],
        'str': [str_],
        'int': [int_],
        'rec': [5],
        'dex': [dex],
        'phyres': [phyres],
        'magres': [magres],
        'con': [con],
        'gift': ['gold'],
    }
    response = requests.post("http://localhost:7000/playerselection_json", data=payload)
    print(response.status_code)
    print(response.json())
    return response.json()['player_id']

def get_room_history(room_id):
    payload = {
        'campaign_id': str(room_id)
    }
    response = requests.post("http://localhost:7000/get_room_history", data=payload)
    print(response.status_code)
    print(response.json())
    return response.json()['history']

