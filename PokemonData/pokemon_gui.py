import sys
import requests
import os
import json
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QComboBox, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QSplitter, QProgressBar, QMessageBox, QSizePolicy, QGridLayout, QGroupBox, QFrame, QCheckBox, QScrollArea, QLineEdit, QListWidget, QPushButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QSize, QPointF
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QPen, QColor, QFont, QPainterPath, QPolygonF
import numpy as np
from fetcher import PersistentCache, PokemonDataFetcher

CACHE_FILE = 'pokemon_cache.json'

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

class PokemonCardWidget(QWidget):
    def __init__(self, name, image_data, types, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 180)
        self.setStyleSheet("background: #f8fafc; border-radius: 10px; border: 1px solid #b0b8c1;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Pokemon image
        img_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        img_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)

        # Name
        name_label = QLabel(name.capitalize())
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #2d5aa6;")
        layout.addWidget(name_label)

        # Types
        type_layout = QHBoxLayout()
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
            type_layout.addWidget(type_label)
        layout.addLayout(type_layout)

    def type_color(self, t):
        colors = {
            'grass': '#78C850', 'poison': '#A040A0', 'fire': '#F08030', 'water': '#6890F0',
            'bug': '#A8B820', 'normal': '#A8A878', 'flying': '#A890F0', 'electric': '#F8D030',
            'ground': '#E0C068', 'fairy': '#EE99AC', 'fighting': '#C03028', 'psychic': '#F85888',
            'rock': '#B8A038', 'steel': '#B8B8D0', 'ice': '#98D8D8', 'ghost': '#705898',
            'dragon': '#7038F8', 'dark': '#705848'
        }
        return colors.get(t, '#888888')

class PokemonGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cache = PersistentCache(CACHE_FILE)
        self.fetcher = PokemonDataFetcher(cache=self.cache)
        self.initUI()
    def initUI(self):
        self.setWindowTitle('Pokemon Veri Görüntüleyici')
        self.setGeometry(100, 100, 1400, 900)
        # Set window icon
        if os.path.exists('pokeball.ico'):
            self.setWindowIcon(QIcon('pokeball.ico'))
        # Set modern stylesheet
        self.setStyleSheet('''
            QMainWindow { background: #f6f8fc; }
            QGroupBox { background: #f0f4fa; border: 1px solid #b0b8c1; border-radius: 6px; margin-top: 8px; }
            QGroupBox::title { color: #2d5aa6; font-weight: bold; subcontrol-origin: margin; left: 10px; top: 2px; }
            QLabel, QCheckBox { font-size: 13px; }
            QTableWidget { background: #ffffff; border: 1px solid #b0b8c1; }
            QComboBox, QLineEdit, QTextEdit { background: #f8fafc; border: 1px solid #b0b8c1; border-radius: 4px; }
            QPushButton { background: #e53e3e; color: white; border-radius: 4px; padding: 4px 12px; font-weight: bold; }
            QPushButton:hover { background: #c53030; }
            QProgressBar { border: 1px solid #b0b8c1; border-radius: 4px; text-align: center; }
            QLineEdit#searchBox { 
                padding: 8px;
                font-size: 14px;
                background: #ffffff;
                border: 2px solid #e53e3e;
                border-radius: 6px;
            }
            QLineEdit#searchBox:focus {
                border: 2px solid #c53030;
            }
        ''')
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sol panel: kategori, arama ve liste
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Arama kutusu
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("Ara... (İsim veya ID)")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_box)
        left_layout.addLayout(search_layout)

        # Veri tipi seçici
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(['Pokemon', 'Hareket', 'Yetenek', 'Eşya'])
        self.data_type_combo.currentIndexChanged.connect(self.on_data_type_changed)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(120)
        left_layout.addWidget(QLabel('Veri Tipi:'))
        left_layout.addWidget(self.data_type_combo)
        left_layout.addWidget(self.progress_bar)
        left_layout.addStretch(1)

        # Kart görünümü için scroll area ve grid
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setStyleSheet("border: none;")
        self.card_container = QWidget()
        self.card_grid = QGridLayout(self.card_container)
        self.card_grid.setSpacing(12)
        self.card_grid.setContentsMargins(0, 0, 0, 0)
        self.card_scroll.setWidget(self.card_container)
        left_layout.addWidget(self.card_scroll, 10)

        # Sağ panel: detaylar (scroll area içinde)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("""
            QScrollArea {
                background: #f6f8fc;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f4fa;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #b0b8c1;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f4fa;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #b0b8c1;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # Form seçici
        self.form_selector = QComboBox()
        self.form_selector.setVisible(False)
        self.form_selector.currentIndexChanged.connect(self.on_form_selected)
        right_layout.addWidget(self.form_selector)

        # Üst grid: ID/size/type, description, image, stats
        top_grid = QGridLayout()
        top_grid.setSpacing(10)
        self.info_box = QGroupBox("Kimlik Bilgileri")
        info_layout = QVBoxLayout(self.info_box)
        self.label_id = QLabel("ID: ")
        self.label_size = QLabel("Boy: ")
        self.label_weight = QLabel("Ağırlık: ")
        self.label_type = QLabel("Tür: ")
        self.label_catch_rate = QLabel("Yakalanma Oranı: ")
        self.label_gender_ratio = QLabel("Cinsiyet Oranı: ")
        self.label_leveling_rate = QLabel("Seviye Atlama Hızı: ")
        info_layout.addWidget(self.label_id)
        info_layout.addWidget(self.label_size)
        info_layout.addWidget(self.label_weight)
        info_layout.addWidget(self.label_type)
        info_layout.addWidget(self.label_catch_rate)
        info_layout.addWidget(self.label_gender_ratio)
        info_layout.addWidget(self.label_leveling_rate)
        self.desc_box = QGroupBox("Açıklama")
        desc_layout = QVBoxLayout(self.desc_box)
        self.label_desc = QTextEdit()
        self.label_desc.setReadOnly(True)
        self.label_desc.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #b0b8c1;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        desc_layout.addWidget(self.label_desc)
        self.image_box = QGroupBox("Resim")
        image_layout = QVBoxLayout(self.image_box)
        self.pokemon_image = QLabel()
        self.pokemon_image.setAlignment(Qt.AlignCenter)
        self.pokemon_image.setMinimumHeight(120)
        image_layout.addWidget(self.pokemon_image)
        self.stats_box = QGroupBox("Temel İstatistikler")
        stats_layout = QVBoxLayout(self.stats_box)
        self.stats_widget = StatsWidget()
        stats_layout.addWidget(self.stats_widget)
        top_grid.addWidget(self.info_box, 0, 0)
        top_grid.addWidget(self.desc_box, 0, 1)
        top_grid.addWidget(self.image_box, 0, 2)
        top_grid.addWidget(self.stats_box, 0, 3)
        mid_grid = QGridLayout()
        mid_grid.setSpacing(10)
        self.egg_box = QGroupBox("Yumurta Grubu")
        egg_layout = QVBoxLayout(self.egg_box)
        self.egg_text = QLabel("")
        egg_layout.addWidget(self.egg_text)
        self.abilities_box = QGroupBox("Yetenekler")
        abilities_layout = QVBoxLayout(self.abilities_box)
        self.abilities_text = QLabel("")
        self.abilities_text.setWordWrap(True)
        abilities_layout.addWidget(self.abilities_text)
        self.moves_box = QGroupBox("Öğrenebildiği Hamleler")
        moves_layout = QVBoxLayout(self.moves_box)
        self.moves_text = QTextEdit()
        self.moves_text.setReadOnly(True)
        moves_layout.addWidget(self.moves_text)
        mid_grid.addWidget(self.egg_box, 0, 0)
        mid_grid.addWidget(self.abilities_box, 0, 1)
        mid_grid.addWidget(self.moves_box, 0, 2)
        self.evo_box = QGroupBox("Evrim Zinciri")
        evo_layout = QHBoxLayout(self.evo_box)
        self.evo_text = QLabel("")
        self.evo_text.setWordWrap(True)
        evo_layout.addWidget(self.evo_text)
        # Yeni: Evrim Şartları Listbox
        self.evo_conditions_box = QGroupBox("Evrim Şartları")
        evo_cond_layout = QVBoxLayout(self.evo_conditions_box)
        self.evo_conditions_list = QListWidget()
        evo_cond_layout.addWidget(self.evo_conditions_list)
        # Tip Avantajları/Zayıflıkları
        self.type_box = QGroupBox("Tip Avantajları/Zayıflıkları")
        type_layout = QVBoxLayout(self.type_box)
        self.type_effect_text = QLabel("")
        self.type_effect_text.setWordWrap(True)
        type_layout.addWidget(self.type_effect_text)
        # Sprite Galerisi
        self.sprite_box = QGroupBox("Sprite Galerisi")
        sprite_layout = QHBoxLayout(self.sprite_box)
        self.sprite_labels = []
        for i in range(4):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumSize(60, 60)
            self.sprite_labels.append(lbl)
            sprite_layout.addWidget(lbl)
        # Oyun/Bölge Bilgisi
        self.region_box = QGroupBox("Oyun/Bölge Bilgisi")
        region_layout = QVBoxLayout(self.region_box)
        self.region_text = QLabel("")
        self.region_text.setWordWrap(True)
        region_layout.addWidget(self.region_text)
        # Favoriler/Notlar
        self.fav_box = QGroupBox("Favoriler / Notlar")
        fav_layout = QVBoxLayout(self.fav_box)
        self.fav_checkbox = QCheckBox("Favorilere ekle")
        self.fav_checkbox.stateChanged.connect(self.on_fav_changed)
        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText("Kendi notunuzu buraya yazabilirsiniz...")
        self.note_text.textChanged.connect(self.on_note_changed)
        fav_layout.addWidget(self.fav_checkbox)
        fav_layout.addWidget(self.note_text)
        # Topluluk Linkleri
        self.links_box = QGroupBox("Topluluk Linkleri")
        links_layout = QVBoxLayout(self.links_box)
        self.links_label = QLabel("")
        self.links_label.setOpenExternalLinks(True)
        links_layout.addWidget(self.links_label)
        # Bu Hareketi Öğrenebilen Pokémonlar
        self.move_learners_box = QGroupBox("Bu Hareketi Öğrenebilen Pokémonlar")
        move_learners_layout = QVBoxLayout(self.move_learners_box)
        self.move_learners_text = QTextEdit()
        self.move_learners_text.setReadOnly(True)
        move_learners_layout.addWidget(self.move_learners_text)
        # Sağ paneli birleştir
        right_layout.addLayout(top_grid)
        right_layout.addLayout(mid_grid)
        right_layout.addWidget(self.evo_box)
        right_layout.addWidget(self.evo_conditions_box)
        right_layout.addWidget(self.type_box)
        right_layout.addWidget(self.sprite_box)
        right_layout.addWidget(self.region_box)
        right_layout.addWidget(self.fav_box)
        right_layout.addWidget(self.links_box)
        right_layout.addWidget(self.move_learners_box)
        right_layout.addStretch(1)

        # Scroll area'ya sağ paneli ekle
        right_scroll.setWidget(right_panel)

        # Ana layout'a panelleri ekle
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_scroll, 5)  # right_panel yerine right_scroll kullanıyoruz
        self.on_data_type_changed(0)
        # Favoriler ve notlar için depolama
        self.favorites = {}
        self.notes = {}
    def on_data_type_changed(self, index):
        self.current_data_type = self.data_type_combo.currentText().lower()
        self.pokemon_image.clear()
        self.label_id.setText("ID: ")
        self.label_size.setText("Boy: ")
        self.label_weight.setText("Ağırlık: ")
        self.label_type.setText("Tür: ")
        self.label_catch_rate.setText("Yakalanma Oranı: ")
        self.label_gender_ratio.setText("Cinsiyet Oranı: ")
        self.label_leveling_rate.setText("Seviye Atlama Hızı: ")
        self.label_desc.setText("")
        self.stats_widget.update_stats([])
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")
        self.type_effect_text.setText("")
        self.load_items()
    def load_items(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.fetcher_thread = DataFetcherThread(self.fetcher, self.current_data_type)
        self.fetcher_thread.finished.connect(self.on_items_loaded)
        self.fetcher_thread.error.connect(self.on_error)
        self.fetcher_thread.start()
    def on_items_loaded(self, items):
        if self.current_data_type == 'pokemon':
            # Debug için yazdırma
            print("Toplam Pokemon sayısı:", len(items))
            print("Lycanroc formları:")
            for item in items:
                if 'lycanroc' in item['name']:
                    print(f"- {item['name']}")
            
            # Lycanroc formlarını özel olarak işle
            processed_items = []
            lycanroc_forms = []
            
            for item in items:
                name = item['name']
                if name.startswith('lycanroc-'):
                    print(f"Lycanroc formu bulundu: {name}")
                    lycanroc_forms.append(item)
                else:
                    processed_items.append(item)
            
            # Eğer lycanroc formları varsa, ana lycanroc'u ekle ve formları onun altına yerleştir
            if lycanroc_forms:
                print(f"Bulunan Lycanroc form sayısı: {len(lycanroc_forms)}")
                # Ana lycanroc'u bul veya oluştur
                main_lycanroc = next((item for item in items if item['name'] == 'lycanroc'), None)
                if not main_lycanroc:
                    print("Ana Lycanroc manuel olarak oluşturuluyor...")
                    # İlk formun URL'sini kullanarak ana Lycanroc'u oluştur
                    first_form = lycanroc_forms[0]
                    main_lycanroc = {
                        'name': 'lycanroc',
                        'url': first_form['url'].replace('lycanroc-midday', 'lycanroc')  # URL'yi düzelt
                    }
                
                print("Ana Lycanroc listeye eklendi")
                processed_items.append(main_lycanroc)
                # Formları ana lycanroc'un altına ekle
                for form in lycanroc_forms:
                    form['parent'] = 'lycanroc'  # Parent bilgisini ekle
                    processed_items.append(form)
                    print(f"Form eklendi: {form['name']}")
            
            print(f"İşlenmiş toplam Pokemon sayısı: {len(processed_items)}")
            self.update_list_table(processed_items)
        else:
            self.update_list_table(items)
        self.progress_bar.setVisible(False)
    def on_error(self, error_msg):
        QMessageBox.critical(self, "Hata", f"Veri yüklenirken bir hata oluştu: {error_msg}")
        self.progress_bar.setVisible(False)
    def update_list_table(self, items):
        # Sadece Pokemon için kart görünümü uygula
        if self.current_data_type == 'pokemon':
            # Kartları temizle
            for i in reversed(range(self.card_grid.count())):
                widget = self.card_grid.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            # Kartları ekle
            row, col = 0, 0
            for idx, item in enumerate(items):
                name = item['name']
                try:
                    data = self.fetcher.get_pokemon_data_safe(name)
                    types = [t['type']['name'] for t in data['types']]
                    img_data = self.fetcher.get_pokemon_image(data['id'])
                except Exception:
                    types = []
                    img_data = b''
                card = PokemonCardWidget(name, img_data, types)
                card.mousePressEvent = lambda e, n=name: self.on_card_clicked(n)
                self.card_grid.addWidget(card, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        else:
            # Diğer veri tipleri için eski tabloyu kullanmak isterseniz buraya ekleyebilirsiniz
            pass
    def on_card_clicked(self, name):
        # Kart tıklanınca detayları göster
        if self.current_data_type == 'pokemon':
            try:
                species = self.fetcher.get_pokemon_species(name)
                varieties = species.get('varieties', [])
                self.form_data_list = []
                self.form_selector.clear()
                for var in varieties:
                    form_name = var['pokemon']['name']
                    data = self.fetcher.get_pokemon_data_safe(form_name)
                    self.form_data_list.append((data, species))
                    display_name = data['name'].capitalize()
                    if '-' in form_name:
                        region = form_name.split('-')[1].capitalize()
                        display_name += f" ({region})"
                    self.form_selector.addItem(display_name)
                self.form_selector.setVisible(len(varieties) > 1)
                self.display_pokemon_info(self.form_data_list[0][0], self.form_data_list[0][1], update_form_selector=False)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"{name} bulunamadı!")
    def on_form_selected(self, idx):
        # When user selects a form, update the details
        if hasattr(self, 'form_data_list') and 0 <= idx < len(self.form_data_list):
            data, species = self.form_data_list[idx]
            self.display_pokemon_info(data, species, update_form_selector=False)
    def display_pokemon_info(self, data, species, update_form_selector=True):
        # Show all detail boxes
        self.info_box.show()
        self.desc_box.show()
        self.image_box.show()
        self.stats_box.show()
        self.egg_box.show()
        self.abilities_box.show()
        self.moves_box.show()
        self.evo_box.show()
        self.type_box.show()
        self.sprite_box.show()
        self.region_box.show()
        self.fav_box.show()
        self.links_box.show()
        self.move_learners_box.show()
        if update_form_selector:
            self.form_selector.setVisible(False)
        # Kimlik bilgileri
        self.label_id.setText(f"ID: {data['id']}")
        self.label_size.setText(f"Boy: {data['height']/10}m")
        self.label_weight.setText(f"Ağırlık: {data['weight']/10}kg")
        types = [t['type']['name'] for t in data['types']]
        types_str = ', '.join(t.capitalize() for t in types)
        self.label_type.setText(f"Tür: {types_str}")
        
        # Catch Rate ve Gender Ratio
        catch_rate = species.get('capture_rate', 'N/A')
        self.label_catch_rate.setText(f"Yakalanma Oranı: {catch_rate}")
        
        gender_rate = species.get('gender_rate', -1)
        if gender_rate == -1:
            gender_ratio = "Cinsiyetsiz"
        else:
            female_percent = (gender_rate / 8) * 100
            male_percent = 100 - female_percent
            gender_ratio = f"Erkek: %{male_percent:.1f}, Dişi: %{female_percent:.1f}"
        self.label_gender_ratio.setText(f"Cinsiyet Oranı: {gender_ratio}")
        
        # Leveling Rate
        growth_rate = species.get('growth_rate', {}).get('name', 'N/A')
        growth_rate_map = {
            'slow': 'Yavaş',
            'medium': 'Normal',
            'fast': 'Hızlı',
            'medium-slow': 'Orta-Yavaş',
            'slow-then-very-fast': 'Yavaş-Sonra Çok Hızlı',
            'fast-then-very-slow': 'Hızlı-Sonra Çok Yavaş'
        }
        leveling_rate = growth_rate_map.get(growth_rate, growth_rate.capitalize())
        self.label_leveling_rate.setText(f"Seviye Atlama Hızı: {leveling_rate}")
        
        # Açıklama
        flavor = next((entry['flavor_text'] for entry in species['flavor_text_entries'] if entry['language']['name']=='en'), "")
        self.label_desc.setText(flavor.replace('\n', ' ').replace('\f', ' '))
        # Resim
        image_data = self.fetcher.get_pokemon_image(data['id'])
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        self.pokemon_image.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # Sprite Galerisi
        sprites = data.get('sprites', {})
        sprite_urls = [
            (sprites.get('front_default'), 'Normal Erkek'),
            (sprites.get('front_shiny'), 'Shiny Erkek'),
            (sprites.get('front_female'), 'Normal Dişi'),
            (sprites.get('front_shiny_female'), 'Shiny Dişi'),
        ]
        for i, (url, label) in enumerate(sprite_urls):
            if url:
                img_data = requests.get(url).content
                img = QImage.fromData(img_data)
                pix = QPixmap.fromImage(img)
                self.sprite_labels[i].setPixmap(pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.sprite_labels[i].setToolTip(label)
            else:
                self.sprite_labels[i].clear()
                self.sprite_labels[i].setText(label)
        # Temel istatistikler
        self.stats_widget.update_stats(data['stats'])
        # Yumurta grubu
        eggs = ', '.join([e['name'].capitalize() for e in species['egg_groups']])
        self.egg_text.setText(eggs)
        # Yetenekler
        abilities = ', '.join([a['ability']['name'].capitalize() for a in data['abilities']])
        self.abilities_text.setText(abilities)
        # Hamleler
        moves_info = {}  # {move_name: {methods: set(), levels: set()}}
        for move in data['moves']:
            move_name = move['move']['name'].capitalize()
            if move_name not in moves_info:
                moves_info[move_name] = {'methods': set(), 'levels': set()}
            
            for vgd in move['version_group_details']:
                method = vgd['move_learn_method']['name']
                level = vgd['level_learned_at']
                if method == 'level-up':
                    moves_info[move_name]['levels'].add(level)
                else:
                    moves_info[move_name]['methods'].add(method)

        # Öğrenme yöntemlerinin Türkçe karşılıkları
        method_names = {
            'machine': 'TM/HM',
            'tutor': 'Yetenek Öğreticisi',
            'egg': 'Yumurta',
            'stadium-surfing-pikachu': 'Stadyum Surfing Pikachu',
            'light-ball-egg': 'Light Ball Yumurta',
            'form-change': 'Form Değişimi',
            'zygarde-cube': 'Zygarde Cube',
            'special': 'Özel'
        }

        # Hamleleri grupla
        level_moves = {}  # {level: [move_names]}
        other_moves = {}  # {method: [move_names]}
        
        for move_name, info in moves_info.items():
            # Seviye ile öğrenilen hamleleri ekle
            for level in info['levels']:
                if level not in level_moves:
                    level_moves[level] = []
                level_moves[level].append(move_name)
            
            # Diğer yöntemlerle öğrenilen hamleleri ekle
            for method in info['methods']:
                if method not in other_moves:
                    other_moves[method] = []
                other_moves[method].append(move_name)

        moves_html = "<h3>Seviye ile Öğrenilen Hamleler</h3>"
        if level_moves:
            moves_html += "<ul>"
            for level in sorted(level_moves.keys()):
                moves = sorted(level_moves[level])
                moves_html += f"<li><b>Seviye {level}:</b> {', '.join(moves)}</li>"
            moves_html += "</ul>"
        else:
            moves_html += "<p>Seviye ile öğrenilen hamle yok.</p>"

        # Diğer öğrenme yöntemleri
        for method, moves in other_moves.items():
            if method in method_names:
                moves_html += f"<h3>{method_names[method]} ile Öğrenilen Hamleler</h3>"
                moves_html += "<ul>"
                for move in sorted(moves):
                    # Bu hamlenin tüm öğrenme yöntemlerini göster
                    methods = []
                    if moves_info[move]['levels']:
                        levels = sorted(moves_info[move]['levels'])
                        methods.append(f"Seviye {', '.join(map(str, levels))}")
                    for m in sorted(moves_info[move]['methods']):
                        if m in method_names:
                            methods.append(method_names[m])
                    moves_html += f"<li>{move} <i>({', '.join(methods)})</i></li>"
                moves_html += "</ul>"

        self.moves_text.setHtml(moves_html)
        # Evrim zinciri
        evo_chain_url = species['evolution_chain']['url']
        evo_chain = self.fetcher.get_evolution_chain(evo_chain_url)
        # Remove old widget if exists
        for i in reversed(range(self.evo_box.layout().count())):
            w = self.evo_box.layout().itemAt(i).widget()
            if w:
                w.setParent(None)
        # Evrim ağacı widget'ı ve scroll area
        evo_widget = EvolutionChainWidget(evo_chain, data['name'], self.fetcher)
        evo_scroll = QScrollArea()
        evo_scroll.setWidgetResizable(True)
        evo_scroll.setWidget(evo_widget)
        evo_scroll.setMinimumHeight(450)
        evo_scroll.setStyleSheet("""
            QScrollArea {
                background: #f6f8fc;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f4fa;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #b0b8c1;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f4fa;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #b0b8c1;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        self.evo_box.setMinimumHeight(450)
        self.evo_box.layout().addWidget(evo_scroll)
        # Evrim şartlarını listbox'a ekle
        self.populate_evo_conditions(evo_chain)
        # Tip avantajları/zayıflıkları
        self.type_effect_text.setText(self.get_type_effectiveness(types))
        # Oyun/Bölge Bilgisi
        self.region_text.setText(self.get_region_info(data, species))
        # Topluluk Linkleri
        self.links_label.setText(self.get_community_links(data['name']))
        # Favoriler/Notlar
        name = data['name']
        self.fav_checkbox.blockSignals(True)
        self.fav_checkbox.setChecked(self.favorites.get(name, False))
        self.fav_checkbox.blockSignals(False)
        self.note_text.blockSignals(True)
        self.note_text.setText(self.notes.get(name, ""))
        self.note_text.blockSignals(False)
        # Bu Hareketi Öğrenebilen Pokémonlar
        self.move_learners_text.setText(self.get_move_learners(data))
    def populate_evo_conditions(self, evo_chain):
        self.evo_conditions_list.clear()
        def traverse(chain):
            species = chain['species']['name']
            for evo in chain.get('evolves_to', []):
                evo_name = evo['species']['name']
                for detail in evo.get('evolution_details', []):
                    conds = self.evo_condition_text(detail)
                    self.evo_conditions_list.addItem(f"{species.capitalize()} → {evo_name.capitalize()}: {conds}")
                traverse(evo)
        traverse(evo_chain['chain'])
    def get_type_effectiveness(self, types):
        # Type chart (simplified, can be expanded)
        type_chart = {
            'normal':     {'weak': ['fighting'], 'immune': ['ghost'], 'strong': []},
            'fire':       {'weak': ['water', 'ground', 'rock'], 'strong': ['grass', 'ice', 'bug', 'steel'], 'immune': []},
            'water':      {'weak': ['electric', 'grass'], 'strong': ['fire', 'ground', 'rock'], 'immune': []},
            'electric':   {'weak': ['ground'], 'strong': ['water', 'flying'], 'immune': []},
            'grass':      {'weak': ['fire', 'ice', 'poison', 'flying', 'bug'], 'strong': ['water', 'ground', 'rock'], 'immune': []},
            'ice':        {'weak': ['fire', 'fighting', 'rock', 'steel'], 'strong': ['grass', 'ground', 'flying', 'dragon'], 'immune': []},
            'fighting':   {'weak': ['flying', 'psychic', 'fairy'], 'strong': ['normal', 'ice', 'rock', 'dark', 'steel'], 'immune': []},
            'poison':     {'weak': ['ground', 'psychic'], 'strong': ['grass', 'fairy'], 'immune': []},
            'ground':     {'weak': ['water', 'grass', 'ice'], 'strong': ['fire', 'electric', 'poison', 'rock', 'steel'], 'immune': ['electric']},
            'flying':     {'weak': ['electric', 'ice', 'rock'], 'strong': ['grass', 'fighting', 'bug'], 'immune': ['ground']},
            'psychic':    {'weak': ['bug', 'ghost', 'dark'], 'strong': ['fighting', 'poison'], 'immune': []},
            'bug':        {'weak': ['fire', 'flying', 'rock'], 'strong': ['grass', 'psychic', 'dark'], 'immune': []},
            'rock':       {'weak': ['water', 'grass', 'fighting', 'ground', 'steel'], 'strong': ['fire', 'ice', 'flying', 'bug'], 'immune': []},
            'ghost':      {'weak': ['ghost', 'dark'], 'strong': ['psychic', 'ghost'], 'immune': ['normal', 'fighting']},
            'dragon':     {'weak': ['ice', 'dragon', 'fairy'], 'strong': ['dragon'], 'immune': []},
            'dark':       {'weak': ['fighting', 'bug', 'fairy'], 'strong': ['psychic', 'ghost'], 'immune': ['psychic']},
            'steel':      {'weak': ['fire', 'fighting', 'ground'], 'strong': ['ice', 'rock', 'fairy'], 'immune': ['poison']},
            'fairy':      {'weak': ['poison', 'steel'], 'strong': ['fighting', 'dragon', 'dark'], 'immune': ['dragon']},
        }
        # Calculate weaknesses and strengths
        weaknesses = set()
        strengths = set()
        immunities = set()
        for t in types:
            chart = type_chart.get(t, {})
            weaknesses.update(chart.get('weak', []))
            strengths.update(chart.get('strong', []))
            immunities.update(chart.get('immune', []))
        # Remove immunities from weaknesses
        weaknesses = weaknesses - immunities
        # Format
        if not types:
            return ''
        return (
            f"Zayıf Olduğu Tipler: {', '.join(w.capitalize() for w in weaknesses) if weaknesses else '-'}\n"
            f"Güçlü Olduğu Tipler: {', '.join(s.capitalize() for s in strengths) if strengths else '-'}\n"
            f"Bağışık Olduğu Tipler: {', '.join(i.capitalize() for i in immunities) if immunities else '-'}"
        )
    def get_region_info(self, data, species):
        # Get games from game_indices
        games = [g['version']['name'].replace('-', ' ').capitalize() for g in data.get('game_indices', [])]
        games = sorted(set(games))
        # Get generation/region from species
        gen = species.get('generation', {}).get('name', '').replace('-', ' ').capitalize()
        # Try to get region from pokedex_numbers
        region = ''
        pokedexes = species.get('pokedex_numbers', [])
        if pokedexes:
            region = ', '.join([p['pokedex']['name'].capitalize() for p in pokedexes])
        info = ''
        if games:
            info += f"Göründüğü Oyunlar: {', '.join(games)}\n"
        if gen:
            info += f"Jenerasyon: {gen}\n"
        if region:
            info += f"Bölgeler: {region}"
        return info if info else '-'
    def display_move_info(self, data):
        # Sadece gerekli kutuları göster
        self.info_box.hide()
        self.desc_box.hide()
        self.image_box.hide()
        self.egg_box.hide()
        self.abilities_box.hide()
        self.moves_box.hide()
        self.evo_box.hide()
        self.type_box.hide()
        self.region_box.hide()
        self.fav_box.hide()
        self.sprite_box.hide()
        self.stats_widget.update_stats([])
        self.links_box.show()
        self.move_learners_box.show()
        self.pokemon_image.clear()

        # Temel istatistikler (move info)
        info = f"""
        <h2>{data['name'].capitalize()}</h2>
        <p><b>ID:</b> {data['id']}</p>
        <p><b>Güç:</b> {data['power'] if data['power'] else 'N/A'}</p>
        <p><b>PP:</b> {data['pp']}</p>
        <p><b>Doğruluk:</b> {data['accuracy'] if data['accuracy'] else 'N/A'}</p>
        <p><b>Tür:</b> {data['type']['name'].capitalize()}</p>
        <p><b>Hasar Türü:</b> {data['damage_class']['name'].capitalize()}</p>
        """
        if data['effect_entries']:
            effect = ""
            for entry in data['effect_entries']:
                if entry['language']['name'] == 'en':
                    effect = entry['effect']
                    break
            if effect:
                info += f"<h3>Açıklama</h3><p>{effect}</p>"
        self.stats_widget.update_stats(data['stats'])
        self.label_desc.setText("")
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")
        self.type_effect_text.setText("")
        self.region_text.setText("")
        self.fav_checkbox.setChecked(False)
        self.note_text.setText("")
        # Topluluk Linkleri
        self.links_label.setText(self.get_community_links(data['name']))
        # Bu Hareketi Öğrenebilen Pokémonlar
        self.move_learners_text.setText(self.get_move_learners(data))

    def on_search_text_changed(self, text):
        # Arama metni değiştiğinde listeyi filtrele
        text = text.lower()
        for row in range(self.card_grid.count()):
            widget = self.card_grid.itemAt(row).widget()
            if widget:
                name = widget.name.lower()
                # İsim veya ID ile arama
                if text in name or (text.isdigit() and text in widget.name):
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def get_move_learners(self, move_data):
        # Try to get Pokémon that can learn this move (from 'learned_by_pokemon')
        learners = move_data.get('learned_by_pokemon', [])
        if not learners:
            return 'Veri yok.'
        lines = []
        for poke in learners:
            name = poke['name'].capitalize()
            lines.append(f"- {name}")
        return '\n'.join(lines)

    def display_ability_info(self, data):
        # Only show stats/info box
        self.info_box.hide()
        self.desc_box.hide()
        self.image_box.hide()
        self.egg_box.hide()
        self.abilities_box.hide()
        self.moves_box.hide()
        self.evo_box.hide()
        self.stats_widget.update_stats([])
        self.type_box.hide()
        self.sprite_box.hide()
        self.region_box.hide()
        self.fav_box.hide()
        self.links_box.hide()
        self.pokemon_image.clear()
        # Get English effect
        effect = ""
        for entry in data['effect_entries']:
            if entry['language']['name'] == 'en':
                effect = entry['effect']
                break
        info = f"<h2>{data['name'].capitalize()}</h2><p><b>ID:</b> {data['id']}</p>"
        if effect:
            info += f"<h3>Açıklama</h3><p>{effect}</p>"
        self.stats_widget.update_stats(data['stats'])
        self.label_desc.setText("")
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")

    def display_item_info(self, data):
        # Only show stats/info box
        self.info_box.hide()
        self.desc_box.hide()
        self.image_box.hide()
        self.egg_box.hide()
        self.abilities_box.hide()
        self.moves_box.hide()
        self.evo_box.hide()
        self.stats_widget.update_stats([])
        self.pokemon_image.clear()
        info = f"<h2>{data['name'].capitalize()}</h2><p><b>ID:</b> {data['id']}</p><p><b>Fiyat:</b> {data['cost']}</p>"
        if data['effect_entries']:
            info += f"<h3>Açıklama</h3><p>{data['effect_entries'][0]['effect']}</p>"
        self.stats_widget.update_stats(data['stats'])
        self.label_desc.setText("")
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")

    def on_fav_changed(self, state):
        # Store favorite status for current Pokémon
        if hasattr(self, 'form_data_list') and self.form_selector.currentIndex() >= 0:
            data, _ = self.form_data_list[self.form_selector.currentIndex()]
            self.favorites[data['name']] = bool(state)

    def on_note_changed(self):
        # Store note for current Pokémon
        if hasattr(self, 'form_data_list') and self.form_selector.currentIndex() >= 0:
            data, _ = self.form_data_list[self.form_selector.currentIndex()]
            self.notes[data['name']] = self.note_text.toPlainText()

    def get_community_links(self, name):
        name_cap = name.capitalize()
        name_dash = name.replace(' ', '-').lower()
        bulbapedia = f'https://bulbapedia.bulbagarden.net/wiki/{name_cap}_(Pokémon)'
        serebii = f'https://www.serebii.net/pokedex-swsh/{name_dash}/'
        smogon = f'https://www.smogon.com/dex/ss/pokemon/{name_dash}/'
        return (
            f'<a href="{bulbapedia}">Bulbapedia</a> | '
            f'<a href="{serebii}">Serebii</a> | '
            f'<a href="{smogon}">Smogon</a>'
        )

    def evo_condition_text(self, details):
        conds = []
        if details.get('min_level'):
            conds.append(f"Seviye: {details['min_level']}")
        if details.get('item'):
            conds.append(f"Eşya: {details['item']['name'].capitalize()}")
        if details.get('trigger'):
            conds.append(details['trigger']['name'].capitalize())
        if details.get('location'):
            conds.append(f"{details['location']['name'].capitalize()}")
        if details.get('known_move_type'):
            conds.append(f"{details['known_move_type']['name'].capitalize()} move")
        if details.get('time_of_day') and details['time_of_day']:
            conds.append(f"{details['time_of_day'].capitalize()}")
        if details.get('min_happiness'):
            conds.append("Happiness")
        if details.get('min_beauty'):
            conds.append("Beauty")
        if details.get('min_affection'):
            conds.append("Affection")
        if details.get('relative_physical_stats'):
            conds.append("Physical stats")
        if details.get('gender') is not None:
            conds.append(f"Gender: {details['gender']}")
        if details.get('held_item'):
            conds.append(f"Held: {details['held_item']['name'].capitalize()}")
        if details.get('turn_upside_down'):
            conds.append("Turn upside down")
        return ', '.join(conds) if conds else "-"

def main():
    app = QApplication(sys.argv)
    ex = PokemonGUI()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

# Build talimatı (Windows için):
# 1. pokeball.ico dosyasını proje klasörüne koyun.
# 2. Terminalde: pip install pyinstaller
# 3. Terminalde: pyinstaller --onefile --windowed --icon pokeball.ico pokemon_gui.py
# Çıktı: dist/pokemon_gui.exe dosyasını çift tıklayarak çalıştırabilirsiniz. 