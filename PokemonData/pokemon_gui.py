import sys
import requests
import os
import json
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QComboBox, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QSplitter, QProgressBar, QMessageBox, QSizePolicy, QGridLayout, QGroupBox, QFrame, QCheckBox, QScrollArea, QLineEdit, QListWidget, QPushButton, QMenuBar, QMenu, QAction, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QSize, QPointF
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QPen, QColor, QFont, QPainterPath, QPolygonF
import numpy as np
from fetcher import PersistentCache, PokemonDataFetcher
from threads import DataFetcherThread
from widgets import PokemonCardWidget, StatsWidget, EvolutionChainWidget

CACHE_FILE = 'pokemon_cache.json'
FAV_FILE = 'favorites.json'

class DataFetcherThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    def __init__(self, fetcher, data_type):
        super().__init__()
        self.fetcher = fetcher
        self.data_type = data_type
    def run(self):
        try:
            if self.data_type == 'pokemon':
                response = requests.get(f"{self.fetcher.base_url}/pokemon?limit=1")
                total_count = response.json()['count']
                response = requests.get(f"{self.fetcher.base_url}/pokemon?limit={total_count}")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'hareket':
                response = requests.get(f"{self.fetcher.base_url}/move?limit=1000")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'yetenek':
                response = requests.get(f"{self.fetcher.base_url}/ability?limit=1000")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'eşya':
                response = requests.get(f"{self.fetcher.base_url}/item?limit=1025")
                self.finished.emit(response.json()['results'])
            else:
                self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))

# --- EvolutionChainWidget ---
class EvolutionChainWidget(QWidget):
    def __init__(self, evo_chain, current_name, fetcher, parent=None):
        super().__init__(parent)
        self.evo_chain = evo_chain
        self.current_name = current_name
        self.fetcher = fetcher
        # Boyutları ayarlıyoruz
        self.setMinimumSize(800, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QWidget {
                background: #3a7a2a;
                border-radius: 12px;
            }
        """)
        self.pokemon_nodes = []
        self.zoom = 1.0
        self.prepare_nodes()
        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self):
        # Minimum boyutu döndürüyoruz
        return QSize(800, 400)

    def minimumSizeHint(self):
        # Minimum boyut ipucu
        return QSize(800, 400)

    def wheelEvent(self, event):
        # Mouse wheel zoom'u devre dışı bırakıyoruz
        pass

    def keyPressEvent(self, event):
        # Klavye zoom'u devre dışı bırakıyoruz
        super().keyPressEvent(event)

    def prepare_nodes(self):
        if not self.evo_chain or 'chain' not in self.evo_chain:
            self.pokemon_nodes = []
            return
        # Her zaman zincirin kökünü bul (ör: Eevee)
        root_chain = self.evo_chain['chain']
        root_name = root_chain['species']['name']

        # Ana node (merkez)
        try:
            print(f'Trying to fetch: {root_name}')
            data = self.fetcher.get_pokemon_data_safe(root_name)
            img_data = self.fetcher.get_pokemon_image(data['id'])
            img = QImage.fromData(img_data)
            pix = QPixmap.fromImage(img).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            types = [t['type']['name'] for t in data['types']]
        except Exception as e:
            print(f'Error fetching data for {root_name}:', e)
            pix = QPixmap(80, 80)
            pix.fill(Qt.gray)
            types = []
        self.pokemon_nodes = [{
            'name': root_name,
            'pix': pix,
            'types': types,
            'depth': 0,
            'chain': root_chain,
            'evo_details': None,
            'parent_pos': None,
            'angle': 0
        }]

        # Tüm ilk evrimler (dallanmalar)
        evolutions = root_chain['evolves_to']
        # Lycanroc için varieties ile formları ekle
        lycanroc_forms = []
        for evo in evolutions:
            if evo['species']['name'] == 'lycanroc':
                species = self.fetcher.get_pokemon_species('lycanroc')
                lycanroc_forms = [v['pokemon']['name'] for v in species.get('varieties', []) if v['pokemon']['name'].startswith('lycanroc-')]
                break
        total_evos = len(evolutions) - (1 if lycanroc_forms else 0) + len(lycanroc_forms)
        angle_step = 360 / total_evos if total_evos > 0 else 360
        evo_idx = 0
        for evo in evolutions:
            evo_name = evo['species']['name']
            if evo_name == 'lycanroc' and lycanroc_forms:
                # Ana Lycanroc verilerini al
                try:
                    main_data = self.fetcher.get_pokemon_data_safe('lycanroc')
                    main_types = [t['type']['name'] for t in main_data['types']]
                    main_evo_details = evo['evolution_details'][0] if evo['evolution_details'] else None
                except Exception as e:
                    print(f'Error fetching main Lycanroc data:', e)
                    main_types = []
                    main_evo_details = None

                for form_name in lycanroc_forms:
                    try:
                        print(f'Trying to fetch: {form_name}')
                        data = self.fetcher.get_pokemon_data_safe(form_name)
                        img_data = self.fetcher.get_pokemon_image(data['id'])
                        img = QImage.fromData(img_data)
                        pix = QPixmap.fromImage(img).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        # Form ismini düzgün göster
                        display_name = self.get_lycanroc_display_name(form_name)
                        self.pokemon_nodes.append({
                            'name': form_name,
                            'display_name': display_name,
                            'pix': pix,
                            'types': main_types,
                            'depth': 1,
                            'chain': evo,
                            'evo_details': main_evo_details,
                            'parent_pos': 0,
                            'angle': evo_idx * angle_step
                        })
                        evo_idx += 1
                    except Exception as e:
                        print(f'Error fetching data for {form_name}:', e)
                        pix = QPixmap(80, 80)
                        pix.fill(Qt.gray)
                        display_name = self.get_lycanroc_display_name(form_name)
                        self.pokemon_nodes.append({
                            'name': form_name,
                            'display_name': display_name,
                            'pix': pix,
                            'types': main_types,
                            'depth': 1,
                            'chain': evo,
                            'evo_details': main_evo_details,
                            'parent_pos': 0,
                            'angle': evo_idx * angle_step
                        })
                        evo_idx += 1
            else:
                try:
                    print(f'Trying to fetch: {evo_name}')
                    data = self.fetcher.get_pokemon_data_safe(evo_name)
                    img_data = self.fetcher.get_pokemon_image(data['id'])
                    img = QImage.fromData(img_data)
                    pix = QPixmap.fromImage(img).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    types = [t['type']['name'] for t in data['types']]
                except Exception as e:
                    print(f'Error fetching data for {evo_name}:', e)
                    pix = QPixmap(80, 80)
                    pix.fill(Qt.gray)
                    types = []
                self.pokemon_nodes.append({
                    'name': evo_name,
                    'display_name': evo_name.capitalize(),
                    'pix': pix,
                    'types': types,
                    'depth': 1,
                    'chain': evo,
                    'evo_details': evo['evolution_details'][0] if evo['evolution_details'] else None,
                    'parent_pos': 0,
                    'angle': evo_idx * angle_step
                })
                evo_idx += 1

    def get_lycanroc_display_name(self, name):
        # Lycanroc formlarını düzgün göster
        if name.startswith('lycanroc-'):
            suffix = name.split('-')[1]
            form_map = {'midday': 'Midday', 'midnight': 'Midnight', 'dusk': 'Dusk'}
            return f"Lycanroc ({form_map.get(suffix, suffix.capitalize())})"
        return 'Lycanroc'

    def paintEvent(self, event):
        if not hasattr(self, 'pokemon_nodes') or not self.pokemon_nodes:
            return
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            w = self.width()
            h = self.height()
            center_x = w // 2
            center_y = h // 2

            # Find main node (depth 0)
            main_node = next((n for n in self.pokemon_nodes if n['depth'] == 0), None)
            if not main_node:
                print('No main node found in evolution chain!')
                return
            if main_node['pix'] is None:
                print('Main node pix is None!')
                return

            # Draw main node in center
            self.draw_pokemon_node(painter, center_x, center_y, main_node)

            # Draw evolutions in a circle
            evo_nodes = [n for n in self.pokemon_nodes if n['depth'] == 1]
            if evo_nodes:
                radius = min(w, h) * 0.35
                for node in evo_nodes:
                    angle_rad = math.radians(node['angle'])
                    node_x = center_x + radius * math.cos(angle_rad)
                    node_y = center_y + radius * math.sin(angle_rad)
                    # Draw evolution node
                    self.draw_pokemon_node(painter, node_x, node_y, node)
                    # Draw arrow
                    start_x = center_x + 32 * math.cos(angle_rad)
                    start_y = center_y + 32 * math.sin(angle_rad)
                    end_x = node_x - 32 * math.cos(angle_rad)
                    end_y = node_y - 32 * math.sin(angle_rad)
                    self.draw_curved_arrow(painter, start_x, start_y, end_x, end_y, node['evo_details'], node['angle'])
                    # Draw name label on the arrow
                    self.draw_name_on_arrow(painter, start_x, start_y, end_x, end_y, node)
        except Exception as e:
            import traceback
            print('paintEvent error:', e)
            traceback.print_exc()

    def draw_name_on_arrow(self, painter, x1, y1, x2, y2, node):
        # Okun ortasına isim ve arka plan kutusu çiz
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        display_name = node.get('display_name', node['name'].capitalize())
        types = node.get('types', [])
        if types:
            bg_color = self.type_color(types[0])
        else:
            bg_color = '#3a7a2a'
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(display_name) + 16
        text_height = metrics.height() + 4
        rect_x = int(mid_x - text_width/2)
        rect_y = int(mid_y - text_height/2)
        # Arka plan kutusu
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bg_color))
        painter.drawRoundedRect(rect_x, rect_y, text_width, text_height, 8, 8)
        # İsim
        painter.setPen(Qt.white)
        painter.drawText(rect_x, rect_y, text_width, text_height, Qt.AlignCenter, display_name)

    def draw_curved_arrow(self, painter, x1, y1, x2, y2, evo_details, angle):
        # Eğrisel ok çizimi
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        angle_rad = math.radians(angle)
        control_distance = 50
        ctrl_x = (x1 + x2) / 2 + control_distance * math.cos(angle_rad + math.pi/2)
        ctrl_y = (y1 + y2) / 2 + control_distance * math.sin(angle_rad + math.pi/2)
        path = QPainterPath()
        path.moveTo(x1, y1)
        path.quadTo(ctrl_x, ctrl_y, x2, y2)
        painter.drawPath(path)
        arrow_size = 10
        angle = math.atan2(y2 - ctrl_y, x2 - ctrl_x)
        arrow_x1 = x2 - arrow_size * math.cos(angle - math.pi/6)
        arrow_y1 = y2 - arrow_size * math.sin(angle - math.pi/6)
        arrow_x2 = x2 - arrow_size * math.cos(angle + math.pi/6)
        arrow_y2 = y2 - arrow_size * math.sin(angle + math.pi/6)
        painter.setBrush(QColor(Qt.black))
        painter.drawPolygon(QPolygonF([
            QPointF(x2, y2),
            QPointF(arrow_x1, arrow_y1),
            QPointF(arrow_x2, arrow_y2)
        ]))

    def evo_condition_icon(self, details):
        # Return (icon_text, color) or (icon_unicode, color) for the main evolution condition
        if details.get('item'):
            item = details['item']['name']
            # Common stones
            stone_icons = {
                'thunder-stone': ('⚡', '#f7d51d'),
                'fire-stone': ('🔥', '#e25822'),
                'water-stone': ('💧', '#3498db'),
                'leaf-stone': ('🍃', '#27ae60'),
                'moon-stone': ('🌙', '#b39ddb'),
                'sun-stone': ('☀️', '#fbc02d'),
                'dusk-stone': ('🌑', '#616161'),
                'dawn-stone': ('🌅', '#fbc02d'),
                'shiny-stone': ('✨', '#b2bec3'),
                'ice-stone': ('❄️', '#74b9ff'),
                'oval-stone': ('⚪', '#dfe6e9'),
                'king\'s-rock': ('👑', '#bfa14a'),
            }
            icon, color = stone_icons.get(item, ('🔸', '#888888'))
            return icon, color
        if details.get('min_level'):
            return f"Lv. {details['min_level']}", '#222222'
        if details.get('min_happiness'):
            return '❤️', '#e74c3c'
        if details.get('min_beauty'):
            return '💎', '#00b894'
        if details.get('min_affection'):
            return '💕', '#e84393'
        if details.get('time_of_day'):
            if details['time_of_day'] == 'day':
                return '☀️', '#fbc02d'
            elif details['time_of_day'] == 'night':
                return '🌙', '#636e72'
        if details.get('trigger') and details['trigger']['name'] == 'trade':
            return '🔄', '#0984e3'
        if details.get('known_move_type'):
            return '📘', '#6c5ce7'
        if details.get('held_item'):
            return '🎒', '#636e72'
        # Default
        return '?', '#888888'

    def get_form_label(self, node):
        # Try to extract region, form, or time info for display
        chain = node.get('chain', {})
        # Time of day
        evo_details = node.get('evo_details')
        if evo_details and evo_details.get('time_of_day'):
            t = evo_details['time_of_day']
            if t:
                return t.capitalize()
        # Region or form in species name
        name = node['name']
        if '-' in name:
            suffix = name.split('-')[1]
            # Common region/form suffixes
            region_map = {
                'alola': 'Alolan', 'galar': 'Galarian', 'hisui': 'Hisuian', 'paldea': 'Paldean',
                'dusk': 'Dusk', 'midday': 'Day', 'midnight': 'Night', 'dawn': 'Dawn',
                'mega': 'Mega', 'gigantamax': 'Gmax', 'origin': 'Origin', 'therian': 'Therian',
            }
            return region_map.get(suffix, suffix.capitalize())
        return ''

    def draw_pokemon_node(self, painter, x, y, node):
        node_size = 64
        image_size = 56
        types = node.get('types', [])
        if types:
            bg_color = self.type_color(types[0])
        else:
            bg_color = '#3a7a2a'
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(QColor(bg_color))
        painter.drawEllipse(int(x-node_size/2), int(y-node_size/2), node_size, node_size)
        painter.drawPixmap(int(x-image_size/2), int(y-image_size/2), image_size, image_size, node['pix'].scaled(image_size, image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # (İsim artık dairenin içinde çizilmiyor)
        # Draw form/region/time label if exists
        form_label = self.get_form_label(node)
        if form_label:
            font = QFont()
            font.setPointSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(QColor('#2d5aa6')))
            painter.drawText(int(x-node_size/2), int(y+node_size/2+30), node_size, 12, Qt.AlignCenter, form_label)

    def type_color(self, t):
        # Simple color map for types
        colors = {
            'grass': '#78C850', 'poison': '#A040A0', 'fire': '#F08030', 'water': '#6890F0',
            'bug': '#A8B820', 'normal': '#A8A878', 'flying': '#A890F0', 'electric': '#F8D030',
            'ground': '#E0C068', 'fairy': '#EE99AC', 'fighting': '#C03028', 'psychic': '#F85888',
            'rock': '#B8A038', 'steel': '#B8B8D0', 'ice': '#98D8D8', 'ghost': '#705898',
            'dragon': '#7038F8', 'dark': '#705848'
        }
        return colors.get(t, '#888888')

class StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.stat_bars = {}
        self.stat_labels = {}
        self.stat_names = {
            'hp': 'HP',
            'attack': 'Saldırı',
            'defense': 'Savunma',
            'special-attack': 'Özel Saldırı',
            'special-defense': 'Özel Savunma',
            'speed': 'Hız'
        }
        self.stat_colors = {
            'hp': '#FF5959',
            'attack': '#F5AC78',
            'defense': '#FAE078',
            'special-attack': '#9DB7F5',
            'special-defense': '#A7DB8D',
            'speed': '#FA92B2'
        }
        for key in self.stat_names:
            row = QHBoxLayout()
            label = QLabel(self.stat_names[key])
            label.setFixedWidth(110)
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(255)
            bar.setTextVisible(True)
            bar.setFormat('%v')
            bar.setFixedHeight(18)
            bar.setStyleSheet(f"QProgressBar::chunk {{ background: {self.stat_colors[key]}; }}")
            value_label = QLabel('0')
            value_label.setFixedWidth(30)
            value_label.setAlignment(Qt.AlignRight)
            row.addWidget(label)
            row.addWidget(bar, 1)
            row.addWidget(value_label)
            self.layout.addLayout(row)
            self.stat_bars[key] = bar
            self.stat_labels[key] = value_label
        # Toplam
        self.total_label = QLabel('Toplam: 0')
        self.total_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.total_label)
        self.layout.addStretch(1)

    def update_stats(self, stats):
        total = 0
        for stat in stats:
            name = stat['stat']['name']
            value = stat['base_stat']
            total += value
            if name in self.stat_bars:
                self.stat_bars[name].setValue(value)
                self.stat_labels[name].setText(str(value))
        self.total_label.setText(f'Toplam: {total}')

class PokemonGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cache = PersistentCache(CACHE_FILE)
        self.fetcher = PokemonDataFetcher(cache=self.cache)
        self.favorites = self.load_favorites()
        self.setup_ui()
        self.setup_menu()
        self.load_data()
        
    def setup_ui(self):
        self.setWindowTitle("Pokemon Veri Görüntüleyici")
        self.setMinimumSize(1000, 700)

        # Önce detay panelini oluştur
        self.pokemon_detail_widget = QWidget()
        detail_layout = QVBoxLayout()
        self.pokemon_detail_widget.setLayout(detail_layout)

        # --- Üst Bilgi Alanları ---
        info_layout = QHBoxLayout()
        detail_layout.addLayout(info_layout)

        # Kimlik Bilgileri
        self.id_group = QGroupBox("Kimlik Bilgileri")
        id_layout = QVBoxLayout()
        self.id_label = QLabel()
        id_layout.addWidget(self.id_label)
        self.id_group.setLayout(id_layout)
        info_layout.addWidget(self.id_group)

        # Açıklama
        self.desc_group = QGroupBox("Açıklama")
        desc_layout = QVBoxLayout()
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        desc_layout.addWidget(self.desc_label)
        self.desc_group.setLayout(desc_layout)
        info_layout.addWidget(self.desc_group)

        # Yumurta Grubu
        self.egg_group = QGroupBox("Yumurta Grubu")
        egg_layout = QVBoxLayout()
        self.egg_label = QLabel()
        egg_layout.addWidget(self.egg_label)
        self.egg_group.setLayout(egg_layout)
        info_layout.addWidget(self.egg_group)

        # Yetenekler
        self.ability_group = QGroupBox("Yetenekler")
        ability_layout = QVBoxLayout()
        self.ability_label = QLabel()
        ability_layout.addWidget(self.ability_label)
        self.ability_group.setLayout(ability_layout)
        info_layout.addWidget(self.ability_group)

        # Pokemon resmi
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        detail_layout.addWidget(self.image_label)

        # Pokemon adı
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        detail_layout.addWidget(self.name_label)

        # Pokemon türleri
        self.types_label = QLabel()
        self.types_label.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(self.types_label)

        # İstatistikler
        self.stats_widget = StatsWidget()
        detail_layout.addWidget(self.stats_widget)

        # Evrim zinciri
        self.evolution_widget = EvolutionChainWidget(evo_chain=None, current_name=None, fetcher=self.fetcher)
        detail_layout.addWidget(self.evolution_widget)

        # Hareketler
        self.moves_label = QLabel("Hareketler:")
        self.moves_label.setStyleSheet("font-weight: bold;")
        detail_layout.addWidget(self.moves_label)

        self.moves_scroll = QScrollArea()
        self.moves_scroll.setWidgetResizable(True)
        self.moves_scroll.setMinimumHeight(200)
        self.moves_widget = QWidget()
        self.moves_layout = QVBoxLayout()
        self.moves_widget.setLayout(self.moves_layout)
        self.moves_scroll.setWidget(self.moves_widget)
        detail_layout.addWidget(self.moves_scroll)

        # Evrim Şartları
        self.evo_conditions_group = QGroupBox("Evrim Şartları")
        evo_conditions_layout = QVBoxLayout()
        self.evo_conditions_label = QTextEdit()
        self.evo_conditions_label.setReadOnly(True)
        evo_conditions_layout.addWidget(self.evo_conditions_label)
        self.evo_conditions_group.setLayout(evo_conditions_layout)
        detail_layout.addWidget(self.evo_conditions_group)

        # Tip Avantajları/Zayıflıkları
        self.type_adv_group = QGroupBox("Tip Avantajları/Zayıflıkları")
        type_adv_layout = QVBoxLayout()
        self.type_weak_label = QLabel()
        self.type_strong_label = QLabel()
        self.type_immune_label = QLabel()
        type_adv_layout.addWidget(QLabel("<b>Zayıf Olduğu Tipler:</b>"))
        type_adv_layout.addWidget(self.type_weak_label)
        type_adv_layout.addWidget(QLabel("<b>Güçlü Olduğu Tipler:</b>"))
        type_adv_layout.addWidget(self.type_strong_label)
        type_adv_layout.addWidget(QLabel("<b>Bağışık Olduğu Tipler:</b>"))
        type_adv_layout.addWidget(self.type_immune_label)
        self.type_adv_group.setLayout(type_adv_layout)
        detail_layout.addWidget(self.type_adv_group)

        # Sprite Galerisi
        self.sprite_group = QGroupBox("Sprite Galerisi")
        sprite_layout = QGridLayout()
        self.sprite_labels = {}
        sprite_types = [
            ("Normal Dişi", "front_default"),
            ("Normal Erkek", "front_female"),
            ("Shiny Dişi", "front_shiny"),
            ("Shiny Erkek", "front_shiny_female")
        ]
        for i, (label, key) in enumerate(sprite_types):
            sprite_layout.addWidget(QLabel(label), 0, i)
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            sprite_layout.addWidget(img_label, 1, i)
            self.sprite_labels[key] = img_label
        self.sprite_group.setLayout(sprite_layout)
        detail_layout.addWidget(self.sprite_group)

        # Oyun/Bölge Bilgisi
        self.game_info_group = QGroupBox("Oyun/Bölge Bilgisi")
        game_info_layout = QVBoxLayout()
        self.game_info_label = QLabel()
        self.game_info_label.setWordWrap(True)
        game_info_layout.addWidget(self.game_info_label)
        self.game_info_group.setLayout(game_info_layout)
        detail_layout.addWidget(self.game_info_group)

        # Favoriler / Notlar
        self.fav_group = QGroupBox("Favoriler / Notlar")
        fav_layout = QVBoxLayout()
        self.fav_checkbox = QCheckBox("Favorilere ekle")
        self.fav_checkbox.stateChanged.connect(self.on_fav_changed)
        fav_layout.addWidget(self.fav_checkbox)
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Kendi notunuzu buraya yazabilirsiniz...")
        self.note_edit.textChanged.connect(self.on_note_changed)
        fav_layout.addWidget(self.note_edit)
        self.fav_group.setLayout(fav_layout)
        detail_layout.addWidget(self.fav_group)

        # Topluluk Linkleri
        self.links_group = QGroupBox("Topluluk Linkleri")
        links_layout = QHBoxLayout()
        self.bulba_link = QLabel()
        self.serebii_link = QLabel()
        self.smogon_link = QLabel()
        for lbl in [self.bulba_link, self.serebii_link, self.smogon_link]:
            lbl.setOpenExternalLinks(True)
            links_layout.addWidget(lbl)
        self.links_group.setLayout(links_layout)
        detail_layout.addWidget(self.links_group)

        # Bu Hareketi Öğrenebilen Pokémonlar
        self.move_learners_group = QGroupBox("Bu Hareketi Öğrenebilen Pokémonlar")
        move_learners_layout = QVBoxLayout()
        self.move_learners_label = QLabel()
        self.move_learners_label.setWordWrap(True)
        move_learners_layout.addWidget(self.move_learners_label)
        self.move_learners_group.setLayout(move_learners_layout)
        detail_layout.addWidget(self.move_learners_group)

        # Sonra splitter ve panelleri oluştur
        splitter = QSplitter()
        self.setCentralWidget(splitter)

        # Sol panel: Arama ve liste
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        self.left_search = QLineEdit()
        self.left_search.setPlaceholderText("Ara... (İsim veya ID)")
        self.left_search.textChanged.connect(self.filter_pokemon_list)
        left_layout.addWidget(self.left_search)

        self.pokemon_table = QTableWidget()
        self.pokemon_table.setColumnCount(2)
        self.pokemon_table.setHorizontalHeaderLabels(["İsim", "URL"])
        self.pokemon_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pokemon_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pokemon_table.setSelectionMode(QTableWidget.SingleSelection)
        self.pokemon_table.cellClicked.connect(self.on_pokemon_selected)
        self.pokemon_table.setMinimumWidth(120)
        left_layout.addWidget(self.pokemon_table)

        # Sağ panel: Detaylar
        right_widget = self.pokemon_detail_widget
        splitter.addWidget(right_widget)
        splitter.setSizes([150, 850])
        
        # Durum çubuğu
        self.statusBar().showMessage("Hazır")
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu('Dosya')
        
        clear_cache_action = QAction('Önbelleği Temizle', self)
        clear_cache_action.triggered.connect(self.clear_cache)
        file_menu.addAction(clear_cache_action)
        
        cache_size_action = QAction('Önbellek Boyutu', self)
        cache_size_action.triggered.connect(self.show_cache_size)
        file_menu.addAction(cache_size_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Çıkış', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('Yardım')
        
        about_action = QAction('Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def load_data(self):
        self.statusBar().showMessage("Veriler yükleniyor...")
        self.thread = DataFetcherThread(self.fetcher, 'pokemon')
        self.thread.finished.connect(self.on_data_loaded)
        self.thread.error.connect(self.on_error)
        self.thread.start()
        
    def on_data_loaded(self, data):
        self.pokemon_list = data
        self.filter_pokemon_list()
        self.statusBar().showMessage("Veriler yüklendi")
        
    def on_error(self, error_msg):
        QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata oluştu: {error_msg}")
        self.statusBar().showMessage("Hata oluştu")
        
    def search(self):
        print("search fonksiyonu çağrıldı")
        try:
            search_text = self.left_search.text().strip().lower()
            if not search_text:
                print("Arama metni boş, çıkılıyor.")
                return
            # search_type artık yok, varsayılan olarak 'pokemon' araması yap
            self.statusBar().showMessage("Aranıyor...")
            pokemon_data = self.fetcher.get_pokemon_data_safe(search_text)
            species_data = self.fetcher.get_pokemon_species(search_text)
            evolution_chain = None
            if species_data and species_data.get('evolution_chain'):
                evolution_chain = self.fetcher.get_evolution_chain(
                    species_data['evolution_chain']['url']
                )
            self.image_label.setPixmap(QPixmap.fromImage(QImage.fromData(self.fetcher.get_pokemon_image(pokemon_data['id']))))
            self.name_label.setText(pokemon_data['name'].capitalize())
            self.types_label.setText(', '.join([t['type']['name'].capitalize() for t in pokemon_data['types']]))
            self.stats_widget.update_stats(pokemon_data['stats'])
            self.evolution_widget.evo_chain = evolution_chain
            self.evolution_widget.current_name = pokemon_data['name']
            self.evolution_widget.prepare_nodes()
            self.evolution_widget.update()
            # Hareketler güncelle (gelişmiş görünüm)
            while self.moves_layout.count():
                item = self.moves_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            move_groups = {}
            for move in pokemon_data['moves']:
                for version in move['version_group_details']:
                    method = version['move_learn_method']['name']
                    if method not in move_groups:
                        move_groups[method] = []
                    move_groups[method].append({
                        'name': move['move']['name'],
                        'level': version.get('level_learned_at', 0)
                    })
            # Seviye ile öğrenilenler
            if 'level-up' in move_groups:
                html = '<b>Seviye ile Öğrenilen Hamleler</b><ul>'
                # Seviyeye göre sırala
                level_moves = sorted(move_groups['level-up'], key=lambda x: x['level'])
                last_level = None
                for m in level_moves:
                    if m['level'] != last_level:
                        if last_level is not None:
                            html += '</ul>'
                        html += f'<li><b>Seviye {m["level"]}:</b> <ul>'
                        last_level = m['level']
                    html += f'<li>{m["name"].capitalize()}</li>'
                if last_level is not None:
                    html += '</ul>'
                html += '</ul>'
                label = QLabel()
                label.setTextFormat(Qt.RichText)
                label.setText(html)
                label.setWordWrap(True)
                self.moves_layout.addWidget(label)
            # Diğer yöntemler
            for method, moves in move_groups.items():
                if method == 'level-up':
                    continue
                html = f'<b>{method.replace("-", " ").capitalize()} ile Öğrenilen Hamleler</b><ul>'
                for m in sorted(moves, key=lambda x: x['name']):
                    html += f'<li>{m["name"].capitalize()}</li>'
                html += '</ul>'
                label = QLabel()
                label.setTextFormat(Qt.RichText)
                label.setText(html)
                label.setWordWrap(True)
                self.moves_layout.addWidget(label)
            self.moves_layout.addStretch()
            self.statusBar().showMessage("Pokemon bulundu")
            
            # Kimlik Bilgileri
            gender_rate = species_data.get('gender_rate', -1)
            if gender_rate == -1:
                gender_text = 'Cinsiyetsiz'
            else:
                male = 100 - (gender_rate * 12.5)
                female = gender_rate * 12.5
                gender_text = f'Erkek: %{male:.1f}, Dişi: %{female:.1f}'
            id_text = (
                f"ID: {pokemon_data['id']}\n"
                f"Boy: {pokemon_data['height'] / 10}m\n"
                f"Ağırlık: {pokemon_data['weight'] / 10}kg\n"
                f"Tür: {', '.join([t['type']['name'].capitalize() for t in pokemon_data['types']])}\n"
                f"Yakalama Oranı: {species_data.get('capture_rate', 'Bilinmiyor')}\n"
                f"Cinsiyet Oranı: {gender_text}\n"
                f"Seviye Atlama Hızı: {species_data.get('growth_rate', {}).get('name', 'Bilinmiyor').replace('-', ' ').capitalize()}"
            )
            self.id_label.setText(id_text)

            # Açıklama
            flavor = next((f for f in species_data.get('flavor_text_entries', []) if f['language']['name'] == 'en'), None)
            self.desc_label.setText(flavor['flavor_text'].replace('\n', ' ') if flavor else 'Açıklama yok.')

            # Yumurta Grubu
            egg_groups = [g['name'].capitalize() for g in species_data.get('egg_groups', [])]
            self.egg_label.setText(', '.join(egg_groups) if egg_groups else 'Yok')

            # Yetenekler
            abilities = [a['ability']['name'].capitalize() for a in pokemon_data.get('abilities', [])]
            self.ability_label.setText(', '.join(abilities) if abilities else 'Yok')
            
            # Evrim Şartları metni
            def parse_evo_chain(chain):
                lines = []
                def walk(chain):
                    from_poke = chain['species']['name'].capitalize()
                    for evo in chain.get('evolves_to', []):
                        to_poke = evo['species']['name'].capitalize()
                        details = evo.get('evolution_details', [{}])[0]
                        conds = []
                        if details.get('min_level'):
                            conds.append(f"Seviye: {details['min_level']}")
                        if details.get('item'):
                            conds.append(f"Item: {details['item']['name'].capitalize()}")
                        if details.get('trigger') and details['trigger']['name'] != 'level-up':
                            conds.append(f"{details['trigger']['name'].capitalize()}")
                        if details.get('time_of_day'):
                            conds.append(f"Zaman: {details['time_of_day'].capitalize()}")
                        if details.get('min_happiness'):
                            conds.append(f"Mutluluk: {details['min_happiness']}")
                        if details.get('min_beauty'):
                            conds.append(f"Güzellik: {details['min_beauty']}")
                        if details.get('min_affection'):
                            conds.append(f"Bağlılık: {details['min_affection']}")
                        if details.get('held_item'):
                            conds.append(f"Tuttuğu eşya: {details['held_item']['name'].capitalize()}")
                        if details.get('known_move'):
                            conds.append(f"Bildiği hareket: {details['known_move']['name'].capitalize()}")
                        if details.get('known_move_type'):
                            conds.append(f"Bildiği tür: {details['known_move_type']['name'].capitalize()}")
                        if details.get('location'):
                            conds.append(f"Lokasyon: {details['location']['name'].capitalize()}")
                        if details.get('gender') is not None:
                            conds.append(f"Cinsiyet: {'Erkek' if details['gender']==1 else 'Dişi'}")
                        cond_str = ', '.join(conds) if conds else 'Level-up'
                        lines.append(f"{from_poke} → {to_poke}: {cond_str}")
                        walk(evo)
                walk(chain['chain'])
                return lines
            evo_lines = []
            if evolution_chain:
                evo_lines = parse_evo_chain(evolution_chain)
            self.evo_conditions_label.setPlainText('\n'.join(evo_lines) if evo_lines else 'Veri yok.')
            
            # Tip Avantajları/Zayıflıkları
            # Tüm tipleri çek
            all_types = [t['type']['name'] for t in pokemon_data['types']]
            type_chart = {}
            # Tip etkilerini hesapla (çarpanlar)
            # Tüm saldırı tipleri için çarpanları başlat
            for t in [
                'normal','fire','water','electric','grass','ice','fighting','poison','ground','flying','psychic','bug','rock','ghost','dragon','dark','steel','fairy']:
                type_chart[t] = 1.0
            for poke_type in all_types:
                type_data = self.fetcher.get_type_data(poke_type)
                for rel in type_data['damage_relations']['double_damage_from']:
                    type_chart[rel['name']] *= 2
                for rel in type_data['damage_relations']['half_damage_from']:
                    type_chart[rel['name']] *= 0.5
                for rel in type_data['damage_relations']['no_damage_from']:
                    type_chart[rel['name']] *= 0
            weak = [t.capitalize() for t, v in type_chart.items() if v > 1]
            strong = [t.capitalize() for t, v in type_chart.items() if 0 < v < 1]
            immune = [t.capitalize() for t, v in type_chart.items() if v == 0]
            self.type_weak_label.setText(', '.join(weak) if weak else '-')
            self.type_strong_label.setText(', '.join(strong) if strong else '-')
            self.type_immune_label.setText(', '.join(immune) if immune else '-')
            
            # Sprite Galerisi
            sprites = pokemon_data.get('sprites', {})
            for key, label in self.sprite_labels.items():
                url = sprites.get(key)
                if url:
                    try:
                        img_data = requests.get(url).content
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_data)
                        label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    except Exception:
                        label.clear()
                else:
                    label.clear()
            
            # Oyun/Bölge Bilgisi
            games = sorted(set([g['version']['name'].replace('-', ' ').capitalize() for g in pokemon_data.get('game_indices', [])]))
            generation = species_data.get('generation', {}).get('name', '').replace('-', ' ').capitalize()
            regions = [r['name'].replace('-', ' ').capitalize() for r in species_data.get('paldea_forms', [])] if 'paldea_forms' in species_data else []
            game_text = (
                f"Göründüğü Oyunlar: {', '.join(games) if games else '-'}\n"
                f"Jenerasyon: {generation if generation else '-'}\n"
                f"Bölgeler: {', '.join(regions) if regions else '-'}"
            )
            self.game_info_label.setText(game_text)
            
            # Favoriler / Notlar güncelle
            self.current_pokemon_name = pokemon_data['name']
            fav = self.favorites.get(self.current_pokemon_name, {})
            self.fav_checkbox.blockSignals(True)
            self.fav_checkbox.setChecked(self.current_pokemon_name in self.favorites)
            self.fav_checkbox.blockSignals(False)
            self.note_edit.blockSignals(True)
            self.note_edit.setPlainText(fav.get('note', ''))
            self.note_edit.blockSignals(False)
            
            # Topluluk Linkleri
            poke_name = pokemon_data['name'].capitalize()
            bulba_url = f'https://bulbapedia.bulbagarden.net/wiki/{poke_name}_(Pokémon)'
            serebii_url = f'https://www.serebii.net/pokedex-swsh/{poke_name.lower()}/'
            smogon_url = f'https://www.smogon.com/dex/ss/pokemon/{poke_name.lower()}/'
            self.bulba_link.setText(f'<a href="{bulba_url}">Bulbapedia</a>')
            self.serebii_link.setText(f'<a href="{serebii_url}">Serebii</a>')
            self.smogon_link.setText(f'<a href="{smogon_url}">Smogon</a>')
            
            # Bu hareketi öğrenebilen Pokémonlar
            learners = pokemon_data.get('learned_by_pokemon', [])
            if learners:
                names = ', '.join([p['name'].capitalize() for p in learners])
                self.move_learners_label.setText(names)
            else:
                self.move_learners_label.setText('Veri yok.')
            
            print("search fonksiyonu bitti")
        except Exception as e:
            print(f"search fonksiyonunda hata: {e}")
            QMessageBox.critical(self, "Hata", f"Beklenmeyen hata: {str(e)}")

    def clear_cache(self):
        reply = QMessageBox.question(self, 'Önbelleği Temizle',
                                   'Tüm önbellek verilerini temizlemek istediğinizden emin misiniz?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                   
        if reply == QMessageBox.Yes:
            self.fetcher.clear_image_cache()
            self.cache.data = {'pokemon': {}, 'move': {}, 'ability': {}, 'item': {}, 'images': {}}
            self.cache.save()
            QMessageBox.information(self, 'Bilgi', 'Önbellek temizlendi.')
            
    def show_cache_size(self):
        image_cache_size = self.fetcher.get_image_cache_size()
        data_cache_size = len(str(self.cache.data)) / (1024 * 1024)  # MB cinsinden
        total_size = image_cache_size + data_cache_size
        
        QMessageBox.information(self, 'Önbellek Boyutu',
                              f'Resim Önbelleği: {image_cache_size:.2f} MB\n'
                              f'Veri Önbelleği: {data_cache_size:.2f} MB\n'
                              f'Toplam: {total_size:.2f} MB')
                              
    def show_about(self):
        QMessageBox.about(self, 'Pokemon Veri Görüntüleyici Hakkında',
                         'Pokemon Veri Görüntüleyici v1.0\n\n'
                         'Bu uygulama, Pokemon verilerini görüntülemek için tasarlanmıştır.\n'
                         'PokeAPI kullanılarak geliştirilmiştir.\n\n'
                         'Özellikler:\n'
                         '- Pokemon, hareket, yetenek ve eşya bilgilerini görüntüleme\n'
                         '- Evrim zincirlerini görselleştirme\n'
                         '- İstatistikleri grafiksel olarak gösterme\n'
                         '- Önbellekleme ile hızlı veri erişimi\n'
                         '- Resim önbellekleme\n\n'
                         '© 2024 Pokemon Veri Görüntüleyici')

    def load_favorites(self):
        try:
            with open(FAV_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_favorites(self):
        try:
            with open(FAV_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_fav_changed(self):
        name = getattr(self, 'current_pokemon_name', None)
        if not name:
            return
        if self.fav_checkbox.isChecked():
            if name not in self.favorites:
                self.favorites[name] = {'note': self.note_edit.toPlainText()}
        else:
            if name in self.favorites:
                del self.favorites[name]
        self.save_favorites()

    def on_note_changed(self):
        name = getattr(self, 'current_pokemon_name', None)
        if not name:
            return
        if self.fav_checkbox.isChecked():
            self.favorites[name] = {'note': self.note_edit.toPlainText()}
            self.save_favorites()

    def filter_pokemon_list(self):
        text = self.left_search.text().strip().lower()
        self.pokemon_table.setRowCount(0)
        for p in getattr(self, 'pokemon_list', []):
            name = p['name']
            url = p['url']
            if text in name.lower() or text in url.lower() or text in str(p.get('id', '')):
                row = self.pokemon_table.rowCount()
                self.pokemon_table.insertRow(row)
                self.pokemon_table.setItem(row, 0, QTableWidgetItem(name.capitalize()))
                self.pokemon_table.setItem(row, 1, QTableWidgetItem(url))

    def on_pokemon_selected(self, row, col):
        name = self.pokemon_table.item(row, 0).text().strip().lower()
        print(f"Seçilen: {name}")
        self.search()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PokemonGUI()
    window.show()
    sys.exit(app.exec_())

# Build talimatı (Windows için):
# 1. pokeball.ico dosyasını proje klasörüne koyun.
# 2. Terminalde: pip install pyinstaller
# 3. Terminalde: pyinstaller --onefile --windowed --icon pokeball.ico pokemon_gui.py
# Çıktı: dist/pokemon_gui.exe dosyasını çift tıklayarak çalıştırabilirsiniz. 