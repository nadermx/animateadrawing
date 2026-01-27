#!/usr/bin/env python3
"""
Generate demo assets for the examples page.
Creates original drawings and their animated versions.
"""
import os
import sys
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Output directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'demos')
SOURCES_DIR = os.path.join(STATIC_DIR, 'sources')
EXAMPLES_DIR = os.path.join(STATIC_DIR, 'examples')

# Colors
BG_COLOR = (248, 249, 250)
LINE_COLOR = (40, 40, 40)
BLUE = (59, 130, 246)


def ensure_dirs():
    """Create output directories"""
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(SOURCES_DIR, exist_ok=True)
    os.makedirs(EXAMPLES_DIR, exist_ok=True)
    print(f"Output directories created at {STATIC_DIR}")


# ============================================================================
# STICK FIGURE FUNCTIONS
# ============================================================================

def draw_stick_figure(draw, cx, cy, scale=1.0, rotation=0, arm_angle=0, leg_angle=0, color=LINE_COLOR):
    """Draw a properly proportioned stick figure with natural walking motion

    Proportions based on ~180px total height:
    - Head: ~20px diameter
    - Torso: ~40px (neck to hip)
    - Legs: ~75px each
    """
    # Apply rotation around center point
    cos_r = math.cos(math.radians(rotation))
    sin_r = math.sin(math.radians(rotation))

    def rotate(x, y):
        dx, dy = x - cx, y - cy
        nx = cx + (dx * cos_r - dy * sin_r)
        ny = cy + (dx * sin_r + dy * cos_r)
        return nx, ny

    # Figure proportions (relative to cy as hip center)
    # Total height ~170 pixels, centered on cy
    head_center_y = cy - 70 * scale  # Head center
    neck_y = cy - 55 * scale
    shoulder_y = cy - 50 * scale
    hip_y = cy - 5 * scale  # Hip joint
    foot_y = cy + 70 * scale  # Ground level

    line_width = max(3, int(4 * scale))
    head_r = 15 * scale

    # HEAD
    hx, hy = rotate(cx, head_center_y)
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)

    # TORSO (neck to hip)
    neck_pt = rotate(cx, neck_y)
    hip_pt = rotate(cx, hip_y)
    draw.line([neck_pt, hip_pt], fill=color, width=line_width)

    # ARMS - hang from shoulders, swing forward/back
    arm_len = 35 * scale
    shoulder_l = rotate(cx - 2 * scale, shoulder_y)
    shoulder_r = rotate(cx + 2 * scale, shoulder_y)

    # Left arm: swings forward when arm_angle > 0
    la_rad = math.radians(arm_angle * 0.8)  # Dampen arm swing
    left_hand = (
        shoulder_l[0] + math.sin(la_rad) * arm_len,
        shoulder_l[1] + math.cos(la_rad) * arm_len
    )
    draw.line([shoulder_l, left_hand], fill=color, width=line_width)

    # Right arm: swings opposite
    ra_rad = math.radians(-arm_angle * 0.8)
    right_hand = (
        shoulder_r[0] + math.sin(ra_rad) * arm_len,
        shoulder_r[1] + math.cos(ra_rad) * arm_len
    )
    draw.line([shoulder_r, right_hand], fill=color, width=line_width)

    # LEGS - start from hip, swing forward/back
    leg_len = 70 * scale
    hip_width = 10 * scale  # Distance between leg attachment points

    # Left hip and leg
    left_hip = rotate(cx - hip_width/2, hip_y)
    ll_rad = math.radians(leg_angle)
    left_foot = (
        left_hip[0] + math.sin(ll_rad) * leg_len,
        left_hip[1] + math.cos(ll_rad) * leg_len
    )
    draw.line([left_hip, left_foot], fill=color, width=line_width)

    # Right hip and leg (swings opposite)
    right_hip = rotate(cx + hip_width/2, hip_y)
    rl_rad = math.radians(-leg_angle)
    right_foot = (
        right_hip[0] + math.sin(rl_rad) * leg_len,
        right_hip[1] + math.cos(rl_rad) * leg_len
    )
    draw.line([right_hip, right_foot], fill=color, width=line_width)


def create_stick_figure_png(action='neutral'):
    """Create a static stick figure PNG"""
    img = Image.new('RGBA', (200, 250), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Add white background
    draw.rectangle([10, 10, 190, 240], fill=(255, 255, 255, 255))

    if action == 'walk':
        # Mid-stride pose - one leg forward, opposite arm forward
        draw_stick_figure(draw, 100, 130, scale=1.0, leg_angle=18, arm_angle=-20)
    elif action == 'wave':
        # Standing with arm up (we'll draw wave arm separately)
        draw_stick_figure(draw, 100, 130, scale=1.0)
        # Add raised waving arm
        shoulder = (102, 130 - 50)
        arm_len = 35
        hand_x = shoulder[0] + arm_len * math.sin(math.radians(-45))
        hand_y = shoulder[1] - arm_len * math.cos(math.radians(-45))
        draw.line([shoulder, (hand_x, hand_y)], fill=LINE_COLOR, width=4)
    elif action == 'dance':
        # Dynamic dance pose
        draw_stick_figure(draw, 100, 130, scale=1.0, rotation=8, arm_angle=35, leg_angle=15)
    else:
        draw_stick_figure(draw, 100, 130, scale=1.0)

    return img


def create_stick_walk_gif():
    """Create walking animation GIF - natural stride"""
    frames = []
    num_frames = 24

    for i in range(num_frames):
        img = Image.new('RGB', (200, 250), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Walking motion - moderate leg swing to avoid crossing
        leg_swing = math.sin(t) * 20  # Leg stride angle (degrees)
        arm_swing = -math.sin(t) * 25  # Arms swing opposite to legs

        # Subtle bounce on each step (highest when legs pass)
        bounce = abs(math.sin(t)) * 4

        draw_stick_figure(draw, 100, 130 - bounce, scale=1.0, arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)

    return frames


def create_stick_wave_gif():
    """Create waving animation GIF - one arm waves while standing"""
    frames = []
    num_frames = 24

    for i in range(num_frames):
        img = Image.new('RGB', (200, 250), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 3 * math.pi

        # Draw base figure standing still
        draw_stick_figure(draw, 100, 130, scale=1.0)

        # Waving arm - raised up and waving side to side
        shoulder_y = 130 - 50  # Match figure's shoulder
        shoulder = (102, shoulder_y)
        arm_len = 35

        # Arm goes up at angle, waves back and forth
        base_angle = -60  # Raised up
        wave = math.sin(t) * 30  # Side to side wave

        hand_x = shoulder[0] + arm_len * math.sin(math.radians(base_angle + wave))
        hand_y = shoulder[1] - arm_len * math.cos(math.radians(base_angle + wave))

        # Draw the waving arm (overwrites the default right arm)
        draw.line([shoulder, (hand_x, hand_y)], fill=LINE_COLOR, width=4)

        frames.append(img)

    return frames


def create_stick_dance_gif():
    """Create dancing animation GIF - energetic with body movement"""
    frames = []
    num_frames = 30

    for i in range(num_frames):
        img = Image.new('RGB', (200, 250), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 4 * math.pi

        # Dancing motion - side to side sway with bounce
        sway_x = math.sin(t) * 10
        bounce = abs(math.sin(t * 2)) * 8
        rotation = math.sin(t) * 10

        # Arms and legs move energetically
        arm_swing = math.sin(t * 1.5) * 40
        leg_swing = math.sin(t * 2) * 18

        draw_stick_figure(draw, 100 + sway_x, 130 - bounce, scale=1.0,
                         rotation=rotation, arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)

    return frames


# ============================================================================
# PUG DRAWING
# ============================================================================

def draw_pug(draw, cx, cy, scale=1.0, ear_angle=0, tongue_out=False):
    """Draw a cute pug face"""
    # Face circle
    face_r = 60 * scale
    draw.ellipse([cx - face_r, cy - face_r * 0.8, cx + face_r, cy + face_r * 0.9],
                 fill=(222, 184, 135), outline=LINE_COLOR, width=2)

    # Ears
    ear_w = 25 * scale
    ear_h = 35 * scale
    # Left ear
    left_ear_angle = -15 + ear_angle
    draw.ellipse([cx - face_r + 5, cy - face_r * 0.5 - ear_h * 0.5,
                  cx - face_r + 5 + ear_w, cy - face_r * 0.5 + ear_h * 0.5],
                 fill=(180, 140, 100), outline=LINE_COLOR, width=2)
    # Right ear
    draw.ellipse([cx + face_r - 5 - ear_w, cy - face_r * 0.5 - ear_h * 0.5,
                  cx + face_r - 5, cy - face_r * 0.5 + ear_h * 0.5],
                 fill=(180, 140, 100), outline=LINE_COLOR, width=2)

    # Snout
    snout_w = 40 * scale
    snout_h = 30 * scale
    draw.ellipse([cx - snout_w, cy + 5 * scale, cx + snout_w, cy + 5 * scale + snout_h],
                 fill=(180, 140, 100), outline=LINE_COLOR, width=2)

    # Nose
    nose_w = 15 * scale
    nose_h = 12 * scale
    draw.ellipse([cx - nose_w, cy + 8 * scale, cx + nose_w, cy + 8 * scale + nose_h],
                 fill=(40, 30, 30))

    # Eyes - big round pug eyes
    eye_r = 15 * scale
    eye_y = cy - 15 * scale
    eye_offset = 25 * scale
    # Left eye
    draw.ellipse([cx - eye_offset - eye_r, eye_y - eye_r,
                  cx - eye_offset + eye_r, eye_y + eye_r],
                 fill=(255, 255, 255), outline=LINE_COLOR, width=2)
    draw.ellipse([cx - eye_offset - eye_r * 0.6, eye_y - eye_r * 0.6,
                  cx - eye_offset + eye_r * 0.6, eye_y + eye_r * 0.6],
                 fill=(40, 30, 30))
    draw.ellipse([cx - eye_offset - eye_r * 0.2, eye_y - eye_r * 0.5,
                  cx - eye_offset + eye_r * 0.2, eye_y - eye_r * 0.1],
                 fill=(255, 255, 255))
    # Right eye
    draw.ellipse([cx + eye_offset - eye_r, eye_y - eye_r,
                  cx + eye_offset + eye_r, eye_y + eye_r],
                 fill=(255, 255, 255), outline=LINE_COLOR, width=2)
    draw.ellipse([cx + eye_offset - eye_r * 0.6, eye_y - eye_r * 0.6,
                  cx + eye_offset + eye_r * 0.6, eye_y + eye_r * 0.6],
                 fill=(40, 30, 30))
    draw.ellipse([cx + eye_offset - eye_r * 0.2, eye_y - eye_r * 0.5,
                  cx + eye_offset + eye_r * 0.2, eye_y - eye_r * 0.1],
                 fill=(255, 255, 255))

    # Tongue
    if tongue_out:
        draw.ellipse([cx - 8 * scale, cy + snout_h + 5 * scale,
                      cx + 8 * scale, cy + snout_h + 25 * scale],
                     fill=(255, 150, 150))


def create_pug_drawing():
    """Create pug original drawing"""
    img = Image.new('RGB', (300, 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw_pug(draw, 150, 150, scale=1.2)
    return img


def create_pug_gif():
    """Create pug wiggle animation"""
    frames = []
    num_frames = 20

    for i in range(num_frames):
        img = Image.new('RGB', (300, 300), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi
        ear_wiggle = math.sin(t * 2) * 5
        scale = 1.2 + math.sin(t) * 0.03
        tongue = i % 10 < 5

        draw_pug(draw, 150, 150, scale=scale, ear_angle=ear_wiggle, tongue_out=tongue)
        frames.append(img)

    return frames


# ============================================================================
# STILL LIFE DRAWING
# ============================================================================

def draw_still_life(draw, cx, cy, sway=0, scale=1.0):
    """Draw a still life with vase and fruit"""
    # Table line
    table_y = cy + 60 * scale
    draw.line([(cx - 100 * scale, table_y), (cx + 100 * scale, table_y)],
              fill=LINE_COLOR, width=2)

    # Vase
    vase_w = 30 * scale
    vase_h = 70 * scale
    vase_x = cx - 30 * scale + sway
    vase_y = table_y - vase_h

    # Vase body (curved lines)
    vase_points = [
        (vase_x - vase_w * 0.5, vase_y),
        (vase_x - vase_w * 0.7, vase_y + vase_h * 0.3),
        (vase_x - vase_w * 0.8, vase_y + vase_h * 0.6),
        (vase_x - vase_w * 0.6, table_y),
        (vase_x + vase_w * 0.6, table_y),
        (vase_x + vase_w * 0.8, vase_y + vase_h * 0.6),
        (vase_x + vase_w * 0.7, vase_y + vase_h * 0.3),
        (vase_x + vase_w * 0.5, vase_y),
    ]
    draw.polygon(vase_points, outline=LINE_COLOR, width=2)

    # Flower in vase
    flower_cx = vase_x + sway * 0.5
    flower_cy = vase_y - 20 * scale
    # Stem
    draw.line([(vase_x, vase_y), (flower_cx, flower_cy)], fill=(80, 120, 80), width=2)
    # Petals
    petal_r = 12 * scale
    for angle in range(0, 360, 60):
        px = flower_cx + petal_r * math.cos(math.radians(angle))
        py = flower_cy + petal_r * math.sin(math.radians(angle))
        draw.ellipse([px - petal_r * 0.7, py - petal_r * 0.7,
                      px + petal_r * 0.7, py + petal_r * 0.7],
                     outline=LINE_COLOR, width=1)
    # Center
    draw.ellipse([flower_cx - 5, flower_cy - 5, flower_cx + 5, flower_cy + 5],
                 fill=(255, 200, 100), outline=LINE_COLOR)

    # Apple
    apple_cx = cx + 40 * scale
    apple_cy = table_y - 20 * scale
    draw.ellipse([apple_cx - 20 * scale, apple_cy - 18 * scale,
                  apple_cx + 20 * scale, apple_cy + 18 * scale],
                 outline=LINE_COLOR, width=2)
    # Apple stem
    draw.line([(apple_cx, apple_cy - 18 * scale), (apple_cx + 3, apple_cy - 25 * scale)],
              fill=LINE_COLOR, width=2)
    # Apple leaf
    draw.ellipse([apple_cx + 3, apple_cy - 30 * scale, apple_cx + 15, apple_cy - 22 * scale],
                 outline=LINE_COLOR, width=1)

    # Orange
    orange_cx = cx + 70 * scale
    orange_cy = table_y - 15 * scale
    draw.ellipse([orange_cx - 15 * scale, orange_cy - 15 * scale,
                  orange_cx + 15 * scale, orange_cy + 15 * scale],
                 outline=LINE_COLOR, width=2)


def create_still_life_drawing():
    """Create still life original drawing"""
    img = Image.new('RGB', (300, 250), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw_still_life(draw, 150, 120)
    return img


def create_still_life_gif():
    """Create still life breathing/sway animation"""
    frames = []
    num_frames = 30

    for i in range(num_frames):
        img = Image.new('RGB', (300, 250), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi
        sway = math.sin(t) * 3
        scale = 1.0 + math.sin(t) * 0.01

        draw_still_life(draw, 150, 120, sway=sway, scale=scale)
        frames.append(img)

    return frames


# ============================================================================
# ROBOT CHARACTER
# ============================================================================

def draw_robot(draw, cx, cy, scale=1.0, arm_angle=0, bounce=0):
    """Draw a simple robot"""
    cy = cy - bounce

    # Body colors
    body_color = (100, 100, 110)
    accent = BLUE

    # Head
    head_w = 45 * scale
    head_h = 40 * scale
    head_y = cy - 70 * scale
    draw.rectangle([cx - head_w, head_y, cx + head_w, head_y + head_h],
                   fill=body_color, outline=LINE_COLOR, width=2)

    # Eyes
    eye_r = 10 * scale
    eye_y = head_y + head_h * 0.4
    draw.ellipse([cx - 25 * scale - eye_r, eye_y - eye_r,
                  cx - 25 * scale + eye_r, eye_y + eye_r], fill=accent)
    draw.ellipse([cx + 25 * scale - eye_r, eye_y - eye_r,
                  cx + 25 * scale + eye_r, eye_y + eye_r], fill=accent)

    # Antenna
    draw.line([(cx, head_y), (cx, head_y - 15 * scale)], fill=body_color, width=3)
    draw.ellipse([cx - 5, head_y - 22 * scale, cx + 5, head_y - 12 * scale], fill=accent)

    # Body
    body_top = head_y + head_h + 5 * scale
    body_bottom = cy + 35 * scale
    body_w = 40 * scale
    draw.rectangle([cx - body_w, body_top, cx + body_w, body_bottom],
                   fill=body_color, outline=LINE_COLOR, width=2)
    # Chest light
    draw.ellipse([cx - 8, body_top + 15, cx + 8, body_top + 30], fill=accent)

    # Arms
    arm_y = body_top + 10 * scale
    arm_len = 40 * scale
    arm_w = 12 * scale

    # Left arm
    la = math.radians(90 + arm_angle)
    left_hand_x = cx - body_w - arm_len * math.cos(la)
    left_hand_y = arm_y + arm_len * math.sin(la)
    draw.line([(cx - body_w, arm_y), (left_hand_x, left_hand_y)], fill=body_color, width=int(arm_w))

    # Right arm
    ra = math.radians(90 - arm_angle)
    right_hand_x = cx + body_w + arm_len * math.cos(ra)
    right_hand_y = arm_y + arm_len * math.sin(ra)
    draw.line([(cx + body_w, arm_y), (right_hand_x, right_hand_y)], fill=body_color, width=int(arm_w))

    # Legs
    leg_top = body_bottom + 5 * scale
    leg_bottom = cy + 85 * scale
    leg_w = 15 * scale
    # Left leg
    draw.rectangle([cx - 25 * scale - leg_w, leg_top, cx - 25 * scale + leg_w, leg_bottom],
                   fill=body_color, outline=LINE_COLOR, width=2)
    # Right leg
    draw.rectangle([cx + 25 * scale - leg_w, leg_top, cx + 25 * scale + leg_w, leg_bottom],
                   fill=body_color, outline=LINE_COLOR, width=2)


def create_robot_drawing():
    """Create robot original drawing"""
    img = Image.new('RGBA', (200, 250), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 190, 240], fill=(255, 255, 255, 255))
    draw_robot(draw, 100, 120, scale=1.0)
    return img


def create_robot_gif():
    """Create robot animation"""
    frames = []
    num_frames = 16

    for i in range(num_frames):
        img = Image.new('RGB', (200, 250), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Quantized, mechanical movement
        step = int(i / num_frames * 4) % 4
        arm_angles = [0, 20, 0, -20]
        bounces = [0, 2, 0, 2]

        draw_robot(draw, 100, 120, scale=1.0, arm_angle=arm_angles[step], bounce=bounces[step])
        frames.append(img)

    return frames


# ============================================================================
# CARTOON CAT
# ============================================================================

def draw_cartoon_cat(draw, cx, cy, scale=1.0, ear_twitch=0, tail_wag=0):
    """Draw a cute cartoon cat"""
    # Body
    body_w = 50 * scale
    body_h = 40 * scale
    body_y = cy + 20 * scale
    draw.ellipse([cx - body_w, body_y - body_h, cx + body_w, body_y + body_h],
                 fill=(255, 180, 100), outline=LINE_COLOR, width=2)

    # Head
    head_r = 35 * scale
    head_y = cy - 25 * scale
    draw.ellipse([cx - head_r, head_y - head_r, cx + head_r, head_y + head_r],
                 fill=(255, 180, 100), outline=LINE_COLOR, width=2)

    # Ears
    # Left ear
    ear_points = [
        (cx - 25 * scale, head_y - head_r * 0.5 + ear_twitch),
        (cx - 35 * scale - ear_twitch, head_y - head_r - 20 * scale),
        (cx - 10 * scale, head_y - head_r * 0.7)
    ]
    draw.polygon(ear_points, fill=(255, 180, 100), outline=LINE_COLOR, width=2)
    # Inner ear
    inner_ear = [
        (cx - 25 * scale, head_y - head_r * 0.5 + ear_twitch + 5),
        (cx - 30 * scale - ear_twitch * 0.5, head_y - head_r - 10 * scale),
        (cx - 15 * scale, head_y - head_r * 0.7 + 5)
    ]
    draw.polygon(inner_ear, fill=(255, 200, 150))

    # Right ear
    ear_points = [
        (cx + 25 * scale, head_y - head_r * 0.5 - ear_twitch),
        (cx + 35 * scale + ear_twitch, head_y - head_r - 20 * scale),
        (cx + 10 * scale, head_y - head_r * 0.7)
    ]
    draw.polygon(ear_points, fill=(255, 180, 100), outline=LINE_COLOR, width=2)
    inner_ear = [
        (cx + 25 * scale, head_y - head_r * 0.5 - ear_twitch + 5),
        (cx + 30 * scale + ear_twitch * 0.5, head_y - head_r - 10 * scale),
        (cx + 15 * scale, head_y - head_r * 0.7 + 5)
    ]
    draw.polygon(inner_ear, fill=(255, 200, 150))

    # Eyes
    eye_y = head_y - 5 * scale
    eye_r = 10 * scale
    # Left eye
    draw.ellipse([cx - 18 * scale - eye_r, eye_y - eye_r,
                  cx - 18 * scale + eye_r, eye_y + eye_r], fill=(50, 50, 50))
    draw.ellipse([cx - 18 * scale - eye_r * 0.3, eye_y - eye_r * 0.5,
                  cx - 18 * scale + eye_r * 0.3, eye_y], fill=(255, 255, 255))
    # Right eye
    draw.ellipse([cx + 18 * scale - eye_r, eye_y - eye_r,
                  cx + 18 * scale + eye_r, eye_y + eye_r], fill=(50, 50, 50))
    draw.ellipse([cx + 18 * scale - eye_r * 0.3, eye_y - eye_r * 0.5,
                  cx + 18 * scale + eye_r * 0.3, eye_y], fill=(255, 255, 255))

    # Nose
    nose_y = head_y + 10 * scale
    draw.polygon([(cx, nose_y), (cx - 6, nose_y + 8), (cx + 6, nose_y + 8)], fill=(255, 150, 150))

    # Whiskers
    whisker_y = nose_y + 5
    for dy in [-5, 0, 5]:
        draw.line([(cx - 10, whisker_y + dy), (cx - 35, whisker_y + dy - 3)], fill=LINE_COLOR, width=1)
        draw.line([(cx + 10, whisker_y + dy), (cx + 35, whisker_y + dy - 3)], fill=LINE_COLOR, width=1)

    # Front paws
    paw_y = body_y + body_h - 5 * scale
    draw.ellipse([cx - 35 * scale, paw_y - 10, cx - 15 * scale, paw_y + 10],
                 fill=(255, 180, 100), outline=LINE_COLOR, width=2)
    draw.ellipse([cx + 15 * scale, paw_y - 10, cx + 35 * scale, paw_y + 10],
                 fill=(255, 180, 100), outline=LINE_COLOR, width=2)

    # Tail
    tail_start = (cx + body_w - 10, body_y)
    tail_end = (cx + body_w + 30 + tail_wag, body_y - 30 - tail_wag * 0.5)
    tail_mid = (cx + body_w + 15, body_y - 10)
    # Draw curved tail with arc
    draw.line([tail_start, tail_mid, tail_end], fill=(255, 180, 100), width=int(8 * scale))


def create_cat_drawing():
    """Create cartoon cat original drawing"""
    img = Image.new('RGBA', (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5, 5, 195, 195], fill=(255, 255, 255, 255))
    draw_cartoon_cat(draw, 100, 95, scale=0.9)
    return img


def create_cat_gif():
    """Create cat breathing animation"""
    frames = []
    num_frames = 24

    for i in range(num_frames):
        img = Image.new('RGB', (200, 200), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi
        ear_twitch = math.sin(t * 3) * 2 if i % 12 < 3 else 0  # Occasional ear twitch
        tail_wag = math.sin(t * 2) * 8
        scale = 0.9 + math.sin(t) * 0.02  # Breathing

        draw_cartoon_cat(draw, 100, 95, scale=scale, ear_twitch=ear_twitch, tail_wag=tail_wag)
        frames.append(img)

    return frames


# ============================================================================
# SAVE HELPERS
# ============================================================================

def save_image(img, path):
    """Save PIL image to file"""
    img.save(path)
    print(f"  Saved: {path}")


def save_gif(frames, path, duration=67):
    """Save frames as GIF"""
    frames[0].save(
        path,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0
    )
    print(f"  Saved: {path} ({len(frames)} frames)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    ensure_dirs()

    print("\n=== Generating Demo Assets ===\n")

    # Pug
    print("Creating Pug assets...")
    save_image(create_pug_drawing(), os.path.join(STATIC_DIR, 'drawing2.jpg'))
    save_gif(create_pug_gif(), os.path.join(STATIC_DIR, 'demo-pug-ai.gif'), duration=80)

    # Still Life
    print("\nCreating Still Life assets...")
    save_image(create_still_life_drawing(), os.path.join(STATIC_DIR, 'drawing1.jpg'))
    save_gif(create_still_life_gif(), os.path.join(STATIC_DIR, 'demo-still-life-ai.gif'), duration=80)

    # Stick figure sources
    print("\nCreating Stick Figure sources...")
    save_image(create_stick_figure_png('walk'), os.path.join(SOURCES_DIR, 'stick_walk.png'))
    save_image(create_stick_figure_png('wave'), os.path.join(SOURCES_DIR, 'stick_wave.png'))
    save_image(create_stick_figure_png('dance'), os.path.join(SOURCES_DIR, 'stick_dance.png'))

    # Stick figure animations
    print("\nCreating Stick Figure animations...")
    save_gif(create_stick_walk_gif(), os.path.join(EXAMPLES_DIR, 'stick_walk.gif'), duration=50)
    save_gif(create_stick_wave_gif(), os.path.join(EXAMPLES_DIR, 'stick_wave.gif'), duration=60)
    save_gif(create_stick_dance_gif(), os.path.join(EXAMPLES_DIR, 'stick_dance.gif'), duration=50)

    # Robot
    print("\nCreating Robot assets...")
    save_image(create_robot_drawing(), os.path.join(SOURCES_DIR, 'robot.png'))
    save_gif(create_robot_gif(), os.path.join(EXAMPLES_DIR, 'robot.gif'), duration=100)

    # Cartoon Cat
    print("\nCreating Cartoon Cat assets...")
    save_image(create_cat_drawing(), os.path.join(SOURCES_DIR, 'cartoon_cat.png'))
    save_gif(create_cat_gif(), os.path.join(EXAMPLES_DIR, 'cartoon_cat.gif'), duration=70)

    print("\n=== All demo assets generated! ===")
    print(f"Output directory: {STATIC_DIR}")


if __name__ == '__main__':
    main()
