#!/usr/bin/env python3
"""
Generate sample backgrounds and character templates for the animation library.
"""
import os
import sys
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from django.core.files.base import ContentFile
from animator.models import Background, CharacterTemplate


# ============================================================================
# BACKGROUND GENERATION
# ============================================================================

def create_gradient_background(width, height, color1, color2, direction='vertical'):
    """Create a gradient background"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    for i in range(height if direction == 'vertical' else width):
        ratio = i / (height if direction == 'vertical' else width)
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)

        if direction == 'vertical':
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))

    return img


def add_simple_elements(img, element_type='circles'):
    """Add decorative elements to background"""
    draw = ImageDraw.Draw(img)
    width, height = img.size

    if element_type == 'circles':
        # Soft circles
        for _ in range(5):
            x = int(width * (0.1 + 0.8 * (hash(str(_)) % 100) / 100))
            y = int(height * (0.1 + 0.8 * (hash(str(_ + 100)) % 100) / 100))
            r = 30 + hash(str(_ + 200)) % 70
            color = (255, 255, 255, 40)
            # Draw soft circle
            for radius in range(r, 0, -5):
                alpha = int(40 * (radius / r))
                draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                             outline=(255, 255, 255))

    elif element_type == 'stars':
        # Simple stars
        for i in range(15):
            x = int(width * ((hash(str(i)) % 100) / 100))
            y = int(height * 0.6 * ((hash(str(i + 50)) % 100) / 100))
            size = 2 + (hash(str(i + 100)) % 4)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(255, 255, 255))

    elif element_type == 'clouds':
        # Simple cloud shapes
        cloud_color = (255, 255, 255)
        for i in range(3):
            x = int(width * (0.2 + 0.6 * i / 3))
            y = int(height * (0.1 + 0.15 * (i % 2)))
            # Draw overlapping circles for cloud
            for dx, dy, r in [(0, 0, 40), (30, 5, 35), (60, 0, 40), (90, 5, 35), (120, 0, 30)]:
                draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=cloud_color)

    return img


def generate_sky_background():
    """Generate a blue sky with clouds"""
    img = create_gradient_background(1920, 1080, (135, 206, 235), (70, 130, 180))
    img = add_simple_elements(img, 'clouds')
    return img, "Blue Sky with Clouds", "A serene blue sky with fluffy white clouds"


def generate_sunset_background():
    """Generate a sunset gradient"""
    img = create_gradient_background(1920, 1080, (255, 183, 77), (255, 94, 77))
    # Add sun
    draw = ImageDraw.Draw(img)
    sun_x, sun_y = 960, 800
    for r in range(120, 0, -2):
        alpha = int(255 * (r / 120))
        color = (255, min(255, 200 + int(55 * (1 - r/120))), int(100 * (1 - r/120)))
        draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=color)
    return img, "Sunset", "A warm orange and red sunset gradient"


def generate_night_background():
    """Generate a starry night sky"""
    img = create_gradient_background(1920, 1080, (25, 25, 112), (0, 0, 30))
    img = add_simple_elements(img, 'stars')
    # Add moon
    draw = ImageDraw.Draw(img)
    moon_x, moon_y = 1500, 200
    draw.ellipse([moon_x - 60, moon_y - 60, moon_x + 60, moon_y + 60], fill=(240, 240, 220))
    # Moon shadow
    draw.ellipse([moon_x - 40, moon_y - 50, moon_x + 80, moon_y + 70], fill=(25, 25, 112))
    return img, "Starry Night", "A dark blue night sky with stars and crescent moon"


def generate_forest_background():
    """Generate a simple forest scene"""
    img = create_gradient_background(1920, 1080, (144, 238, 144), (34, 139, 34))
    draw = ImageDraw.Draw(img)

    # Ground
    draw.rectangle([0, 800, 1920, 1080], fill=(34, 100, 34))

    # Simple trees
    tree_color = (34, 80, 34)
    trunk_color = (101, 67, 33)
    for i in range(8):
        x = 100 + i * 230
        # Trunk
        draw.rectangle([x - 15, 600, x + 15, 800], fill=trunk_color)
        # Triangle tree top
        draw.polygon([(x, 400), (x - 100, 650), (x + 100, 650)], fill=tree_color)
        draw.polygon([(x, 300), (x - 80, 500), (x + 80, 500)], fill=tree_color)

    return img, "Forest", "A green forest scene with trees"


def generate_ocean_background():
    """Generate an ocean scene"""
    # Sky
    img = create_gradient_background(1920, 1080, (135, 206, 235), (100, 149, 237))
    draw = ImageDraw.Draw(img)

    # Ocean
    draw.rectangle([0, 500, 1920, 1080], fill=(0, 105, 148))

    # Waves
    wave_color = (65, 150, 190)
    for y in range(520, 1080, 60):
        for x in range(0, 1920, 40):
            wave_offset = int(math.sin(x / 80) * 10)
            draw.arc([x, y + wave_offset, x + 40, y + 30 + wave_offset], 0, 180, fill=wave_color, width=3)

    return img, "Ocean", "A calm ocean scene with gentle waves"


def generate_city_background():
    """Generate a simple city skyline"""
    img = create_gradient_background(1920, 1080, (255, 200, 150), (100, 80, 120))
    draw = ImageDraw.Draw(img)

    # Buildings
    building_colors = [(60, 60, 70), (50, 50, 60), (70, 70, 80), (55, 55, 65)]
    positions = [
        (100, 500, 200, 100), (250, 400, 150, 80), (380, 350, 180, 120),
        (520, 450, 160, 90), (660, 300, 200, 140), (850, 400, 170, 100),
        (1000, 350, 190, 130), (1180, 450, 150, 85), (1320, 380, 200, 110),
        (1500, 320, 180, 120), (1680, 400, 160, 100), (1820, 450, 100, 80)
    ]

    for i, (x, y, w, h) in enumerate(positions):
        color = building_colors[i % len(building_colors)]
        draw.rectangle([x, y, x + w, 1080], fill=color)
        # Windows
        window_color = (255, 255, 200)
        for wy in range(y + 20, 1000, 50):
            for wx in range(x + 15, x + w - 15, 30):
                if hash(str(wx + wy)) % 3 != 0:  # Some windows are dark
                    draw.rectangle([wx, wy, wx + 15, wy + 25], fill=window_color)

    return img, "City Skyline", "An urban city skyline at dusk"


def generate_abstract_background():
    """Generate an abstract colorful background"""
    img = Image.new('RGB', (1920, 1080), (240, 240, 245))
    draw = ImageDraw.Draw(img)

    # Colorful shapes
    colors = [(255, 99, 71), (65, 105, 225), (50, 205, 50), (255, 215, 0), (238, 130, 238)]
    for i in range(20):
        x = (hash(str(i)) % 1920)
        y = (hash(str(i + 100)) % 1080)
        r = 50 + (hash(str(i + 200)) % 150)
        color = colors[i % len(colors)]
        # Draw with transparency effect
        for radius in range(r, 0, -10):
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=color)

    return img, "Abstract Shapes", "A modern abstract background with colorful shapes"


def generate_studio_background():
    """Generate a clean studio/photography backdrop"""
    img = create_gradient_background(1920, 1080, (245, 245, 245), (200, 200, 200), 'vertical')

    # Add subtle vignette effect
    draw = ImageDraw.Draw(img)

    return img, "Studio Backdrop", "A clean white/gray gradient backdrop for portraits"


# ============================================================================
# CHARACTER TEMPLATE GENERATION
# ============================================================================

def draw_stick_figure(draw, center_x, center_y, scale=1.0, color=(59, 130, 246)):
    """Draw a simple stick figure"""
    head_y = center_y - 60 * scale
    shoulder_y = center_y - 35 * scale
    hip_y = center_y + 15 * scale
    hand_y = shoulder_y + 40 * scale
    foot_y = center_y + 80 * scale

    # Head
    head_radius = int(18 * scale)
    draw.ellipse([center_x - head_radius, head_y - head_radius,
                  center_x + head_radius, head_y + head_radius],
                 fill=color, outline=color)

    # Body
    draw.line([center_x, head_y + head_radius, center_x, hip_y], fill=color, width=int(4 * scale))

    # Arms
    draw.line([center_x, shoulder_y, center_x - 35 * scale, hand_y], fill=color, width=int(4 * scale))
    draw.line([center_x, shoulder_y, center_x + 35 * scale, hand_y], fill=color, width=int(4 * scale))

    # Legs
    draw.line([center_x, hip_y, center_x - 25 * scale, foot_y], fill=color, width=int(4 * scale))
    draw.line([center_x, hip_y, center_x + 25 * scale, foot_y], fill=color, width=int(4 * scale))


def draw_simple_robot(draw, center_x, center_y, scale=1.0):
    """Draw a simple robot character"""
    color = (100, 100, 110)
    accent = (59, 130, 246)

    # Head (rectangle)
    head_top = center_y - 65 * scale
    head_bottom = center_y - 30 * scale
    head_width = 40 * scale
    draw.rectangle([center_x - head_width, head_top, center_x + head_width, head_bottom], fill=color)

    # Eyes
    eye_y = head_top + 15 * scale
    draw.ellipse([center_x - 25 * scale, eye_y - 8, center_x - 10 * scale, eye_y + 8], fill=accent)
    draw.ellipse([center_x + 10 * scale, eye_y - 8, center_x + 25 * scale, eye_y + 8], fill=accent)

    # Antenna
    draw.line([center_x, head_top, center_x, head_top - 15 * scale], fill=color, width=3)
    draw.ellipse([center_x - 5, head_top - 20 * scale, center_x + 5, head_top - 10 * scale], fill=accent)

    # Body (rectangle)
    body_top = head_bottom + 5 * scale
    body_bottom = center_y + 30 * scale
    body_width = 35 * scale
    draw.rectangle([center_x - body_width, body_top, center_x + body_width, body_bottom], fill=color)

    # Arms
    arm_y = body_top + 15 * scale
    draw.rectangle([center_x - body_width - 25 * scale, arm_y, center_x - body_width, arm_y + 40 * scale], fill=color)
    draw.rectangle([center_x + body_width, arm_y, center_x + body_width + 25 * scale, arm_y + 40 * scale], fill=color)

    # Legs
    leg_width = 12 * scale
    leg_top = body_bottom + 5 * scale
    leg_bottom = center_y + 80 * scale
    draw.rectangle([center_x - 20 * scale - leg_width, leg_top, center_x - 20 * scale + leg_width, leg_bottom], fill=color)
    draw.rectangle([center_x + 20 * scale - leg_width, leg_top, center_x + 20 * scale + leg_width, leg_bottom], fill=color)


def draw_simple_animal(draw, center_x, center_y, animal_type='cat', scale=1.0):
    """Draw a simple animal character"""
    color = (139, 119, 101)  # Brown
    if animal_type == 'cat':
        color = (255, 165, 0)  # Orange
    elif animal_type == 'dog':
        color = (139, 90, 43)  # Brown

    # Body (oval)
    body_width = 50 * scale
    body_height = 35 * scale
    body_y = center_y + 10 * scale
    draw.ellipse([center_x - body_width, body_y - body_height,
                  center_x + body_width, body_y + body_height], fill=color)

    # Head (circle)
    head_x = center_x - 30 * scale
    head_y = center_y - 20 * scale
    head_r = 30 * scale
    draw.ellipse([head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r], fill=color)

    # Ears (triangles)
    if animal_type == 'cat':
        draw.polygon([
            (head_x - 20 * scale, head_y - 25 * scale),
            (head_x - 30 * scale, head_y - 50 * scale),
            (head_x - 5 * scale, head_y - 30 * scale)
        ], fill=color)
        draw.polygon([
            (head_x + 5 * scale, head_y - 30 * scale),
            (head_x + 15 * scale, head_y - 50 * scale),
            (head_x + 25 * scale, head_y - 25 * scale)
        ], fill=color)
    else:  # dog - floppy ears
        draw.ellipse([head_x - 35 * scale, head_y - 10 * scale,
                      head_x - 15 * scale, head_y + 30 * scale], fill=color)
        draw.ellipse([head_x + 15 * scale, head_y - 10 * scale,
                      head_x + 35 * scale, head_y + 30 * scale], fill=color)

    # Eyes
    eye_color = (50, 50, 50)
    draw.ellipse([head_x - 15 * scale, head_y - 10 * scale,
                  head_x - 5 * scale, head_y], fill=eye_color)
    draw.ellipse([head_x + 5 * scale, head_y - 10 * scale,
                  head_x + 15 * scale, head_y], fill=eye_color)

    # Nose
    draw.ellipse([head_x - 5 * scale, head_y + 5 * scale,
                  head_x + 5 * scale, head_y + 12 * scale], fill=(50, 50, 50))

    # Legs
    leg_color = color
    legs = [
        (center_x - 35 * scale, body_y + body_height),
        (center_x - 15 * scale, body_y + body_height),
        (center_x + 15 * scale, body_y + body_height),
        (center_x + 35 * scale, body_y + body_height),
    ]
    for lx, ly in legs:
        draw.rectangle([lx - 8, ly, lx + 8, ly + 25 * scale], fill=leg_color)

    # Tail
    tail_start = (center_x + body_width - 10, body_y)
    if animal_type == 'cat':
        draw.arc([tail_start[0], tail_start[1] - 30 * scale,
                  tail_start[0] + 40 * scale, tail_start[1] + 10 * scale],
                 180, 90, fill=color, width=int(8 * scale))
    else:
        draw.arc([tail_start[0], tail_start[1] - 20 * scale,
                  tail_start[0] + 30 * scale, tail_start[1]],
                 200, 60, fill=color, width=int(10 * scale))


def create_character_template(char_type='stick_figure'):
    """Create a character template preview image"""
    img = Image.new('RGBA', (400, 500), (248, 249, 250, 255))
    draw = ImageDraw.Draw(img)

    center_x, center_y = 200, 250

    if char_type == 'stick_figure':
        draw_stick_figure(draw, center_x, center_y, scale=1.5, color=(59, 130, 246))
        name = "Basic Stick Figure"
        desc = "Simple stick figure with articulated joints. Great for quick animations and prototyping."
        char_type_db = 'humanoid'
    elif char_type == 'robot':
        draw_simple_robot(draw, center_x, center_y, scale=1.5)
        name = "Robot"
        desc = "Blocky robot character with mechanical joints. Perfect for sci-fi animations."
        char_type_db = 'humanoid'
    elif char_type == 'cat':
        draw_simple_animal(draw, center_x, center_y, 'cat', scale=1.5)
        name = "Cat"
        desc = "Cute cartoon cat with flexible body. Great for playful animations."
        char_type_db = 'quadruped'
    elif char_type == 'dog':
        draw_simple_animal(draw, center_x, center_y, 'dog', scale=1.5)
        name = "Dog"
        desc = "Friendly cartoon dog. Ideal for pet-themed animations."
        char_type_db = 'quadruped'
    elif char_type == 'stick_advanced':
        draw_stick_figure(draw, center_x, center_y, scale=1.5, color=(220, 53, 69))
        name = "Advanced Stick Figure"
        desc = "Enhanced stick figure with more joint points for complex animations."
        char_type_db = 'humanoid'
    else:
        draw_stick_figure(draw, center_x, center_y, scale=1.5)
        name = "Character"
        desc = "Generic character template"
        char_type_db = 'humanoid'

    return img, name, desc, char_type_db


def save_image_to_file(img, format='PNG'):
    """Save PIL image to bytes"""
    output = BytesIO()
    img.save(output, format=format)
    output.seek(0)
    return output.getvalue()


def generate_backgrounds():
    """Generate and save sample backgrounds"""
    print("=== Generating Sample Backgrounds ===")

    generators = [
        generate_sky_background,
        generate_sunset_background,
        generate_night_background,
        generate_forest_background,
        generate_ocean_background,
        generate_city_background,
        generate_abstract_background,
        generate_studio_background,
    ]

    for gen_func in generators:
        img, name, desc = gen_func()

        # Check if already exists
        if Background.objects.filter(name=name, is_system=True).exists():
            print(f"  Skipping {name} (already exists)")
            continue

        # Save background
        bg = Background(
            name=name,
            is_system=True,
            is_ai_generated=False,
        )

        img_data = save_image_to_file(img, 'JPEG')
        filename = f"{name.lower().replace(' ', '_')}.jpg"
        bg.image.save(filename, ContentFile(img_data), save=True)

        print(f"  Created: {name}")

    print("Done generating backgrounds.")


def generate_templates():
    """Generate and save character templates"""
    print("\n=== Generating Character Templates ===")

    templates = [
        ('stick_figure', 'Humans'),
        ('stick_advanced', 'Humans'),
        ('robot', 'Sci-Fi'),
        ('cat', 'Animals'),
        ('dog', 'Animals'),
    ]

    for char_type, category in templates:
        img, name, desc, type_db = create_character_template(char_type)

        # Check if already exists
        if CharacterTemplate.objects.filter(name=name).exists():
            print(f"  Skipping {name} (already exists)")
            continue

        # Save template
        template = CharacterTemplate(
            name=name,
            description=desc,
            category=category,
            character_type=type_db,
            is_premium=char_type in ['stick_advanced'],  # Advanced is premium
        )

        img_data = save_image_to_file(img, 'PNG')
        filename = f"{name.lower().replace(' ', '_')}.png"
        template.image.save(filename, ContentFile(img_data), save=True)

        print(f"  Created: {name} (category={category}, premium={template.is_premium})")

    print("Done generating templates.")


if __name__ == '__main__':
    generate_backgrounds()
    generate_templates()
    print("\n=== All sample content generated! ===")
