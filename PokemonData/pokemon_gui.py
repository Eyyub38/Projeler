import sys
import requests
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QComboBox, QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QSplitter, QProgressBar, QMessageBox, QSizePolicy, QGridLayout, QGroupBox, QFrame, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon

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
        ''')
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Sol panel: kategori ve progress bar ve liste
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
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
        self.list_table = QTableWidget()
        self.list_table.setColumnCount(2)
        self.list_table.setHorizontalHeaderLabels(['İsim', 'Detay'])
        self.list_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_table.itemClicked.connect(self.on_item_single_clicked)
        self.list_table.setColumnWidth(0, 200)
        self.list_table.setColumnWidth(1, 400)
        self.list_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.list_table, 10)
        # Sağ panel: detaylar
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
        info_layout.addWidget(self.label_id)
        info_layout.addWidget(self.label_size)
        info_layout.addWidget(self.label_weight)
        info_layout.addWidget(self.label_type)
        self.desc_box = QGroupBox("Açıklama")
        desc_layout = QVBoxLayout(self.desc_box)
        self.label_desc = QLabel("")
        self.label_desc.setWordWrap(True)
        desc_layout.addWidget(self.label_desc)
        self.image_box = QGroupBox("Resim")
        image_layout = QVBoxLayout(self.image_box)
        self.pokemon_image = QLabel()
        self.pokemon_image.setAlignment(Qt.AlignCenter)
        self.pokemon_image.setMinimumHeight(120)
        image_layout.addWidget(self.pokemon_image)
        self.stats_box = QGroupBox("Temel İstatistikler")
        stats_layout = QVBoxLayout(self.stats_box)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(120)
        stats_layout.addWidget(self.stats_text)
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
        right_layout.addWidget(self.type_box)
        right_layout.addWidget(self.sprite_box)
        right_layout.addWidget(self.region_box)
        right_layout.addWidget(self.fav_box)
        right_layout.addWidget(self.links_box)
        right_layout.addWidget(self.move_learners_box)
        right_layout.addStretch(1)
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 5)
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
        self.label_desc.setText("")
        self.stats_text.clear()
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
        self.update_list_table(items)
        self.progress_bar.setVisible(False)
    def on_error(self, error_msg):
        QMessageBox.critical(self, "Hata", f"Veri yüklenirken bir hata oluştu: {error_msg}")
        self.progress_bar.setVisible(False)
    def update_list_table(self, items):
        self.list_table.setRowCount(len(items))
        for i, item in enumerate(items):
            name_item = QTableWidgetItem(item['name'].capitalize())
            url_item = QTableWidgetItem(item['url'])
            self.list_table.setItem(i, 0, name_item)
            self.list_table.setItem(i, 1, url_item)
    def on_form_selected(self, idx):
        # When user selects a form, update the details
        if hasattr(self, 'form_data_list') and 0 <= idx < len(self.form_data_list):
            data, species = self.form_data_list[idx]
            self.display_pokemon_info(data, species, update_form_selector=False)
    def on_item_double_clicked(self, item):
        name = self.list_table.item(item.row(), 0).text().lower()
        if self.current_data_type == 'pokemon':
            try:
                # Get all forms for this species
                species = self.fetcher.get_pokemon_species(name)
                varieties = species.get('varieties', [])
                self.form_data_list = []
                self.form_selector.clear()
                for var in varieties:
                    form_name = var['pokemon']['name']
                    data = self.fetcher.get_pokemon_data(form_name)
                    self.form_data_list.append((data, species))
                    display_name = data['name'].capitalize()
                    # Bölgesel form varsa ekle
                    if '-' in form_name:
                        region = form_name.split('-')[1].capitalize()
                        display_name += f" ({region})"
                    self.form_selector.addItem(display_name)
                self.form_selector.setVisible(len(varieties) > 1)
                # Varsayılan olarak ilk formu göster
                self.display_pokemon_info(self.form_data_list[0][0], self.form_data_list[0][1], update_form_selector=False)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"{name} bulunamadı!")
        elif self.current_data_type == 'hareket':
            try:
                data = self.fetcher.get_move_data(name)
                self.display_move_info(data)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"{name} bulunamadı!")
        elif self.current_data_type == 'yetenek':
            try:
                data = self.fetcher.get_ability_data(name)
                self.display_ability_info(data)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"{name} bulunamadı!")
        elif self.current_data_type == 'eşya':
            try:
                data = self.fetcher.get_item_data(name)
                self.display_item_info(data)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"{name} bulunamadı!")
    def on_item_single_clicked(self, item):
        self.on_item_double_clicked(item)
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
        stats_html = "<table border='1' cellpadding='3' style='border-collapse:collapse;'><tr><th>İstatistik</th><th>Değer</th></tr>"
        for stat in data['stats']:
            stats_html += f"<tr><td>{stat['stat']['name'].capitalize()}</td><td>{stat['base_stat']}</td></tr>"
        stats_html += "</table>"
        self.stats_text.setHtml(stats_html)
        # Yumurta grubu
        eggs = ', '.join([e['name'].capitalize() for e in species['egg_groups']])
        self.egg_text.setText(eggs)
        # Yetenekler
        abilities = ', '.join([a['ability']['name'].capitalize() for a in data['abilities']])
        self.abilities_text.setText(abilities)
        # Hamleler
        moves_html = "<ul>"
        for move in data['moves'][:15]:
            move_name = move['move']['name'].capitalize()
            methods = []
            for vgd in move['version_group_details']:
                method = vgd['move_learn_method']['name']
                level = vgd['level_learned_at']
                if method == 'level-up':
                    methods.append(f"Seviye: {level}")
                else:
                    methods.append(method.replace('-', ' ').capitalize())
            moves_html += f"<li>{move_name} <i>({' / '.join(set(methods))})</i></li>"
        moves_html += "</ul>"
        self.moves_text.setHtml(moves_html)
        # Evrim zinciri
        evo_chain_url = species['evolution_chain']['url']
        evo_chain = self.fetcher.get_evolution_chain(evo_chain_url)
        self.evo_text.setText(self.render_evolution_chain(evo_chain, data['name']))
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
    def render_evolution_chain(self, evo_chain, current_name):
        # Show all possible next evolutions and regional forms
        def find_current(chain, target_name):
            species = chain['species']['name']
            if species == target_name:
                return chain
            for evo in chain['evolves_to']:
                found = find_current(evo, target_name)
                if found:
                    return found
            return None
        def get_evo_text(evo):
            evo_species = evo['species']['name'].capitalize()
            details = evo['evolution_details'][0] if evo['evolution_details'] else None
            condition = ''
            if details:
                if details.get('min_level'):
                    condition = f" (Seviye: {details['min_level']})"
                if details.get('item'):
                    condition += f" (Eşya: {details['item']['name'].capitalize()})"
                if details.get('trigger'):
                    condition += f" ({details['trigger']['name'].capitalize()})"
                if details.get('location'):
                    condition += f" ({details['location']['name'].capitalize()})"
                if details.get('known_move_type'):
                    condition += f" ({details['known_move_type']['name'].capitalize()} move)"
                if details.get('time_of_day') and details['time_of_day']:
                    condition += f" ({details['time_of_day'].capitalize()})"
                if details.get('min_happiness'):
                    condition += f" (Happiness)"
                if details.get('min_beauty'):
                    condition += f" (Beauty)"
                if details.get('min_affection'):
                    condition += f" (Affection)"
                if details.get('relative_physical_stats'):
                    condition += f" (Physical stats)"
                if details.get('gender') is not None:
                    condition += f" (Gender: {details['gender']})"
                if details.get('held_item'):
                    condition += f" (Held: {details['held_item']['name'].capitalize()})"
                if details.get('turn_upside_down'):
                    condition += f" (Turn upside down)"
            return f"{evo_species}{condition}"
        chain = evo_chain['chain']
        current_chain = find_current(chain, current_name)
        if not current_chain:
            # fallback: show all first evolutions
            current_chain = chain
        if current_chain['evolves_to']:
            evos = [get_evo_text(evo) for evo in current_chain['evolves_to']]
            return ' / '.join(evos)
        else:
            return f"{current_chain['species']['name'].capitalize()} (Son aşama)"
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
        # Show only relevant boxes for move
        self.info_box.hide()
        self.desc_box.hide()
        self.image_box.hide()
        self.egg_box.hide()
        self.abilities_box.hide()
        self.moves_box.hide()
        self.evo_box.hide()
        self.type_box.hide()
        self.region_box.show()
        self.fav_box.hide()
        self.links_box.show()
        self.sprite_box.show()
        self.stats_box.show()
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
        self.stats_text.setHtml(info)
        self.label_desc.setText("")
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")
        self.type_effect_text.setText("")
        # Sprite Galerisi (show example Pokémon sprites for this move)
        from random import choice
        example_ids = [25, 1]
        for i, poke_id in enumerate(example_ids):
            img_data = requests.get(f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke_id}.png').content
            img = QImage.fromData(img_data)
            pix = QPixmap.fromImage(img)
            self.sprite_labels[i].setPixmap(pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.sprite_labels[i].setToolTip(f"Örnek: {['Pikachu','Bulbasaur'][i]}")
        for i in range(2, 4):
            self.sprite_labels[i].clear()
            self.sprite_labels[i].setText("")
        # Oyun/Bölge Bilgisi
        self.region_text.setText('-')
        # Favoriler/Notlar kutusu gizli
        # Topluluk Linkleri
        self.links_label.setText(self.get_community_links(data['name']))
        # Bu Hareketi Öğrenebilen Pokémonlar
        self.move_learners_text.setText(self.get_move_learners(data))
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
        self.stats_box.show()
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
        self.stats_text.setHtml(info)
        self.label_desc.setText("")
        self.egg_text.setText("")
        self.abilities_text.setText("")
        self.moves_text.clear()
        self.evo_text.setText("")
        self.type_effect_text.setText("")
        self.region_text.setText("")
        self.fav_checkbox.setChecked(False)
        self.note_text.setText("")
        self.links_label.setText("")
    def display_item_info(self, data):
        # Only show stats/info box
        self.info_box.hide()
        self.desc_box.hide()
        self.image_box.hide()
        self.egg_box.hide()
        self.abilities_box.hide()
        self.moves_box.hide()
        self.evo_box.hide()
        self.stats_box.show()
        self.pokemon_image.clear()
        info = f"<h2>{data['name'].capitalize()}</h2><p><b>ID:</b> {data['id']}</p><p><b>Fiyat:</b> {data['cost']}</p>"
        if data['effect_entries']:
            info += f"<h3>Açıklama</h3><p>{data['effect_entries'][0]['effect']}</p>"
        self.stats_text.setHtml(info)
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