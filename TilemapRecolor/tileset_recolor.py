from PIL import Image
import numpy as np

class TilesetRecolor:
    def __init__(self):
        self.tileset = None

    def load_tileset(self, file_path):
        self.tileset = Image.open(file_path).convert('RGB')

    def extract_palette(self):
        if not self.tileset:
            return []
        # Convert image to numpy array and get unique colors
        img_array = np.array(self.tileset)
        unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
        return [tuple(color) for color in unique_colors]

    def create_color_mapping(self, original_palette, new_palette):
        return dict(zip(original_palette, new_palette))

    def recolor_tileset(self, color_mapping):
        if not self.tileset:
            return None
        img_array = np.array(self.tileset)
        recolored = img_array.copy()
        for old_color, new_color in color_mapping.items():
            mask = np.all(img_array == old_color, axis=-1)
            recolored[mask] = new_color
        return Image.fromarray(recolored)

    def save_palette_as_image(self, palette, file_path):
        if not palette:
            return
        # Create a 1xN image with the palette colors
        palette_img = Image.new('RGB', (len(palette), 1))
        palette_img.putdata(palette)
        palette_img.save(file_path)

    def save_recolored_tileset(self, recolored_tileset, file_path):
        if recolored_tileset:
            recolored_tileset.save(file_path) 