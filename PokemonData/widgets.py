from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QScrollArea, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QFont
import requests
from io import BytesIO

class EvolutionChainWidget(QWidget):
    def __init__(self, fetcher):
        super().__init__()
        self.fetcher = fetcher
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumHeight(150)
        
    def update_chain(self, chain_data):
        self.clear_layout()
        if not chain_data:
            return
            
        def add_evolution(chain, level=0):
            if not chain:
                return
                
            pokemon_name = chain['species']['name']
            try:
                pokemon_data = self.fetcher.get_pokemon_data_safe(pokemon_name)
                pokemon_id = pokemon_data['id']
                
                # Pokemon kartı
                card = QFrame()
                card.setFrameStyle(QFrame.Box | QFrame.Raised)
                card.setStyleSheet("""
                    QFrame {
                        background-color: #f0f0f0;
                        border-radius: 10px;
                        padding: 5px;
                    }
                """)
                card_layout = QVBoxLayout()
                
                # Pokemon resmi
                img_label = QLabel()
                img_data = self.fetcher.get_pokemon_image(pokemon_id)
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                
                # Pokemon adı
                name_label = QLabel(pokemon_name.capitalize())
                name_label.setAlignment(Qt.AlignCenter)
                name_label.setStyleSheet("font-weight: bold;")
                
                card_layout.addWidget(img_label)
                card_layout.addWidget(name_label)
                card.setLayout(card_layout)
                
                self.layout.addWidget(card)
                
                # Evrim detayları
                if chain.get('evolves_to'):
                    for evo in chain['evolves_to']:
                        if level > 0:
                            arrow = QLabel("→")
                            arrow.setStyleSheet("font-size: 24px; font-weight: bold;")
                            arrow.setAlignment(Qt.AlignCenter)
                            self.layout.addWidget(arrow)
                        add_evolution(evo, level + 1)
                        
            except Exception as e:
                print(f"Error loading evolution: {e}")
                
        add_evolution(chain_data['chain'])
        self.layout.addStretch()
        
    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

class StatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.stats = {}
        self.setup_ui()
        
    def setup_ui(self):
        stat_names = {
            'hp': 'HP',
            'attack': 'Saldırı',
            'defense': 'Savunma',
            'special-attack': 'Özel Saldırı',
            'special-defense': 'Özel Savunma',
            'speed': 'Hız'
        }
        
        for i, (stat_id, stat_name) in enumerate(stat_names.items()):
            label = QLabel(stat_name)
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(255)
            progress.setTextVisible(True)
            progress.setFormat("%v")
            progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 5px;
                }
            """)
            self.layout.addWidget(label, i, 0)
            self.layout.addWidget(progress, i, 1)
            self.stats[stat_id] = progress
            
    def update_stats(self, stats_data):
        for stat in stats_data:
            stat_id = stat['stat']['name']
            if stat_id in self.stats:
                self.stats[stat_id].setValue(stat['base_stat'])

class PokemonCardWidget(QWidget):
    def __init__(self, fetcher, name=None, image_data=None, types=None, parent=None):
        super().__init__(parent)
        if fetcher is None:
            raise ValueError("fetcher parameter is required")
            
        self.fetcher = fetcher
        self.setFixedSize(140, 180)
        self.setStyleSheet("background: #f8fafc; border-radius: 10px; border: 1px solid #b0b8c1;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Pokemon image
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img_label)

        # Name
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #2d5aa6;")
        layout.addWidget(self.name_label)

        # Types
        self.type_layout = QHBoxLayout()
        layout.addLayout(self.type_layout)

        # İstatistikler
        self.stats_widget = StatsWidget()
        layout.addWidget(self.stats_widget)
        
        # Evrim zinciri
        self.evolution_widget = EvolutionChainWidget(self.fetcher)
        layout.addWidget(self.evolution_widget)
        
        # Hareketler
        self.moves_label = QLabel("Hareketler:")
        self.moves_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.moves_label)
        
        self.moves_scroll = QScrollArea()
        self.moves_scroll.setWidgetResizable(True)
        self.moves_scroll.setMinimumHeight(200)
        
        self.moves_widget = QWidget()
        self.moves_layout = QVBoxLayout()
        self.moves_widget.setLayout(self.moves_layout)
        self.moves_scroll.setWidget(self.moves_widget)
        layout.addWidget(self.moves_scroll)
        
        # Update with initial data if provided
        if name is not None or image_data is not None or types is not None:
            self.update_display(name, image_data, types)

    def update_display(self, name=None, image_data=None, types=None):
        # Update image
        if image_data is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.img_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.img_label.clear()

        # Update name
        if name is not None:
            self.name_label.setText(name.capitalize())
        else:
            self.name_label.clear()

        # Update types
        # Clear existing type labels
        while self.type_layout.count():
            item = self.type_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if types is not None:
            for t in types:
                type_label = QLabel(t.capitalize())
                type_label.setAlignment(Qt.AlignCenter)
                type_label.setStyleSheet(f"""
                    background: {self.type_color(t)};
                    color: white;
                    border-radius: 6px;
                    padding: 2px 8px;
                    font-size: 12px;
                    font-weight: bold;
                """)
                self.type_layout.addWidget(type_label)

    def type_color(self, t):
        colors = {
            'grass': '#78C850', 'poison': '#A040A0', 'fire': '#F08030', 'water': '#6890F0',
            'bug': '#A8B820', 'normal': '#A8A878', 'flying': '#A890F0', 'electric': '#F8D030',
            'ground': '#E0C068', 'fairy': '#EE99AC', 'fighting': '#C03028', 'psychic': '#F85888',
            'rock': '#B8A038', 'steel': '#B8B8D0', 'ice': '#98D8D8', 'ghost': '#705898',
            'dragon': '#7038F8', 'dark': '#705848'
        }
        return colors.get(t, '#888888')

    def update_pokemon(self, pokemon_data, species_data=None, evolution_chain=None):
        """Tam Pokemon verilerini kullanarak kartı güncelle"""
        # Resim güncelleme
        pokemon_id = pokemon_data['id']
        img_data = self.fetcher.get_pokemon_image(pokemon_id)
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img_label.setPixmap(pixmap)
        
        # İsim güncelleme
        self.name_label.setText(pokemon_data['name'].capitalize())
        
        # Türler güncelleme
        types = [t['type']['name'].capitalize() for t in pokemon_data['types']]
        self.update_display(pokemon_data['name'], img_data, types)
        
        # İstatistikler güncelleme
        self.stats_widget.update_stats(pokemon_data['stats'])
        
        # Evrim zinciri güncelleme
        if evolution_chain:
            self.evolution_widget.update_chain(evolution_chain)
            
        # Hareketler güncelleme
        self.update_moves(pokemon_data['moves'])
        
    def update_moves(self, moves_data):
        # Mevcut hareketleri temizle
        while self.moves_layout.count():
            item = self.moves_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Hareketleri grupla
        move_groups = {}
        for move in moves_data:
            for version in move['version_group_details']:
                method = version['move_learn_method']['name']
                if method not in move_groups:
                    move_groups[method] = set()
                move_groups[method].add(move['move']['name'])
                
        # Her grup için bir bölüm oluştur
        for method, moves in move_groups.items():
            group_label = QLabel(method.replace('-', ' ').capitalize())
            group_label.setStyleSheet("font-weight: bold; color: #2196F3;")
            self.moves_layout.addWidget(group_label)
            
            moves_text = QLabel(", ".join(sorted(moves)))
            moves_text.setWordWrap(True)
            self.moves_layout.addWidget(moves_text)
            
        self.moves_layout.addStretch() 