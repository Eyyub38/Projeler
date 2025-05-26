from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QTextEdit,
                             QPushButton, QMessageBox, QListWidget, QListWidgetItem,
                             QScrollArea, QWidget, QGroupBox, QFileDialog, QMenu,
                             QSlider, QToolButton, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QAction, QIcon
from database_manager import Pokemon, Move, Item, BaseStats, Evolution, DataType
import os
import shutil
from PIL import Image
import io

class ImagePreview(QLabel):
    def __init__(self, parent=None, preview_size=96):
        super().__init__(parent)
        self.preview_size = preview_size
        self.setMinimumSize(preview_size, preview_size)
        self.setMaximumSize(preview_size, preview_size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            QLabel:hover {
                border: 1px solid #666;
                background-color: #e8e8e8;
            }
        """)
        self.setText("No Image")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # For animated GIFs
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_frame)
        self.current_frame = 0
        self.frames = []
        self.frame_durations = []
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Image manipulation
        self.original_image = None
        self.current_image = None
        self.zoom_level = 1.0
        self.rotation = 0
    
    def set_image(self, image_path):
        """Sets the image from a file path, handling both static and animated images."""
        if not image_path or not os.path.exists(image_path):
            self.clear_image()
            return
        
        try:
            # Reset animation state
            self.animation_timer.stop()
            self.frames.clear()
            self.frame_durations.clear()
            self.current_frame = 0
            
            # Load image with PIL for better format support
            with Image.open(image_path) as img:
                self.original_image = img.copy()
                
                # Handle animated GIFs
                if getattr(img, "is_animated", False):
                    self.frames = []
                    self.frame_durations = []
                    
                    for frame_idx in range(img.n_frames):
                        img.seek(frame_idx)
                        frame = img.convert("RGBA")
                        self.frames.append(frame)
                        self.frame_durations.append(img.info.get('duration', 100))
                    
                    # Start animation
                    self.animation_timer.start(self.frame_durations[0])
                    self.update_frame()
                else:
                    # Static image
                    self.current_image = img.convert("RGBA")
                    self.update_preview()
        
        except Exception as e:
            QMessageBox.warning(self.parent(), "Image Error", f"Failed to load image: {str(e)}")
            self.clear_image()
    
    def clear_image(self):
        """Clears the current image and resets all states."""
        self.animation_timer.stop()
        self.frames.clear()
        self.frame_durations.clear()
        self.current_frame = 0
        self.original_image = None
        self.current_image = None
        self.zoom_level = 1.0
        self.rotation = 0
        self.setText("No Image")
        self.setPixmap(QPixmap())
    
    def next_frame(self):
        """Advances to the next frame in an animated image."""
        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.update_frame()
            self.animation_timer.start(self.frame_durations[self.current_frame])
    
    def update_frame(self):
        """Updates the current frame display."""
        if self.frames:
            self.current_image = self.frames[self.current_frame]
            self.update_preview()
    
    def update_preview(self):
        """Updates the preview with the current image state."""
        if self.current_image:
            # Apply transformations
            img = self.current_image.copy()
            if self.rotation:
                img = img.rotate(self.rotation, expand=True)
            
            # Calculate size maintaining aspect ratio
            width, height = img.size
            scale = min(self.preview_size / width, self.preview_size / height) * self.zoom_level
            new_size = (int(width * scale), int(height * scale))
            
            # Resize image
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to QPixmap and display
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            self.setPixmap(pixmap)
    
    def show_context_menu(self, pos):
        """Shows the context menu for image manipulation."""
        if not self.original_image:
            return
        
        menu = QMenu(self)
        
        # Zoom actions
        zoom_menu = menu.addMenu("Zoom")
        zoom_in = zoom_menu.addAction("Zoom In")
        zoom_out = zoom_menu.addAction("Zoom Out")
        zoom_reset = zoom_menu.addAction("Reset Zoom")
        
        # Rotation actions
        rotate_menu = menu.addMenu("Rotate")
        rotate_left = rotate_menu.addAction("Rotate Left")
        rotate_right = rotate_menu.addAction("Rotate Right")
        rotate_reset = rotate_menu.addAction("Reset Rotation")
        
        # Other actions
        menu.addSeparator()
        clear_action = menu.addAction("Clear Image")
        
        # Show menu and handle action
        action = menu.exec(self.mapToGlobal(pos))
        
        if action == zoom_in:
            self.zoom_level = min(2.0, self.zoom_level + 0.1)
            self.update_preview()
        elif action == zoom_out:
            self.zoom_level = max(0.1, self.zoom_level - 0.1)
            self.update_preview()
        elif action == zoom_reset:
            self.zoom_level = 1.0
            self.update_preview()
        elif action == rotate_left:
            self.rotation = (self.rotation - 90) % 360
            self.update_preview()
        elif action == rotate_right:
            self.rotation = (self.rotation + 90) % 360
            self.update_preview()
        elif action == rotate_reset:
            self.rotation = 0
            self.update_preview()
        elif action == clear_action:
            self.clear_image()
            if hasattr(self.parent(), 'clear_sprite'):
                self.parent().clear_sprite(self)

class SpriteGroup(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preview size control
        size_layout = QHBoxLayout()
        size_label = QLabel("Preview Size:")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(64, 256)
        self.size_slider.setValue(96)
        self.size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.size_slider.setTickInterval(32)
        self.size_slider.valueChanged.connect(self.update_preview_sizes)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider)
        layout.addLayout(size_layout)
        
        # Grid for previews
        self.preview_layout = QHBoxLayout()
        layout.addLayout(self.preview_layout)
    
    def update_preview_sizes(self, size):
        """Updates the size of all preview widgets."""
        for i in range(self.preview_layout.count()):
            widget = self.preview_layout.itemAt(i).widget()
            if isinstance(widget, ImagePreview):
                widget.preview_size = size
                widget.setMinimumSize(size, size)
                widget.setMaximumSize(size, size)
                widget.update_preview()

class PokemonDialog(QDialog):
    def __init__(self, db_manager, pokemon_id=None):
        super().__init__()
        self.db = db_manager
        self.pokemon_id = pokemon_id
        self.sprite_paths = {
            'front': None,
            'back': None,
            'icon': None
        }
        self.init_ui()
        if pokemon_id:
            self.load_pokemon_data()
    
    def init_ui(self):
        self.setWindowTitle("Add/Edit Pokemon")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create widget to hold all content
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(basic_group)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setToolTip("Enter the Pokemon's name (letters, numbers, and spaces only)")
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(20)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)
        
        # Types (Multiple)
        types_label = QLabel("Types:")
        types_label.setToolTip("Select one or two types for the Pokemon")
        self.types_list = QListWidget()
        self.types_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.types_list.setMaximumHeight(100)
        self.types_list.addItems([
            "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
            "Fighting", "Poison", "Ground", "Flying", "Psychic",
            "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
        ])
        basic_layout.addWidget(types_label)
        basic_layout.addWidget(self.types_list)
        
        layout.addWidget(basic_group)
        
        # Replace the old Sprites Group with the new SpriteGroup
        self.sprites_group = SpriteGroup("Sprites")
        sprites_layout = self.sprites_group.preview_layout
        
        # Front Sprite
        front_layout = QVBoxLayout()
        front_label = QLabel("Front Sprite:")
        front_label.setToolTip("Front-facing sprite of the Pokemon")
        self.front_preview = ImagePreview(self, self.sprites_group.size_slider.value())
        self.front_preview.setToolTip("Click to change front sprite\nRight-click for more options")
        self.front_preview.mousePressEvent = lambda e: self.select_sprite('front')
        front_layout.addWidget(front_label)
        front_layout.addWidget(self.front_preview)
        sprites_layout.addLayout(front_layout)
        
        # Back Sprite
        back_layout = QVBoxLayout()
        back_label = QLabel("Back Sprite:")
        back_label.setToolTip("Back-facing sprite of the Pokemon")
        self.back_preview = ImagePreview(self, self.sprites_group.size_slider.value())
        self.back_preview.setToolTip("Click to change back sprite\nRight-click for more options")
        self.back_preview.mousePressEvent = lambda e: self.select_sprite('back')
        back_layout.addWidget(back_label)
        back_layout.addWidget(self.back_preview)
        sprites_layout.addLayout(back_layout)
        
        # Icon Sprite
        icon_layout = QVBoxLayout()
        icon_label = QLabel("Icon:")
        icon_label.setToolTip("Small icon sprite of the Pokemon")
        self.icon_preview = ImagePreview(self, self.sprites_group.size_slider.value())
        self.icon_preview.setToolTip("Click to change icon sprite\nRight-click for more options")
        self.icon_preview.mousePressEvent = lambda e: self.select_sprite('icon')
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_preview)
        sprites_layout.addLayout(icon_layout)
        
        layout.addWidget(self.sprites_group)
        
        # Stats Group
        stats_group = QGroupBox("Base Stats")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_info = QLabel("Base stats determine the Pokemon's battle performance")
        stats_info.setWordWrap(True)
        stats_layout.addWidget(stats_info)
        
        stats_grid = QHBoxLayout()
        
        # HP
        hp_layout = QVBoxLayout()
        hp_label = QLabel("HP:")
        hp_label.setToolTip("Base HP stat (1-255)")
        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 255)
        hp_layout.addWidget(hp_label)
        hp_layout.addWidget(self.hp_spin)
        stats_grid.addLayout(hp_layout)
        
        # Attack
        attack_layout = QVBoxLayout()
        attack_label = QLabel("Attack:")
        attack_label.setToolTip("Base Attack stat (1-255)")
        self.attack_spin = QSpinBox()
        self.attack_spin.setRange(1, 255)
        attack_layout.addWidget(attack_label)
        attack_layout.addWidget(self.attack_spin)
        stats_grid.addLayout(attack_layout)
        
        # Defense
        defense_layout = QVBoxLayout()
        defense_label = QLabel("Defense:")
        defense_label.setToolTip("Base Defense stat (1-255)")
        self.defense_spin = QSpinBox()
        self.defense_spin.setRange(1, 255)
        defense_layout.addWidget(defense_label)
        defense_layout.addWidget(self.defense_spin)
        stats_grid.addLayout(defense_layout)
        
        # Sp. Attack
        sp_attack_layout = QVBoxLayout()
        sp_attack_label = QLabel("Sp. Attack:")
        sp_attack_label.setToolTip("Base Special Attack stat (1-255)")
        self.sp_attack_spin = QSpinBox()
        self.sp_attack_spin.setRange(1, 255)
        sp_attack_layout.addWidget(sp_attack_label)
        sp_attack_layout.addWidget(self.sp_attack_spin)
        stats_grid.addLayout(sp_attack_layout)
        
        # Sp. Defense
        sp_defense_layout = QVBoxLayout()
        sp_defense_label = QLabel("Sp. Defense:")
        sp_defense_label.setToolTip("Base Special Defense stat (1-255)")
        self.sp_defense_spin = QSpinBox()
        self.sp_defense_spin.setRange(1, 255)
        sp_defense_layout.addWidget(sp_defense_label)
        sp_defense_layout.addWidget(self.sp_defense_spin)
        stats_grid.addLayout(sp_defense_layout)
        
        # Speed
        speed_layout = QVBoxLayout()
        speed_label = QLabel("Speed:")
        speed_label.setToolTip("Base Speed stat (1-255)")
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 255)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_spin)
        stats_grid.addLayout(speed_layout)
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_group)
        
        # Moves Group
        moves_group = QGroupBox("Moves")
        moves_layout = QVBoxLayout(moves_group)
        
        moves_info = QLabel("Select moves that this Pokemon can learn")
        moves_info.setWordWrap(True)
        moves_layout.addWidget(moves_info)
        
        self.moves_list = QListWidget()
        self.moves_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.moves_list.setMaximumHeight(150)
        # Load available moves from database
        moves = self.db.get_all_entries(DataType.MOVE)
        self.moves_list.addItems([move['name'] for move in moves])
        moves_layout.addWidget(self.moves_list)
        
        layout.addWidget(moves_group)
        
        # Evolutions Group
        evolutions_group = QGroupBox("Evolutions")
        evolutions_layout = QVBoxLayout(evolutions_group)
        
        evolutions_info = QLabel("Add evolution paths for this Pokemon")
        evolutions_info.setWordWrap(True)
        evolutions_layout.addWidget(evolutions_info)
        
        self.evolutions_list = QListWidget()
        self.evolutions_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.evolutions_list.setMaximumHeight(100)
        evolutions_layout.addWidget(self.evolutions_list)
        
        evolution_input_layout = QHBoxLayout()
        self.evolution_combo = QComboBox()
        self.evolution_combo.setEditable(True)
        self.evolution_combo.setToolTip("Enter the name of the evolved form")
        
        self.evolution_level = QSpinBox()
        self.evolution_level.setRange(1, 100)
        self.evolution_level.setToolTip("Level required for evolution")
        
        self.evolution_condition = QLineEdit()
        self.evolution_condition.setPlaceholderText("Evolution condition (optional)")
        self.evolution_condition.setToolTip("Special condition for evolution (e.g., 'Fire Stone', 'Friendship')")
        
        add_evolution_btn = QPushButton("Add Evolution")
        add_evolution_btn.setToolTip("Add a new evolution path")
        add_evolution_btn.clicked.connect(self.add_evolution)
        
        remove_evolution_btn = QPushButton("Remove Evolution")
        remove_evolution_btn.setToolTip("Remove selected evolution(s)")
        remove_evolution_btn.clicked.connect(self.remove_evolution)
        
        evolution_input_layout.addWidget(self.evolution_combo)
        evolution_input_layout.addWidget(QLabel("Level:"))
        evolution_input_layout.addWidget(self.evolution_level)
        evolution_input_layout.addWidget(self.evolution_condition)
        evolution_input_layout.addWidget(add_evolution_btn)
        evolution_input_layout.addWidget(remove_evolution_btn)
        
        evolutions_layout.addLayout(evolution_input_layout)
        layout.addWidget(evolutions_group)
        
        # Additional Information Group
        additional_group = QGroupBox("Additional Information")
        additional_layout = QVBoxLayout(additional_group)
        
        # Forms
        forms_label = QLabel("Forms:")
        forms_label.setToolTip("Select available forms for this Pokemon")
        self.forms_list = QListWidget()
        self.forms_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.forms_list.setMaximumHeight(100)
        self.forms_list.addItems(["Normal", "Mega", "Alolan", "Galarian", "Hisuian", "Gigantamax"])
        additional_layout.addWidget(forms_label)
        additional_layout.addWidget(self.forms_list)
        
        # Egg Groups
        egg_groups_label = QLabel("Egg Groups:")
        egg_groups_label.setToolTip("Select egg groups for breeding compatibility")
        self.egg_groups_list = QListWidget()
        self.egg_groups_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.egg_groups_list.setMaximumHeight(100)
        self.egg_groups_list.addItems([
            "Monster", "Water 1", "Bug", "Flying", "Field", "Fairy",
            "Grass", "Human-Like", "Water 3", "Mineral", "Amorphous",
            "Water 2", "Ditto", "Dragon", "Undiscovered"
        ])
        additional_layout.addWidget(egg_groups_label)
        additional_layout.addWidget(self.egg_groups_list)
        
        # Additional Stats
        stats_info = QLabel("Additional battle-related stats")
        stats_info.setWordWrap(True)
        additional_layout.addWidget(stats_info)
        
        stats_layout = QHBoxLayout()
        
        self.xp_yield_spin = QSpinBox()
        self.xp_yield_spin.setRange(0, 1000)
        self.xp_yield_spin.setToolTip("Experience points gained when defeating this Pokemon")
        xp_label = QLabel("XP Yield:")
        stats_layout.addWidget(xp_label)
        stats_layout.addWidget(self.xp_yield_spin)
        
        self.catch_rate_spin = QSpinBox()
        self.catch_rate_spin.setRange(0, 255)
        self.catch_rate_spin.setToolTip("Base catch rate (higher = easier to catch)")
        catch_label = QLabel("Catch Rate:")
        stats_layout.addWidget(catch_label)
        stats_layout.addWidget(self.catch_rate_spin)
        
        additional_layout.addLayout(stats_layout)
        
        # Gender Ratio
        gender_label = QLabel("Gender Ratio:")
        gender_label.setToolTip("Gender distribution of this Pokemon species")
        self.gender_ratio_combo = QComboBox()
        self.gender_ratio_combo.addItems([
            "Always Male",
            "87.5% Male, 12.5% Female",
            "75% Male, 25% Female",
            "50% Male, 50% Female",
            "25% Male, 75% Female",
            "12.5% Male, 87.5% Female",
            "Always Female",
            "Genderless"
        ])
        additional_layout.addWidget(gender_label)
        additional_layout.addWidget(self.gender_ratio_combo)
        
        # Abilities
        abilities_label = QLabel("Abilities:")
        abilities_label.setToolTip("Select abilities this Pokemon can have")
        self.abilities_list = QListWidget()
        self.abilities_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.abilities_list.setMaximumHeight(100)
        self.abilities_list.addItems([
            "Overgrow", "Blaze", "Torrent", "Static", "Intimidate",
            "Levitate", "Swift Swim", "Water Absorb", "Volt Absorb",
            "Flash Fire", "Thick Fat", "Natural Cure", "Synchronize"
        ])
        additional_layout.addWidget(abilities_label)
        additional_layout.addWidget(self.abilities_list)
        
        # Physical Characteristics
        physical_label = QLabel("Physical Characteristics:")
        physical_label.setToolTip("Height and weight of this Pokemon")
        additional_layout.addWidget(physical_label)
        
        physical_layout = QHBoxLayout()
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(0, 100)
        self.height_spin.setSingleStep(0.1)
        self.height_spin.setToolTip("Height in meters")
        height_label = QLabel("Height (m):")
        physical_layout.addWidget(height_label)
        physical_layout.addWidget(self.height_spin)
        
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(0, 1000)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setToolTip("Weight in kilograms")
        weight_label = QLabel("Weight (kg):")
        physical_layout.addWidget(weight_label)
        physical_layout.addWidget(self.weight_spin)
        
        additional_layout.addLayout(physical_layout)
        layout.addWidget(additional_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save Pokemon data")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and close")
        save_btn.clicked.connect(self.save_pokemon)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Set the scroll area's widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def clear_sprite(self, preview_widget):
        """Clears a sprite and its associated path."""
        if preview_widget == self.front_preview:
            self.sprite_paths['front'] = None
        elif preview_widget == self.back_preview:
            self.sprite_paths['back'] = None
        elif preview_widget == self.icon_preview:
            self.sprite_paths['icon'] = None
    
    def select_sprite(self, sprite_type):
        """Opens a file dialog to select a sprite image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {sprite_type.title()} Sprite",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        
        if file_path:
            try:
                # Create sprites directory if it doesn't exist
                sprites_dir = os.path.join("data", "sprites", "pokemon")
                os.makedirs(sprites_dir, exist_ok=True)
                
                # Generate unique filename
                base_name = f"{self.pokemon_id if self.pokemon_id else 'new'}_{sprite_type}"
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
                    ext = '.png'  # Default to PNG if extension is not supported
                new_path = os.path.join(sprites_dir, f"{base_name}{ext}")
                
                # Copy the file
                shutil.copy2(file_path, new_path)
                
                # Update preview and path
                self.sprite_paths[sprite_type] = new_path
                if sprite_type == 'front':
                    self.front_preview.set_image(new_path)
                elif sprite_type == 'back':
                    self.back_preview.set_image(new_path)
                elif sprite_type == 'icon':
                    self.icon_preview.set_image(new_path)
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save sprite: {str(e)}")
    
    def validate_pokemon_data(self) -> tuple[bool, str]:
        """Validates Pokemon data before saving."""
        # Name validation
        name = self.name_edit.text().strip()
        if not name:
            return False, "Name cannot be empty"
        if not name.replace(" ", "").isalnum():
            return False, "Name can only contain letters, numbers, and spaces"
        
        # Type validation
        types = [item.text() for item in self.types_list.selectedItems()]
        if not types:
            return False, "At least one type must be selected"
        if len(types) > 2:
            return False, "A Pokemon can have at most two types"
        
        # Stats validation
        stats = [
            self.hp_spin.value(),
            self.attack_spin.value(),
            self.defense_spin.value(),
            self.sp_attack_spin.value(),
            self.sp_defense_spin.value(),
            self.speed_spin.value()
        ]
        if any(stat < 1 or stat > 255 for stat in stats):
            return False, "All stats must be between 1 and 255"
        
        # Evolution validation
        evolutions = []
        for i in range(self.evolutions_list.count()):
            item = self.evolutions_list.item(i)
            evolution_data = item.data(Qt.ItemDataRole.UserRole)
            if evolution_data['next_form'] == name:
                return False, "A Pokemon cannot evolve into itself"
            evolutions.append(evolution_data['next_form'])
        
        if len(set(evolutions)) != len(evolutions):
            return False, "Duplicate evolution paths are not allowed"
        
        # Egg group validation
        egg_groups = [item.text() for item in self.egg_groups_list.selectedItems()]
        if not egg_groups:
            return False, "At least one egg group must be selected"
        
        # Ability validation
        abilities = [item.text() for item in self.abilities_list.selectedItems()]
        if not abilities:
            return False, "At least one ability must be selected"
        
        # Sprite validation
        if not self.sprite_paths['front']:
            return False, "Front sprite is required"
        if not self.sprite_paths['back']:
            return False, "Back sprite is required"
        if not self.sprite_paths['icon']:
            return False, "Icon sprite is required"
        
        return True, ""
    
    def save_pokemon(self):
        """Saves Pokemon data with validation."""
        # Validate data
        is_valid, error_message = self.validate_pokemon_data()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_message)
            return
        
        try:
            # Get selected types
            types = [item.text() for item in self.types_list.selectedItems()]
            
            # Get selected moves
            moves = [item.text() for item in self.moves_list.selectedItems()]
            
            # Get evolutions
            evolutions = []
            for i in range(self.evolutions_list.count()):
                item = self.evolutions_list.item(i)
                evolution_data = item.data(Qt.ItemDataRole.UserRole)
                evolutions.append(Evolution(
                    next_form=evolution_data['next_form'],
                    level=evolution_data['level'],
                    condition=evolution_data['condition']
                ))
            
            # Get selected forms
            forms = [item.text() for item in self.forms_list.selectedItems()]
            
            # Get selected egg groups
            egg_groups = [item.text() for item in self.egg_groups_list.selectedItems()]
            
            # Get selected abilities
            abilities = [item.text() for item in self.abilities_list.selectedItems()]
            
            base_stats = BaseStats(
                hp=self.hp_spin.value(),
                attack=self.attack_spin.value(),
                defense=self.defense_spin.value(),
                sp_attack=self.sp_attack_spin.value(),
                sp_defense=self.sp_defense_spin.value(),
                speed=self.speed_spin.value()
            )
            
            pokemon = Pokemon(
                id=self.pokemon_id if self.pokemon_id else self.db.get_next_id(DataType.POKEMON),
                name=self.name_edit.text().strip(),
                type=types,
                base_stats=base_stats,
                moves=moves,
                evolutions=evolutions,
                forms=forms,
                egg_groups=egg_groups,
                xp_yield=self.xp_yield_spin.value(),
                catch_rate=self.catch_rate_spin.value(),
                gender_ratio=self.gender_ratio_combo.currentText(),
                abilities=abilities,
                height=self.height_spin.value(),
                weight=self.weight_spin.value(),
                sprites=self.sprite_paths  # Add sprites to Pokemon data
            )
            
            if self.pokemon_id:
                self.db.update_entry(DataType.POKEMON, self.pokemon_id, pokemon)
            else:
                self.db.add_entry(DataType.POKEMON, pokemon)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Pokemon: {str(e)}")
    
    def add_evolution(self):
        """Adds a new evolution to the list."""
        next_form = self.evolution_combo.currentText()
        level = self.evolution_level.value()
        condition = self.evolution_condition.text()
        
        if next_form:
            evolution_text = f"{next_form} (Lv.{level})"
            if condition:
                evolution_text += f" - {condition}"
            
            item = QListWidgetItem(evolution_text)
            item.setData(Qt.ItemDataRole.UserRole, {
                'next_form': next_form,
                'level': level,
                'condition': condition
            })
            self.evolutions_list.addItem(item)
            
            # Clear inputs
            self.evolution_combo.setCurrentText("")
            self.evolution_level.setValue(1)
            self.evolution_condition.clear()
    
    def remove_evolution(self):
        """Removes selected evolution(s) from the list."""
        for item in self.evolutions_list.selectedItems():
            self.evolutions_list.takeItem(self.evolutions_list.row(item))
    
    def load_pokemon_data(self):
        """Loads existing Pokemon data."""
        pokemon = self.db.get_entry(DataType.POKEMON, self.pokemon_id)
        if pokemon:
            self.name_edit.setText(pokemon['name'])
            
            # Types
            for type_name in pokemon['type']:
                items = self.types_list.findItems(type_name, Qt.MatchFlag.MatchExactly)
                for item in items:
                    item.setSelected(True)
            
            # Base Stats
            self.hp_spin.setValue(pokemon['base_stats']['hp'])
            self.attack_spin.setValue(pokemon['base_stats']['attack'])
            self.defense_spin.setValue(pokemon['base_stats']['defense'])
            self.sp_attack_spin.setValue(pokemon['base_stats']['sp_attack'])
            self.sp_defense_spin.setValue(pokemon['base_stats']['sp_defense'])
            self.speed_spin.setValue(pokemon['base_stats']['speed'])
            
            # Moves
            for move in pokemon['moves']:
                items = self.moves_list.findItems(move, Qt.MatchFlag.MatchExactly)
                for item in items:
                    item.setSelected(True)
            
            # Evolutions
            for evolution in pokemon['evolutions']:
                evolution_text = f"{evolution['next_form']} (Lv.{evolution['level']})"
                if evolution['condition']:
                    evolution_text += f" - {evolution['condition']}"
                
                item = QListWidgetItem(evolution_text)
                item.setData(Qt.ItemDataRole.UserRole, evolution)
                self.evolutions_list.addItem(item)
            
            # Forms
            for form in pokemon['forms']:
                items = self.forms_list.findItems(form, Qt.MatchFlag.MatchExactly)
                for item in items:
                    item.setSelected(True)
            
            # Egg Groups
            for group in pokemon['egg_groups']:
                items = self.egg_groups_list.findItems(group, Qt.MatchFlag.MatchExactly)
                for item in items:
                    item.setSelected(True)
            
            # Additional Stats
            self.xp_yield_spin.setValue(pokemon['xp_yield'])
            self.catch_rate_spin.setValue(pokemon['catch_rate'])
            
            # Gender Ratio
            self.gender_ratio_combo.setCurrentText(pokemon['gender_ratio'])
            
            # Abilities
            for ability in pokemon['abilities']:
                items = self.abilities_list.findItems(ability, Qt.MatchFlag.MatchExactly)
                for item in items:
                    item.setSelected(True)
            
            # Physical Characteristics
            self.height_spin.setValue(pokemon['height'])
            self.weight_spin.setValue(pokemon['weight'])
            
            # Load sprites
            if 'sprites' in pokemon:
                self.sprite_paths = pokemon['sprites']
                self.front_preview.set_image(self.sprite_paths['front'])
                self.back_preview.set_image(self.sprite_paths['back'])
                self.icon_preview.set_image(self.sprite_paths['icon'])

class MoveDialog(QDialog):
    def __init__(self, db_manager, move_id=None):
        super().__init__()
        self.db = db_manager
        self.move_id = move_id
        self.init_ui()
        if move_id:
            self.load_move_data()
    
    def init_ui(self):
        self.setWindowTitle("Add/Edit Move")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create widget to hold all content
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(basic_group)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setToolTip("Enter the move's name (letters, numbers, and spaces only)")
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(20)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)
        
        # Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setToolTip("Select the move's type")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
            "Fighting", "Poison", "Ground", "Flying", "Psychic",
            "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        basic_layout.addLayout(type_layout)
        
        layout.addWidget(basic_group)
        
        # Battle Stats Group
        stats_group = QGroupBox("Battle Stats")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_info = QLabel("Stats that determine the move's effectiveness in battle")
        stats_info.setWordWrap(True)
        stats_layout.addWidget(stats_info)
        
        stats_grid = QHBoxLayout()
        
        # Power
        power_layout = QVBoxLayout()
        power_label = QLabel("Power:")
        power_label.setToolTip("Base power of the move (0-255, 0 for status moves)")
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 255)
        power_layout.addWidget(power_label)
        power_layout.addWidget(self.power_spin)
        stats_grid.addLayout(power_layout)
        
        # Accuracy
        accuracy_layout = QVBoxLayout()
        accuracy_label = QLabel("Accuracy:")
        accuracy_label.setToolTip("Base accuracy of the move (0-100, 0 for moves that never miss)")
        self.accuracy_spin = QSpinBox()
        self.accuracy_spin.setRange(0, 100)
        accuracy_layout.addWidget(accuracy_label)
        accuracy_layout.addWidget(self.accuracy_spin)
        stats_grid.addLayout(accuracy_layout)
        
        # PP
        pp_layout = QVBoxLayout()
        pp_label = QLabel("PP:")
        pp_label.setToolTip("Power Points - number of times the move can be used (1-64)")
        self.pp_spin = QSpinBox()
        self.pp_spin.setRange(1, 64)
        pp_layout.addWidget(pp_label)
        pp_layout.addWidget(self.pp_spin)
        stats_grid.addLayout(pp_layout)
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_group)
        
        # Category Group
        category_group = QGroupBox("Move Category")
        category_layout = QVBoxLayout(category_group)
        
        category_info = QLabel("The category determines how the move's damage is calculated")
        category_info.setWordWrap(True)
        category_layout.addWidget(category_info)
        
        category_combo_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setToolTip("Physical: uses Attack/Defense\nSpecial: uses Sp. Attack/Sp. Defense\nStatus: no damage")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Physical", "Special", "Status"])
        self.category_combo.currentTextChanged.connect(self.update_power_visibility)
        category_combo_layout.addWidget(category_label)
        category_combo_layout.addWidget(self.category_combo)
        category_layout.addLayout(category_combo_layout)
        
        layout.addWidget(category_group)
        
        # Description Group
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        desc_info = QLabel("Describe what the move does in battle")
        desc_info.setWordWrap(True)
        desc_layout.addWidget(desc_info)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Enter a detailed description of the move's effects...")
        self.desc_edit.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_edit)
        
        layout.addWidget(desc_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save move data")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and close")
        save_btn.clicked.connect(self.save_move)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Set the scroll area's widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Initialize power visibility
        self.update_power_visibility()
    
    def update_power_visibility(self):
        """Updates the visibility of the power spinbox based on the category."""
        is_status = self.category_combo.currentText() == "Status"
        self.power_spin.setEnabled(not is_status)
        if is_status:
            self.power_spin.setValue(0)
    
    def validate_move_data(self) -> tuple[bool, str]:
        """Validates move data before saving."""
        # Name validation
        name = self.name_edit.text().strip()
        if not name:
            return False, "Name cannot be empty"
        if not name.replace(" ", "").isalnum():
            return False, "Name can only contain letters, numbers, and spaces"
        
        # Description validation
        description = self.desc_edit.toPlainText().strip()
        if not description:
            return False, "Description cannot be empty"
        
        # Category-specific validation
        category = self.category_combo.currentText()
        if category == "Status" and self.power_spin.value() != 0:
            return False, "Status moves must have 0 power"
        elif category != "Status" and self.power_spin.value() == 0:
            return False, "Non-status moves must have power greater than 0"
        
        return True, ""
    
    def load_move_data(self):
        """Loads existing move data."""
        move = self.db.get_entry(DataType.MOVE, self.move_id)
        if move:
            self.name_edit.setText(move['name'])
            self.type_combo.setCurrentText(move['type'])
            self.power_spin.setValue(move['power'])
            self.accuracy_spin.setValue(move['accuracy'])
            self.pp_spin.setValue(move['pp'])
            self.category_combo.setCurrentText(move['category'])
            self.desc_edit.setText(move['description'])
    
    def save_move(self):
        """Saves move data with validation."""
        # Validate data
        is_valid, error_message = self.validate_move_data()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_message)
            return
        
        try:
            move = Move(
                id=self.move_id if self.move_id else self.db.get_next_id(DataType.MOVE),
                name=self.name_edit.text().strip(),
                type=self.type_combo.currentText(),
                power=self.power_spin.value(),
                accuracy=self.accuracy_spin.value(),
                pp=self.pp_spin.value(),
                category=self.category_combo.currentText(),
                description=self.desc_edit.toPlainText().strip()
            )
            
            if self.move_id:
                self.db.update_entry(DataType.MOVE, self.move_id, move)
            else:
                self.db.add_entry(DataType.MOVE, move)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Move: {str(e)}")

class ItemDialog(QDialog):
    def __init__(self, db_manager, item_id=None):
        super().__init__()
        self.db = db_manager
        self.item_id = item_id
        self.icon_path = None
        self.init_ui()
        if item_id:
            self.load_item_data()
    
    def init_ui(self):
        self.setWindowTitle("Add/Edit Item")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create widget to hold all content
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(basic_group)
        
        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setToolTip("Enter the item's name (letters, numbers, and spaces only)")
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(30)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setToolTip("Select the item's category")
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Medicine", "Poke Ball", "Battle Item", "Hold Item",
            "Evolution Item", "TM/HM", "Berry", "Key Item", "Other"
        ])
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        basic_layout.addLayout(category_layout)
        
        layout.addWidget(basic_group)
        
        # Replace the old Icon Group with the new SpriteGroup
        self.icon_group = SpriteGroup("Item Icon")
        icon_layout = self.icon_group.preview_layout
        
        # Icon Preview
        icon_preview_layout = QVBoxLayout()
        icon_label = QLabel("Icon:")
        icon_label.setToolTip("Icon sprite of the item")
        self.icon_preview = ImagePreview(self, self.icon_group.size_slider.value())
        self.icon_preview.setToolTip("Click to change icon sprite\nRight-click for more options")
        self.icon_preview.mousePressEvent = lambda e: self.select_icon()
        icon_preview_layout.addWidget(icon_label)
        icon_preview_layout.addWidget(self.icon_preview)
        icon_layout.addLayout(icon_preview_layout)
        
        layout.addWidget(self.icon_group)
        
        # Effects Group
        effects_group = QGroupBox("Effects")
        effects_layout = QVBoxLayout(effects_group)
        
        effects_info = QLabel("Describe what the item does when used")
        effects_info.setWordWrap(True)
        effects_layout.addWidget(effects_info)
        
        self.effects_edit = QTextEdit()
        self.effects_edit.setPlaceholderText("Enter a detailed description of the item's effects...")
        self.effects_edit.setMaximumHeight(100)
        effects_layout.addWidget(self.effects_edit)
        
        layout.addWidget(effects_group)
        
        # Usage Restrictions Group
        restrictions_group = QGroupBox("Usage Restrictions")
        restrictions_layout = QVBoxLayout(restrictions_group)
        
        restrictions_info = QLabel("Set when and how the item can be used")
        restrictions_info.setWordWrap(True)
        restrictions_layout.addWidget(restrictions_info)
        
        # Battle Usage
        battle_layout = QHBoxLayout()
        battle_label = QLabel("Battle Usage:")
        battle_label.setToolTip("Can this item be used during battle?")
        self.battle_combo = QComboBox()
        self.battle_combo.addItems(["Always", "Outside Battle Only", "Never"])
        battle_layout.addWidget(battle_label)
        battle_layout.addWidget(self.battle_combo)
        restrictions_layout.addLayout(battle_layout)
        
        # Hold Effect
        hold_layout = QHBoxLayout()
        hold_label = QLabel("Hold Effect:")
        hold_label.setToolTip("What happens when a Pokémon holds this item?")
        self.hold_edit = QLineEdit()
        self.hold_edit.setPlaceholderText("Enter hold effect (if any)...")
        hold_layout.addWidget(hold_label)
        hold_layout.addWidget(self.hold_edit)
        restrictions_layout.addLayout(hold_layout)
        
        # Target
        target_layout = QHBoxLayout()
        target_label = QLabel("Target:")
        target_label.setToolTip("Who can use this item?")
        self.target_combo = QComboBox()
        self.target_combo.addItems([
            "Any Pokémon", "Your Pokémon Only", "Opponent's Pokémon Only",
            "Wild Pokémon Only", "Trainer Only", "No Target"
        ])
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        restrictions_layout.addLayout(target_layout)
        
        layout.addWidget(restrictions_group)
        
        # Value Group
        value_group = QGroupBox("Value")
        value_layout = QVBoxLayout(value_group)
        
        value_info = QLabel("Set the item's monetary value and rarity")
        value_info.setWordWrap(True)
        value_layout.addWidget(value_info)
        
        value_grid = QHBoxLayout()
        
        # Price
        price_layout = QVBoxLayout()
        price_label = QLabel("Price:")
        price_label.setToolTip("How much the item costs in Poké Dollars (0 for priceless items)")
        self.price_spin = QSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setSingleStep(100)
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_spin)
        value_grid.addLayout(price_layout)
        
        # Rarity
        rarity_layout = QVBoxLayout()
        rarity_label = QLabel("Rarity:")
        rarity_label.setToolTip("How common or rare the item is")
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(["Common", "Uncommon", "Rare", "Very Rare", "Legendary"])
        rarity_layout.addWidget(rarity_label)
        rarity_layout.addWidget(self.rarity_combo)
        value_grid.addLayout(rarity_layout)
        
        value_layout.addLayout(value_grid)
        layout.addWidget(value_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save item data")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Discard changes and close")
        save_btn.clicked.connect(self.save_item)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Set the scroll area's widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def clear_sprite(self, preview_widget):
        """Clears the icon and its associated path."""
        if preview_widget == self.icon_preview:
            self.icon_path = None
    
    def select_icon(self):
        """Opens a file dialog to select an item icon."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Item Icon",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        
        if file_path:
            try:
                # Create sprites directory if it doesn't exist
                sprites_dir = os.path.join("data", "sprites", "items")
                os.makedirs(sprites_dir, exist_ok=True)
                
                # Generate unique filename
                base_name = f"{self.item_id if self.item_id else 'new'}_icon"
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
                    ext = '.png'  # Default to PNG if extension is not supported
                new_path = os.path.join(sprites_dir, f"{base_name}{ext}")
                
                # Copy the file
                shutil.copy2(file_path, new_path)
                
                # Update preview and path
                self.icon_path = new_path
                self.icon_preview.set_image(new_path)
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save icon: {str(e)}")
    
    def validate_item_data(self) -> tuple[bool, str]:
        """Validates item data before saving."""
        # Name validation
        name = self.name_edit.text().strip()
        if not name:
            return False, "Name cannot be empty"
        if not name.replace(" ", "").isalnum():
            return False, "Name can only contain letters, numbers, and spaces"
        
        # Effects validation
        effects = self.effects_edit.toPlainText().strip()
        if not effects:
            return False, "Effects description cannot be empty"
        
        # Category-specific validation
        category = self.category_combo.currentText()
        if category == "Medicine" and self.battle_combo.currentText() == "Never":
            return False, "Medicine items must be usable in battle"
        elif category == "Key Item" and self.price_spin.value() > 0:
            return False, "Key items cannot have a price"
        
        # Icon validation
        if not self.icon_path:
            return False, "Item icon is required"
        
        return True, ""
    
    def load_item_data(self):
        """Loads existing item data."""
        item = self.db.get_entry(DataType.ITEM, self.item_id)
        if item:
            self.name_edit.setText(item['name'])
            self.category_combo.setCurrentText(item['category'])
            self.effects_edit.setText(item['effects'])
            self.battle_combo.setCurrentText(item['battle_usage'])
            self.hold_edit.setText(item['hold_effect'])
            self.target_combo.setCurrentText(item['target'])
            self.price_spin.setValue(item['price'])
            self.rarity_combo.setCurrentText(item['rarity'])
            
            # Load icon
            if 'icon' in item:
                self.icon_path = item['icon']
                self.icon_preview.set_image(self.icon_path)
    
    def save_item(self):
        """Saves item data with validation."""
        # Validate data
        is_valid, error_message = self.validate_item_data()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_message)
            return
        
        try:
            item = Item(
                id=self.item_id if self.item_id else self.db.get_next_id(DataType.ITEM),
                name=self.name_edit.text().strip(),
                category=self.category_combo.currentText(),
                effects=self.effects_edit.toPlainText().strip(),
                battle_usage=self.battle_combo.currentText(),
                hold_effect=self.hold_edit.text().strip(),
                target=self.target_combo.currentText(),
                price=self.price_spin.value(),
                rarity=self.rarity_combo.currentText(),
                icon=self.icon_path  # Add icon to Item data
            )
            
            if self.item_id:
                self.db.update_entry(DataType.ITEM, self.item_id, item)
            else:
                self.db.add_entry(DataType.ITEM, item)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Item: {str(e)}") 