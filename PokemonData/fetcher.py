import os
import json
import requests
from PIL import Image
from io import BytesIO

CACHE_FILE = 'pokemon_cache.json'
IMAGE_CACHE_DIR = 'image_cache'

class PersistentCache:
    def __init__(self, filename):
        self.filename = filename
        self.data = {'pokemon': {}, 'move': {}, 'ability': {}, 'item': {}, 'images': {}}
        self.load()
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {'pokemon': {}, 'move': {}, 'ability': {}, 'item': {}, 'images': {}}
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
        self._setup_image_cache()
    def _setup_image_cache(self):
        # Resim önbellek dizinini oluştur
        if not os.path.exists(IMAGE_CACHE_DIR):
            os.makedirs(IMAGE_CACHE_DIR)
    def _get_cached_image_path(self, pokemon_id):
        return os.path.join(IMAGE_CACHE_DIR, f"{pokemon_id}.png")
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
        # Önce önbellekte ara
        cache_path = self._get_cached_image_path(pokemon_id)
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return f.read()
                
        # Yoksa indir ve önbelleğe kaydet
        try:
            response = requests.get(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png")
            if response.status_code == 200:
                # Resmi optimize et ve önbelleğe kaydet
                img = Image.open(BytesIO(response.content))
                img.save(cache_path, optimize=True, quality=85)
                return response.content
        except Exception as e:
            print(f"Error caching image for Pokemon {pokemon_id}: {e}")
            # Hata durumunda orijinal veriyi döndür
            return response.content if response.status_code == 200 else b''
    def clear_image_cache(self):
        """Resim önbelleğini temizle"""
        if os.path.exists(IMAGE_CACHE_DIR):
            for file in os.listdir(IMAGE_CACHE_DIR):
                try:
                    os.remove(os.path.join(IMAGE_CACHE_DIR, file))
                except Exception as e:
                    print(f"Error removing cached image {file}: {e}")
                    
    def get_image_cache_size(self):
        """Önbellek boyutunu MB cinsinden döndür"""
        total_size = 0
        if os.path.exists(IMAGE_CACHE_DIR):
            for file in os.listdir(IMAGE_CACHE_DIR):
                total_size += os.path.getsize(os.path.join(IMAGE_CACHE_DIR, file))
        return total_size / (1024 * 1024)  # MB cinsinden
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
    def get_type_data(self, type_name: str) -> dict:
        if self.cache:
            cached = self.cache.get('type', type_name.lower())
            if cached:
                return cached
        response = requests.get(f"{self.base_url}/type/{type_name.lower()}")
        data = response.json()
        if self.cache:
            self.cache.set('type', type_name.lower(), data)
        return data 