import sys
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QColorDialog, QScrollArea, QGridLayout, QMessageBox,
                            QComboBox, QGroupBox, QSpinBox, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QPen, QPalette
from PyQt5.QtCore import Qt, QRect, QPoint
from PIL import Image
import numpy as np
from tileset_recolor import TilesetRecolor
from palette_config import SpritePaletteConfig, SpriteSection, ColorPalette

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tileset_recolor.log'),
        logging.StreamHandler()
    ]
)

class ColorButton(QPushButton):
    def __init__(self, color, main_window, parent=None):
        super().__init__(parent)
        self.color = color
        self.main_window = main_window
        self.setFixedSize(30, 30)
        self.setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); border: 1px solid black;")
        self.clicked.connect(self.change_color)

    def change_color(self):
        try:
            color = QColorDialog.getColor(QColor(*self.color))
            if color.isValid():
                self.color = (color.red(), color.green(), color.blue())
                self.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid black;")
                self.main_window.update_preview()
        except Exception as e:
            logging.error(f"Error changing color: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error changing color: {str(e)}")

class InteractiveSpriteView(QLabel):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        self.sprite_pixmap = None
        self.sections = []  # List of (name, QRect)
        self.selected_section = None
        self.drawing = False
        self.start_point = None
        self.end_point = None

    def set_sprite(self, pixmap):
        self.sprite_pixmap = pixmap
        self.update()

    def set_sections(self, sections, selected_name=None):
        self.sections = [(name, QRect(x, y, w, h)) for name, (x, y, w, h) in sections]
        self.selected_section = selected_name
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()
        elif event.button() == Qt.RightButton:
            # Section selection
            for name, rect in self.sections:
                if rect.contains(event.pos()):
                    self.main_window.select_section_from_view(name)
                    break

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing and self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            self.drawing = False
            self.start_point = None
            self.end_point = None
            # Bildir: yeni bölüm eklensin
            self.main_window.add_section_from_view(rect)
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if self.sprite_pixmap:
            # Sprite'ı ortala
            pixmap = self.sprite_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - pixmap.width()) // 2
            y = (self.height() - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)
            scale_x = pixmap.width() / self.sprite_pixmap.width()
            scale_y = pixmap.height() / self.sprite_pixmap.height()
            # Bölümleri çiz
            for name, rect in self.sections:
                pen = QPen(Qt.red if name == self.selected_section else Qt.green, 2)
                painter.setPen(pen)
                rx = int(rect.x() * scale_x + x)
                ry = int(rect.y() * scale_y + y)
                rw = int(rect.width() * scale_x)
                rh = int(rect.height() * scale_y)
                painter.drawRect(rx, ry, rw, rh)
            # Çizim sırasında geçici dikdörtgen
            if self.drawing and self.start_point and self.end_point:
                pen = QPen(Qt.blue, 2, Qt.DashLine)
                painter.setPen(pen)
                temp_rect = QRect(self.start_point, self.end_point).normalized()
                painter.drawRect(temp_rect)
        painter.end()

class TileMapView(QWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.setMouseTracking(True)
        self.zoom = 8  # 1 pixel = 8x8 px on screen
        self.offset = QPoint(0, 0)
        self.dragging = False
        self.last_mouse_pos = None
        self.tileset_img = None  # numpy array (H, W, 3)
        self.selected_color = (0, 0, 0)
        self.undo_stack = []

    def set_tileset(self, img_array):
        self.tileset_img = img_array.copy()
        self.update()

    def set_selected_color(self, color):
        self.selected_color = color

    def paintEvent(self, event):
        if self.tileset_img is None:
            return
        painter = QPainter(self)
        h, w, _ = self.tileset_img.shape
        # NumPy array'den QImage oluştur
        qim = QImage(self.tileset_img.data, w, h, 3 * w, QImage.Format_RGB888)
        # Zoom ve offset uygula
        target_rect = QRect(self.offset.x(), self.offset.y(), w * self.zoom, h * self.zoom)
        painter.drawImage(target_rect, qim)
        # Grid çizgileri
        pen = QPen(Qt.gray, 1)
        painter.setPen(pen)
        for y in range(h + 1):
            painter.drawLine(self.offset.x(), self.offset.y() + y * self.zoom, self.offset.x() + w * self.zoom, self.offset.y() + y * self.zoom)
        for x in range(w + 1):
            painter.drawLine(self.offset.x() + x * self.zoom, self.offset.y(), self.offset.x() + x * self.zoom, self.offset.y() + h * self.zoom)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.edit_pixel(event.pos())
        elif event.button() == Qt.RightButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.pos()
            self.update()
        elif event.buttons() & Qt.LeftButton:
            self.edit_pixel(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = False
            self.last_mouse_pos = None

    def wheelEvent(self, event):
        old_zoom = self.zoom
        if event.angleDelta().y() > 0:
            self.zoom = min(64, self.zoom + 1)
        else:
            self.zoom = max(1, self.zoom - 1)
        # Zoom merkezini mouse konumuna göre ayarla
        if self.tileset_img is not None and old_zoom != self.zoom:
            mouse_pos = event.pos()
            h, w, _ = self.tileset_img.shape
            rel_x = (mouse_pos.x() - self.offset.x()) / old_zoom
            rel_y = (mouse_pos.y() - self.offset.y()) / old_zoom
            self.offset = QPoint(
                int(mouse_pos.x() - rel_x * self.zoom),
                int(mouse_pos.y() - rel_y * self.zoom)
            )
        self.update()

    def edit_pixel(self, pos):
        if self.tileset_img is None:
            return
        x = (pos.x() - self.offset.x()) // self.zoom
        y = (pos.y() - self.offset.y()) // self.zoom
        h, w, _ = self.tileset_img.shape
        if 0 <= x < w and 0 <= y < h:
            # Undo stack
            self.undo_stack.append((x, y, tuple(self.tileset_img[y, x])))
            self.tileset_img[y, x] = self.selected_color
            self.update()
            self.main_window.update_tileset_from_grid(self.tileset_img)

    def undo(self):
        if self.undo_stack:
            x, y, old_color = self.undo_stack.pop()
            self.tileset_img[y, x] = old_color
            self.update()
            self.main_window.update_tileset_from_grid(self.tileset_img)

class TilesetRecolorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recolorer = TilesetRecolor()
        self.palette = []
        self.current_palette_color = (0, 0, 0)
        self.init_ui()

    def init_ui(self):
        try:
            self.setWindowTitle('Sprite Palette Editor')
            self.setGeometry(100, 100, 1400, 800)
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)

            # Left panel for palette (compact)
            left_panel = QWidget()
            left_panel.setFixedWidth(220)
            left_layout = QVBoxLayout(left_panel)
            load_btn = QPushButton('Load Sprite')
            load_btn.clicked.connect(self.load_tileset)
            left_layout.addWidget(load_btn)
            save_btn = QPushButton('Save Sprite')
            save_btn.clicked.connect(self.save_tileset)
            left_layout.addWidget(save_btn)
            undo_btn = QPushButton('Undo')
            undo_btn.clicked.connect(self.undo)
            left_layout.addWidget(undo_btn)
            # Palette management
            self.palette_combo = QComboBox()
            self.palette_combo.currentIndexChanged.connect(self.on_palette_changed)
            left_layout.addWidget(self.palette_combo)
            add_palette_btn = QPushButton('Add New Palette')
            add_palette_btn.clicked.connect(self.add_new_palette)
            left_layout.addWidget(add_palette_btn)
            # Palette grid in a scroll area (max height)
            self.palette_grid_widget = QWidget()
            self.palette_grid = QGridLayout(self.palette_grid_widget)
            self.palette_grid.setContentsMargins(0, 0, 0, 0)
            self.palette_grid.setSpacing(4)
            palette_scroll = QScrollArea()
            palette_scroll.setWidgetResizable(True)
            palette_scroll.setWidget(self.palette_grid_widget)
            palette_scroll.setMaximumHeight(180)
            left_layout.addWidget(palette_scroll)
            left_panel.setLayout(left_layout)

            # Right panel for grid
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            self.tilemap_view = TileMapView(self)
            self.tilemap_scroll = QScrollArea()
            self.tilemap_scroll.setWidgetResizable(True)
            self.tilemap_scroll.setWidget(self.tilemap_view)
            right_layout.addWidget(self.tilemap_scroll)
            right_panel.setLayout(right_layout)

            main_layout.addWidget(left_panel, 0)
            main_layout.addWidget(right_panel, 1)

            # Palette data
            self.palettes = []  # List[List[Tuple[int, int, int]]]
            self.current_palette_index = 0
        except Exception as e:
            logging.error("Error initializing UI", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error initializing UI: {str(e)}")

    def load_tileset(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, 'Load Sprite', '', 'Image Files (*.png *.jpg *.bmp)')
            if file_path:
                self.recolorer.load_tileset(file_path)
                img_array = np.array(self.recolorer.tileset)
                self.tilemap_view.set_tileset(img_array)
                palette = self.recolorer.extract_palette()
                self.palettes = [palette]
                self.current_palette_index = 0
                self.update_palette_combo()
                self.update_palette_buttons()
        except Exception as e:
            logging.error("Error loading sprite", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error loading sprite: {str(e)}")

    def save_tileset(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, 'Save Sprite', '', 'PNG Files (*.png)')
            if file_path:
                img = Image.fromarray(self.tilemap_view.tileset_img)
                img.save(file_path)
        except Exception as e:
            logging.error("Error saving sprite", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving sprite: {str(e)}")

    def update_palette_combo(self):
        self.palette_combo.blockSignals(True)
        self.palette_combo.clear()
        for i in range(len(self.palettes)):
            self.palette_combo.addItem(f"Palette {i+1}")
        self.palette_combo.setCurrentIndex(self.current_palette_index)
        self.palette_combo.blockSignals(False)

    def add_new_palette(self):
        # Yeni palet: ilk paletin renklerinin kopyasıyla başlasın
        if self.palettes:
            new_palette = list(self.palettes[self.current_palette_index])
        else:
            new_palette = []
        self.palettes.append(new_palette)
        self.current_palette_index = len(self.palettes) - 1
        self.update_palette_combo()
        self.update_palette_buttons()

    def on_palette_changed(self, idx):
        if 0 <= idx < len(self.palettes):
            self.current_palette_index = idx
            self.update_palette_buttons()

    def update_palette_buttons(self):
        # Remove old buttons
        for i in reversed(range(self.palette_grid.count())):
            widget = self.palette_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        # Yatayda mevcut renkler (tek satır)
        palette = self.palettes[self.current_palette_index] if self.palettes else []
        for i, color in enumerate(palette):
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); border: 1px solid black;")
            btn.clicked.connect(lambda _, c=color: self.select_palette_color(c))
            self.palette_grid.addWidget(btn, 0, i)
        # Dikeyde boş kutular (örnek: 4 adet)
        empty_slots = 4
        for j in range(empty_slots):
            empty_btn = QPushButton("+")
            empty_btn.setFixedSize(24, 24)
            empty_btn.setStyleSheet("background-color: #eee; border: 1px dashed #888;")
            empty_btn.clicked.connect(lambda _, idx=j: self.add_new_palette_color())
            self.palette_grid.addWidget(empty_btn, j + 1, 0)
        if palette:
            self.select_palette_color(palette[0])

    def add_new_palette_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            rgb = (color.red(), color.green(), color.blue())
            if self.palettes:
                self.palettes[self.current_palette_index].append(rgb)
                self.update_palette_buttons()

    def select_palette_color(self, color):
        self.current_palette_color = color
        self.tilemap_view.set_selected_color(color)

    def update_tileset_from_grid(self, img_array):
        # Anında güncelleme için (ileride başka görsel alanlar eklenirse buradan yapılabilir)
        pass

    def undo(self):
        self.tilemap_view.undo()

def main():
    try:
        logging.info("Starting application")
        app = QApplication(sys.argv)
        gui = TilesetRecolorGUI()
        gui.show()
        logging.info("Application started successfully")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical("Application crashed", exc_info=True)
        QMessageBox.critical(None, "Fatal Error", f"Application crashed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 