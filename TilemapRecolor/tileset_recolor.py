import logging
import numpy as np
from PIL import Image

class TilesetRecolor:
    def __init__(self):
        self.tileset = None

    def load_tileset(self, file_path):
        """Load a tileset image"""
        self.tileset = Image.open(file_path).convert('RGB')

    def extract_palette_from_image(self, image):
        """Extract unique colors from an image"""
        try:
            # Convert image to numpy array
            img_array = np.array(image)
            
            # Reshape to 2D array of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Get unique colors
            unique_colors = np.unique(pixels, axis=0)
            
            # Convert to list of tuples
            palette = [tuple(color) for color in unique_colors]
            
            # Sort colors by brightness (you can change this sorting if needed)
            palette.sort(key=lambda c: sum(c))
            
            return palette
        except Exception as e:
            logging.error(f"Error extracting palette: {str(e)}", exc_info=True)
            return []

    def extract_palette(self):
        """Extract unique colors from the tileset"""
        if not self.tileset:
            return []
        return self.extract_palette_from_image(self.tileset)

    def create_color_mapping(self, original_palette, new_palette):
        """Create a mapping from original colors to new colors"""
        if len(original_palette) != len(new_palette):
            raise ValueError("Original and new palettes must have the same number of colors")
        return dict(zip(original_palette, new_palette))

    def recolor_tileset(self, color_mapping):
        """Recolor the tileset using the color mapping"""
        if not self.tileset:
            raise ValueError("No tileset loaded")
        
        # Convert image to numpy array
        img_array = np.array(self.tileset)
        
        # Create a copy of the array
        recolored = img_array.copy()
        
        # Apply color mapping
        for old_color, new_color in color_mapping.items():
            mask = np.all(img_array == old_color, axis=-1)
            recolored[mask] = new_color
        
        return Image.fromarray(recolored)

    def save_recolored_tileset(self, recolored_image, file_path):
        """Save the recolored tileset"""
        recolored_image.save(file_path)

    def save_palette_as_image(self, palette, file_path):
        """Save a palette as an image"""
        if not palette:
            raise ValueError("Empty palette")
        
        # Create a palette image
        palette_width = len(palette) * 32
        palette_height = 32
        palette_image = Image.new('RGB', (palette_width, palette_height))
        
        # Draw color swatches
        for i, color in enumerate(palette):
            for x in range(32):
                for y in range(32):
                    palette_image.putpixel((i * 32 + x, y), color)
        
        palette_image.save(file_path) 