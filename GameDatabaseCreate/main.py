import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QSpinBox, QTextEdit, QTabWidget, QDialog)
from PySide6.QtCore import Qt
from database_manager import DatabaseManager, DataType, Pokemon, Move, Item, BaseStats, Evolution
from dialogs import PokemonDialog, MoveDialog, ItemDialog

class PokemonDatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Pokemon Database Manager')
        self.setGeometry(100, 100, 1400, 800)  # Increased width for more columns
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Tab widget oluştur
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Her veri tipi için tab oluştur
        self.pokemon_tab = self.create_pokemon_tab()
        self.move_tab = self.create_move_tab()
        self.item_tab = self.create_item_tab()
        
        tabs.addTab(self.pokemon_tab, "Pokemon")
        tabs.addTab(self.move_tab, "Moves")
        tabs.addTab(self.item_tab, "Items")
        
        # Verileri yükle
        self.load_all_data()
        
    def create_pokemon_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Arama ve filtreleme bölümü
        search_layout = QHBoxLayout()
        
        # Arama
        self.pokemon_search = QLineEdit()
        self.pokemon_search.setPlaceholderText("Search Pokemon by name...")
        self.pokemon_search.textChanged.connect(lambda: self.search_entries(DataType.POKEMON))
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.pokemon_search)
        
        # Tip filtresi
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems([
            "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
            "Fighting", "Poison", "Ground", "Flying", "Psychic",
            "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
        ])
        self.type_filter.currentTextChanged.connect(lambda: self.filter_pokemon_by_type())
        search_layout.addWidget(QLabel("Filter by Type:"))
        search_layout.addWidget(self.type_filter)
        
        layout.addLayout(search_layout)
        
        # Tablo
        self.pokemon_table = QTableWidget()
        self.pokemon_table.setColumnCount(12)
        self.pokemon_table.setHorizontalHeaderLabels([
            "ID", "Name", "Types", "Forms", "HP", "Attack", "Defense",
            "Sp. Attack", "Sp. Defense", "Speed", "Abilities", "Evolutions"
        ])
        
        # Sütun genişliklerini ayarla
        header = self.pokemon_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)  # Types
        header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)  # Forms
        for i in range(4, 10):  # Stats columns
            header.setSectionResizeMode(i, header.ResizeMode.Fixed)
        header.setSectionResizeMode(10, header.ResizeMode.ResizeToContents)  # Abilities
        header.setSectionResizeMode(11, header.ResizeMode.ResizeToContents)  # Evolutions
        
        self.pokemon_table.setColumnWidth(0, 50)  # ID
        for i in range(4, 10):  # Stats columns
            self.pokemon_table.setColumnWidth(i, 70)
        
        layout.addWidget(self.pokemon_table)
        
        # Butonlar
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Pokemon")
        edit_btn = QPushButton("Edit Pokemon")
        delete_btn = QPushButton("Delete Pokemon")
        export_btn = QPushButton("Export to JSON")
        
        add_btn.clicked.connect(lambda: self.show_pokemon_dialog())
        edit_btn.clicked.connect(lambda: self.show_pokemon_dialog(self.get_selected_id(DataType.POKEMON)))
        delete_btn.clicked.connect(lambda: self.delete_entry(DataType.POKEMON))
        export_btn.clicked.connect(self.export_pokemon_data)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        
        return widget
    
    def create_move_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Arama bölümü
        search_layout = QHBoxLayout()
        self.move_search = QLineEdit()
        self.move_search.setPlaceholderText("Move ara...")
        self.move_search.textChanged.connect(lambda: self.search_entries(DataType.MOVE))
        search_layout.addWidget(self.move_search)
        layout.addLayout(search_layout)
        
        # Tablo
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(8)
        self.move_table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Power", "Accuracy", "PP", "Category", "Description"
        ])
        layout.addWidget(self.move_table)
        
        # Butonlar
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Move")
        edit_btn = QPushButton("Edit Move")
        delete_btn = QPushButton("Delete Move")
        
        add_btn.clicked.connect(lambda: self.show_move_dialog())
        edit_btn.clicked.connect(lambda: self.show_move_dialog(self.get_selected_id(DataType.MOVE)))
        delete_btn.clicked.connect(lambda: self.delete_entry(DataType.MOVE))
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)
        
        return widget
    
    def create_item_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Arama bölümü
        search_layout = QHBoxLayout()
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Item ara...")
        self.item_search.textChanged.connect(lambda: self.search_entries(DataType.ITEM))
        search_layout.addWidget(self.item_search)
        layout.addLayout(search_layout)
        
        # Tablo
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(6)
        self.item_table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Description", "Effect", "Price"
        ])
        layout.addWidget(self.item_table)
        
        # Butonlar
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Item")
        edit_btn = QPushButton("Edit Item")
        delete_btn = QPushButton("Delete Item")
        
        add_btn.clicked.connect(lambda: self.show_item_dialog())
        edit_btn.clicked.connect(lambda: self.show_item_dialog(self.get_selected_id(DataType.ITEM)))
        delete_btn.clicked.connect(lambda: self.delete_entry(DataType.ITEM))
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)
        
        return widget
    
    def load_all_data(self):
        """Tüm verileri tablolara yükler."""
        self.load_table_data(DataType.POKEMON)
        self.load_table_data(DataType.MOVE)
        self.load_table_data(DataType.ITEM)
    
    def load_table_data(self, data_type: DataType):
        """Belirtilen veri tipindeki verileri ilgili tabloya yükler."""
        data = self.db.get_all_entries(data_type)
        table = self.get_table_for_type(data_type)
        
        table.setRowCount(len(data))
        for row, entry in enumerate(data):
            if data_type == DataType.POKEMON:
                self._fill_pokemon_row(table, row, entry)
            elif data_type == DataType.MOVE:
                self._fill_move_row(table, row, entry)
            elif data_type == DataType.ITEM:
                self._fill_item_row(table, row, entry)
    
    def _fill_pokemon_row(self, table: QTableWidget, row: int, entry: dict):
        """Fills a row in the Pokemon table with data."""
        table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
        table.setItem(row, 1, QTableWidgetItem(entry['name']))
        table.setItem(row, 2, QTableWidgetItem(', '.join(entry['type'])))
        table.setItem(row, 3, QTableWidgetItem(', '.join(entry['forms'])))
        table.setItem(row, 4, QTableWidgetItem(str(entry['base_stats']['hp'])))
        table.setItem(row, 5, QTableWidgetItem(str(entry['base_stats']['attack'])))
        table.setItem(row, 6, QTableWidgetItem(str(entry['base_stats']['defense'])))
        table.setItem(row, 7, QTableWidgetItem(str(entry['base_stats']['sp_attack'])))
        table.setItem(row, 8, QTableWidgetItem(str(entry['base_stats']['sp_defense'])))
        table.setItem(row, 9, QTableWidgetItem(str(entry['base_stats']['speed'])))
        table.setItem(row, 10, QTableWidgetItem(', '.join(entry['abilities'])))
        
        # Format evolutions
        evolution_texts = []
        for evolution in entry['evolutions']:
            text = f"{evolution['next_form']} (Lv.{evolution['level']})"
            if evolution['condition']:
                text += f" - {evolution['condition']}"
            evolution_texts.append(text)
        table.setItem(row, 11, QTableWidgetItem('\n'.join(evolution_texts)))
        
        # Set row height based on content
        table.setRowHeight(row, max(25, len(evolution_texts) * 20))
    
    def _fill_move_row(self, table: QTableWidget, row: int, entry: dict):
        table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
        table.setItem(row, 1, QTableWidgetItem(entry['name']))
        table.setItem(row, 2, QTableWidgetItem(entry['type']))
        table.setItem(row, 3, QTableWidgetItem(str(entry['power'])))
        table.setItem(row, 4, QTableWidgetItem(str(entry['accuracy'])))
        table.setItem(row, 5, QTableWidgetItem(str(entry['pp'])))
        table.setItem(row, 6, QTableWidgetItem(entry['category']))
        table.setItem(row, 7, QTableWidgetItem(entry['description']))
    
    def _fill_item_row(self, table: QTableWidget, row: int, entry: dict):
        table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
        table.setItem(row, 1, QTableWidgetItem(entry['name']))
        table.setItem(row, 2, QTableWidgetItem(entry['type']))
        table.setItem(row, 3, QTableWidgetItem(entry['description']))
        table.setItem(row, 4, QTableWidgetItem(entry['effect']))
        table.setItem(row, 5, QTableWidgetItem(str(entry['price'])))
    
    def get_table_for_type(self, data_type: DataType) -> QTableWidget:
        """Veri tipine göre ilgili tabloyu döndürür."""
        tables = {
            DataType.POKEMON: self.pokemon_table,
            DataType.MOVE: self.move_table,
            DataType.ITEM: self.item_table
        }
        return tables[data_type]
    
    def get_selected_id(self, data_type: DataType) -> int:
        """Seçili satırın ID'sini döndürür."""
        table = self.get_table_for_type(data_type)
        selected_rows = table.selectedItems()
        if not selected_rows:
            return None
        return int(table.item(selected_rows[0].row(), 0).text())
    
    def search_entries(self, data_type: DataType):
        """Veri tipine göre arama yapar ve sonuçları tabloya yükler."""
        search_term = self.get_search_widget_for_type(data_type).text()
        results = self.db.search_entries(data_type, search_term)
        table = self.get_table_for_type(data_type)
        
        table.setRowCount(len(results))
        for row, entry in enumerate(results):
            if data_type == DataType.POKEMON:
                self._fill_pokemon_row(table, row, entry)
            elif data_type == DataType.MOVE:
                self._fill_move_row(table, row, entry)
            elif data_type == DataType.ITEM:
                self._fill_item_row(table, row, entry)
    
    def get_search_widget_for_type(self, data_type: DataType) -> QLineEdit:
        """Veri tipine göre arama widget'ını döndürür."""
        widgets = {
            DataType.POKEMON: self.pokemon_search,
            DataType.MOVE: self.move_search,
            DataType.ITEM: self.item_search
        }
        return widgets[data_type]
    
    def show_pokemon_dialog(self, pokemon_id: int = None):
        """Pokemon ekleme/düzenleme dialogunu gösterir."""
        dialog = PokemonDialog(self.db, pokemon_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data(DataType.POKEMON)
    
    def show_move_dialog(self, move_id: int = None):
        """Move ekleme/düzenleme dialogunu gösterir."""
        dialog = MoveDialog(self.db, move_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data(DataType.MOVE)
    
    def show_item_dialog(self, item_id: int = None):
        """Item ekleme/düzenleme dialogunu gösterir."""
        dialog = ItemDialog(self.db, item_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data(DataType.ITEM)
    
    def delete_entry(self, data_type: DataType):
        """Seçili veriyi siler."""
        entry_id = self.get_selected_id(data_type)
        if entry_id is None:
            QMessageBox.warning(self, "Warning", "Please select an entry to delete.")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                   "Are you sure you want to delete this entry?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_entry(data_type, entry_id)
            self.load_table_data(data_type)
    
    def filter_pokemon_by_type(self):
        """Filters Pokemon table by selected type."""
        selected_type = self.type_filter.currentText()
        if selected_type == "All Types":
            self.load_table_data(DataType.POKEMON)
            return
        
        data = self.db.get_all_entries(DataType.POKEMON)
        filtered_data = [pokemon for pokemon in data if selected_type in pokemon['type']]
        
        table = self.get_table_for_type(DataType.POKEMON)
        table.setRowCount(len(filtered_data))
        for row, entry in enumerate(filtered_data):
            self._fill_pokemon_row(table, row, entry)
    
    def export_pokemon_data(self):
        """Exports Pokemon data to a JSON file."""
        try:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Pokemon Data",
                "",
                "JSON Files (*.json)"
            )
            
            if file_path:
                data = self.db.get_all_entries(DataType.POKEMON)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Success", "Pokemon data exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = PokemonDatabaseApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 