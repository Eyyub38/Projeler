import json
import os
from typing import Dict, List, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum

class DataType(Enum):
    POKEMON = "pokemon"
    MOVE = "move"
    ITEM = "item"

@dataclass
class BaseStats:
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int

@dataclass
class Evolution:
    next_form: str
    level: int
    condition: str = ""  # Örn: taş, item, dostluk, vs.

@dataclass
class Pokemon:
    id: int
    name: str
    type: List[str]  # Birden fazla tip
    base_stats: BaseStats
    moves: List[str]
    evolutions: List[Evolution]  # Birden fazla evrim
    forms: List[str]  # Mega, Alolan, Galarian, vs.
    egg_groups: List[str]
    xp_yield: int
    catch_rate: int
    gender_ratio: str
    abilities: List[str]
    height: float
    weight: float

@dataclass
class Move:
    id: int
    name: str
    type: str
    power: int
    accuracy: int
    pp: int
    category: str
    description: str

@dataclass
class Item:
    id: int
    name: str
    type: str
    description: str
    effect: str
    price: int

class DatabaseManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_directory()
        
    def _ensure_data_directory(self):
        """Veri dizininin varlığını kontrol eder ve yoksa oluşturur."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _get_file_path(self, data_type: DataType) -> str:
        """Veri tipine göre dosya yolunu döndürür."""
        return os.path.join(self.data_dir, f"{data_type.value}.json")
    
    def _load_data(self, data_type: DataType) -> List[Dict[str, Any]]:
        """Belirtilen veri tipindeki verileri yükler."""
        file_path = self._get_file_path(data_type)
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_data(self, data_type: DataType, data: List[Dict[str, Any]]):
        """Verileri JSON dosyasına kaydeder."""
        file_path = self._get_file_path(data_type)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def add_entry(self, data_type: DataType, entry: Union[Pokemon, Move, Item]):
        """Yeni bir veri girişi ekler."""
        data = self._load_data(data_type)
        data.append(asdict(entry))
        self._save_data(data_type, data)
    
    def update_entry(self, data_type: DataType, entry_id: int, updated_entry: Union[Pokemon, Move, Item]):
        """Mevcut bir veri girişini günceller."""
        data = self._load_data(data_type)
        for i, entry in enumerate(data):
            if entry['id'] == entry_id:
                data[i] = asdict(updated_entry)
                break
        self._save_data(data_type, data)
    
    def delete_entry(self, data_type: DataType, entry_id: int):
        """Bir veri girişini siler."""
        data = self._load_data(data_type)
        data = [entry for entry in data if entry['id'] != entry_id]
        self._save_data(data_type, data)
    
    def get_entry(self, data_type: DataType, entry_id: int) -> Union[Dict[str, Any], None]:
        """ID'ye göre veri girişini getirir."""
        data = self._load_data(data_type)
        for entry in data:
            if entry['id'] == entry_id:
                return entry
        return None
    
    def get_all_entries(self, data_type: DataType) -> List[Dict[str, Any]]:
        """Belirtilen veri tipindeki tüm verileri getirir."""
        return self._load_data(data_type)
    
    def search_entries(self, data_type: DataType, search_term: str) -> List[Dict[str, Any]]:
        """İsme göre veri araması yapar."""
        data = self._load_data(data_type)
        search_term = search_term.lower()
        return [entry for entry in data if search_term in entry['name'].lower()]
    
    def get_next_id(self, data_type: DataType) -> int:
        """Yeni bir giriş için kullanılabilecek ID'yi döndürür."""
        data = self._load_data(data_type)
        if not data:
            return 1
        return max(entry['id'] for entry in data) + 1 