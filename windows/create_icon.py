#!/usr/bin/env python3
"""Generate the application icon for Windows"""
from PIL import Image, ImageDraw

def create_icon():
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', size, color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        margin = size[0] // 8
        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill=(60, 60, 60, 255))
        
        inner_margin = size[0] // 4
        draw.ellipse([inner_margin, inner_margin, size[0]-inner_margin, size[1]-inner_margin], fill=(255, 255, 255, 255))
        
        images.append(img)
    
    images[0].save('monitor_icon.ico', format='ICO', sizes=[(s[0], s[1]) for s in sizes], append_images=images[1:])
    print("Created monitor_icon.ico")

if __name__ == "__main__":
    create_icon()
