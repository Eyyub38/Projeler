import requests
from tabulate import tabulate
import json
from typing import Dict, List, Optional

class PokemonDataFetcher:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2"
        
    def get_pokemon_data(self, pokemon_name: str) -> Dict:
        """Pokemon verilerini çeker"""
        response = requests.get(f"{self.base_url}/pokemon/{pokemon_name.lower()}")
        return response.json()
    
    def get_move_data(self, move_name: str) -> Dict:
        """Hareket verilerini çeker"""
        response = requests.get(f"{self.base_url}/move/{move_name.lower()}")
        return response.json()
    
    def get_ability_data(self, ability_name: str) -> Dict:
        """Yetenek verilerini çeker"""
        response = requests.get(f"{self.base_url}/ability/{ability_name.lower()}")
        return response.json()
    
    def get_item_data(self, item_name: str) -> Dict:
        """Eşya verilerini çeker"""
        response = requests.get(f"{self.base_url}/item/{item_name.lower()}")
        return response.json()

def display_pokemon_info(pokemon_data: Dict):
    """Pokemon bilgilerini düzenli bir şekilde gösterir"""
    print("\n=== Pokemon Bilgileri ===")
    print(f"İsim: {pokemon_data['name'].capitalize()}")
    print(f"ID: {pokemon_data['id']}")
    print(f"Boy: {pokemon_data['height']/10}m")
    print(f"Ağırlık: {pokemon_data['weight']/10}kg")
    
    print("\nTemel İstatistikler:")
    stats = [[stat['stat']['name'], stat['base_stat']] for stat in pokemon_data['stats']]
    print(tabulate(stats, headers=['İstatistik', 'Değer'], tablefmt='grid'))
    
    print("\nTürler:")
    types = [type['type']['name'] for type in pokemon_data['types']]
    print(", ".join(types))
    
    print("\nHareketler:")
    moves = [move['move']['name'] for move in pokemon_data['moves'][:5]]  # İlk 5 hareket
    print(", ".join(moves))

def display_move_info(move_data: Dict):
    """Hareket bilgilerini düzenli bir şekilde gösterir"""
    print("\n=== Hareket Bilgileri ===")
    print(f"İsim: {move_data['name'].capitalize()}")
    print(f"ID: {move_data['id']}")
    print(f"Güç: {move_data['power'] if move_data['power'] else 'N/A'}")
    print(f"PP: {move_data['pp']}")
    print(f"Doğruluk: {move_data['accuracy'] if move_data['accuracy'] else 'N/A'}")
    print(f"Tür: {move_data['type']['name']}")
    print(f"Hasar Türü: {move_data['damage_class']['name']}")
    print(f"Açıklama: {move_data['effect_entries'][0]['effect'] if move_data['effect_entries'] else 'Açıklama yok'}")

def display_ability_info(ability_data: Dict):
    """Yetenek bilgilerini düzenli bir şekilde gösterir"""
    print("\n=== Yetenek Bilgileri ===")
    print(f"İsim: {ability_data['name'].capitalize()}")
    print(f"ID: {ability_data['id']}")
    print(f"Açıklama: {ability_data['effect_entries'][0]['effect'] if ability_data['effect_entries'] else 'Açıklama yok'}")

def display_item_info(item_data: Dict):
    """Eşya bilgilerini düzenli bir şekilde gösterir"""
    print("\n=== Eşya Bilgileri ===")
    print(f"İsim: {item_data['name'].capitalize()}")
    print(f"ID: {item_data['id']}")
    print(f"Fiyat: {item_data['cost']}")
    print(f"Açıklama: {item_data['effect_entries'][0]['effect'] if item_data['effect_entries'] else 'Açıklama yok'}")

def main():
    fetcher = PokemonDataFetcher()
    
    while True:
        print("\n=== Pokemon Veri Çekme Programı ===")
        print("1. Pokemon Bilgisi")
        print("2. Hareket Bilgisi")
        print("3. Yetenek Bilgisi")
        print("4. Eşya Bilgisi")
        print("5. Çıkış")
        
        choice = input("\nSeçiminiz (1-5): ")
        
        if choice == "5":
            print("Program sonlandırılıyor...")
            break
            
        name = input("İsim giriniz: ")
        
        try:
            if choice == "1":
                data = fetcher.get_pokemon_data(name)
                display_pokemon_info(data)
            elif choice == "2":
                data = fetcher.get_move_data(name)
                display_move_info(data)
            elif choice == "3":
                data = fetcher.get_ability_data(name)
                display_ability_info(data)
            elif choice == "4":
                data = fetcher.get_item_data(name)
                display_item_info(data)
            else:
                print("Geçersiz seçim!")
                
        except requests.exceptions.HTTPError as e:
            print(f"Hata: {name} bulunamadı!")
        except Exception as e:
            print(f"Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    main() 