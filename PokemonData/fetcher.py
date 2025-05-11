import os
import json
import requests

CACHE_FILE = 'pokemon_cache.json'

class PersistentCache:
    def __init__(self, filename):
        self.filename = filename
        self.data = {'pokemon': {}, 'move': {}, 'ability': {}, 'item': {}}
        self.load()
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {'pokemon': {}, 'move': {}, 'ability': {}, 'item': {}}
    def save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f)
        except Exception:
            pass
    def get(self, category, key):
        return self.data.get(category, {}).get(key)
    def set(self, category, key, value):
        self.data.setdefault(category, {})[key] = value
        self.save()

class PokemonDataFetcher:
    def __init__(self, cache=None):
        self.base_url = "https://pokeapi.co/api/v2"
        self.cache = cache
    def get_pokemon_data(self, pokemon_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('pokemon', pokemon_name.lower())
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/pokemon/{pokemon_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('pokemon', pokemon_name.lower(), data)
        return data
    def get_pokemon_species(self, pokemon_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('pokemon', f"species_{pokemon_name.lower()}")
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/pokemon-species/{pokemon_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('pokemon', f"species_{pokemon_name.lower()}", data)
        return data
    def get_evolution_chain(self, url: str) -> dict:
        key = f"evo_{url.split('/')[-2]}"
        if self.cache:
            cached = self.cache.get('pokemon', key)
            if cached:
                return cached
        response = requests.get(url)
        data = response.json()
        if self.cache:
            self.cache.set('pokemon', key, data)
        return data
    def get_move_data(self, move_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('move', move_name.lower())
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/move/{move_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('move', move_name.lower(), data)
        return data
    def get_ability_data(self, ability_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('ability', ability_name.lower())
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/ability/{ability_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('ability', ability_name.lower(), data)
        return data
    def get_item_data(self, item_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('item', item_name.lower())
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/item/{item_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('item', item_name.lower(), data)
        return data
    def get_pokemon_image(self, pokemon_id: int) -> bytes:
        response = requests.get(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png")
        return response.content
    def get_pokemon_data_safe(self, name):
        try:
            return self.get_pokemon_data(name)
        except Exception:
            species = self.get_pokemon_species(name)
            for var in species.get('varieties', []):
                var_name = var['pokemon']['name']
                try:
                    return self.get_pokemon_data(var_name)
                except Exception:
                    continue
            raise 