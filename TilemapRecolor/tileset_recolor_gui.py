import sys
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QColorDialog, QScrollArea, QGridLayout, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt
from PIL import Image
import numpy as np
from tileset_recolor import TilesetRecolor

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

class TilesetRecolorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recolorer = TilesetRecolor()
        self.color_buttons = []
        self.original_palette = []
        self.init_ui()

    def init_ui(self):
        try:
            logging.info("Initializing UI")
            self.setWindowTitle('Tileset Recolor Tool')
            self.setGeometry(100, 100, 1200, 800)

            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QHBoxLayout(central_widget)

            # Left panel for controls
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            
            # Load tileset button
            load_btn = QPushButton('Load Tileset')
            load_btn.clicked.connect(self.load_tileset)
            left_layout.addWidget(load_btn)

            # Save palette button
            save_palette_btn = QPushButton('Save Palette')
            save_palette_btn.clicked.connect(self.save_palette)
            left_layout.addWidget(save_palette_btn)

            # Save tileset button
            save_tileset_btn = QPushButton('Save Recolored Tileset')
            save_tileset_btn.clicked.connect(self.save_tileset)
            left_layout.addWidget(save_tileset_btn)

            # Color palette area
            self.palette_scroll = QScrollArea()
            self.palette_widget = QWidget()
            self.palette_layout = QGridLayout(self.palette_widget)
            self.palette_scroll.setWidget(self.palette_widget)
            self.palette_scroll.setWidgetResizable(True)
            left_layout.addWidget(self.palette_scroll)

            # Right panel for preview
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            
            # Original tileset preview
            self.original_label = QLabel('Original Tileset')
            self.original_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(self.original_label)
            
            # Recolored tileset preview
            self.recolored_label = QLabel('Recolored Tileset')
            self.recolored_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(self.recolored_label)

            # Add panels to main layout
            main_layout.addWidget(left_panel, 1)
            main_layout.addWidget(right_panel, 2)
            logging.info("UI initialization completed")
        except Exception as e:
            logging.error("Error initializing UI", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error initializing UI: {str(e)}")

    def load_tileset(self):
        try:
            logging.info("Opening file dialog for tileset")
            file_path, _ = QFileDialog.getOpenFileName(self, 'Load Tileset', '', 'Image Files (*.png *.jpg *.bmp)')
            if file_path:
                logging.info(f"Loading tileset from: {file_path}")
                # Load image directly with QImage first
                qimage = QImage(file_path)
                if qimage.isNull():
                    raise Exception("Failed to load image")
                
                # Convert to PIL Image for processing
                self.recolorer.load_tileset(file_path)
                
                logging.info("Extracting palette from tileset")
                self.original_palette = self.recolorer.extract_palette()
                logging.info(f"Found {len(self.original_palette)} colors in palette")
                
                if not self.original_palette:
                    logging.warning("No colors found in the tileset")
                    QMessageBox.warning(self, "Warning", "No colors found in the tileset!")
                    return
                
                # Set the original image preview
                self.original_label.setPixmap(QPixmap.fromImage(qimage).scaled(400, 400, Qt.KeepAspectRatio))
                
                logging.info("Updating palette buttons")
                self.update_palette_buttons()
                logging.info("Updating previews")
                self.update_preview()
        except Exception as e:
            logging.error("Error loading tileset", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error loading tileset: {str(e)}")

    def update_palette_buttons(self):
        try:
            logging.info("Updating palette buttons")
            # Clear existing buttons
            for button in self.color_buttons:
                button.deleteLater()
            self.color_buttons.clear()

            # Create new buttons
            for i, color in enumerate(self.original_palette):
                button = ColorButton(color, self)
                self.palette_layout.addWidget(button, i // 4, i % 4)
                self.color_buttons.append(button)
            logging.info(f"Created {len(self.color_buttons)} color buttons")
        except Exception as e:
            logging.error("Error updating palette buttons", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error updating palette buttons: {str(e)}")

    def update_preview(self):
        try:
            if self.recolorer.tileset and self.color_buttons:
                logging.info("Creating color mapping")
                # Create color mapping from current button colors
                new_palette = [button.color for button in self.color_buttons]
                color_mapping = self.recolorer.create_color_mapping(self.original_palette, new_palette)
                
                logging.info("Recoloring tileset")
                # Recolor tileset
                recolored = self.recolorer.recolor_tileset(color_mapping)
                
                logging.info("Converting recolored tileset to pixmap")
                # Convert PIL image to QImage
                img_array = np.array(recolored)
                height, width, channel = img_array.shape
                bytes_per_line = 3 * width
                qim = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
                # Show recolored tileset
                self.recolored_label.setPixmap(QPixmap.fromImage(qim).scaled(400, 400, Qt.KeepAspectRatio))
        except Exception as e:
            logging.error("Error updating preview", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error updating preview: {str(e)}")

    def save_palette(self):
        try:
            if not self.color_buttons:
                logging.warning("No palette to save")
                QMessageBox.warning(self, "Warning", "No palette to save!")
                return
                
            logging.info("Opening save dialog for palette")
            file_path, _ = QFileDialog.getSaveFileName(self, 'Save Palette', '', 'PNG Files (*.png)')
            if file_path:
                logging.info(f"Saving palette to: {file_path}")
                new_palette = [button.color for button in self.color_buttons]
                self.recolorer.save_palette_as_image(new_palette, file_path)
                logging.info("Palette saved successfully")
                QMessageBox.information(self, "Success", "Palette saved successfully!")
        except Exception as e:
            logging.error("Error saving palette", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving palette: {str(e)}")

    def save_tileset(self):
        try:
            if not self.recolorer.tileset:
                logging.warning("No tileset loaded")
                QMessageBox.warning(self, "Warning", "No tileset loaded!")
                return
                
            logging.info("Opening save dialog for tileset")
            file_path, _ = QFileDialog.getSaveFileName(self, 'Save Tileset', '', 'PNG Files (*.png)')
            if file_path:
                logging.info(f"Saving tileset to: {file_path}")
                new_palette = [button.color for button in self.color_buttons]
                color_mapping = self.recolorer.create_color_mapping(self.original_palette, new_palette)
                recolored = self.recolorer.recolor_tileset(color_mapping)
                self.recolorer.save_recolored_tileset(recolored, file_path)
                logging.info("Tileset saved successfully")
                QMessageBox.information(self, "Success", "Tileset saved successfully!")
        except Exception as e:
            logging.error("Error saving tileset", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving tileset: {str(e)}")

    @staticmethod
    def pil2pixmap(pil_image):
        try:
            logging.debug("Converting PIL image to QPixmap")
            # Convert PIL image to numpy array
            img_array = np.array(pil_image)
            height, width, channel = img_array.shape
            bytes_per_line = 3 * width
            
            # Create QImage from numpy array
            qim = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
            return QPixmap.fromImage(qim)
        except Exception as e:
            logging.error(f"Error converting image: {str(e)}", exc_info=True)
            raise Exception(f"Error converting image: {str(e)}")

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