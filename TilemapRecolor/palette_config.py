from dataclasses import dataclass
from typing import List, Dict, Tuple
import json

@dataclass
class ColorPalette:
    name: str
    colors: List[Tuple[int, int, int]]  # RGB colors

@dataclass
class SpriteSection:
    name: str
    x: int
    y: int
    width: int
    height: int
    palettes: List[ColorPalette]

class SpritePaletteConfig:
    def __init__(self):
        self.sections: Dict[str, SpriteSection] = {}
    
    def add_section(self, name: str, x: int, y: int, width: int, height: int):
        """Add a new section to the sprite configuration"""
        self.sections[name] = SpriteSection(name, x, y, width, height, [])
    
    def add_palette_to_section(self, section_name: str, palette_name: str, colors: List[Tuple[int, int, int]]):
        """Add a color palette to a specific section"""
        if section_name not in self.sections:
            raise ValueError(f"Section {section_name} does not exist")
        
        palette = ColorPalette(palette_name, colors)
        self.sections[section_name].palettes.append(palette)
    
    def save_to_file(self, filename: str):
        """Save the configuration to a JSON file"""
        config_data = {
            "sections": {
                name: {
                    "x": section.x,
                    "y": section.y,
                    "width": section.width,
                    "height": section.height,
                    "palettes": [
                        {
                            "name": palette.name,
                            "colors": palette.colors
                        }
                        for palette in section.palettes
                    ]
                }
                for name, section in self.sections.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'SpritePaletteConfig':
        """Load configuration from a JSON file"""
        with open(filename, 'r') as f:
            config_data = json.load(f)
        
        config = cls()
        for section_name, section_data in config_data["sections"].items():
            config.add_section(
                section_name,
                section_data["x"],
                section_data["y"],
                section_data["width"],
                section_data["height"]
            )
            
            for palette_data in section_data["palettes"]:
                config.add_palette_to_section(
                    section_name,
                    palette_data["name"],
                    [tuple(color) for color in palette_data["colors"]]
                )
        
        return config

# Example usage:
if __name__ == "__main__":
    # Create a sample configuration
    config = SpritePaletteConfig()
    
    # Add a section for the head
    config.add_section("head", 0, 0, 32, 32)
    config.add_palette_to_section("head", "normal", [(255, 200, 150), (200, 150, 100), (150, 100, 50)])
    config.add_palette_to_section("head", "dark", [(200, 150, 100), (150, 100, 50), (100, 50, 0)])
    
    # Add a section for the body
    config.add_section("body", 32, 0, 32, 48)
    config.add_palette_to_section("body", "normal", [(100, 150, 255), (50, 100, 200), (0, 50, 150)])
    config.add_palette_to_section("body", "dark", [(50, 100, 200), (0, 50, 150), (0, 0, 100)])
    
    # Save the configuration
    config.save_to_file("sprite_palettes.json") 