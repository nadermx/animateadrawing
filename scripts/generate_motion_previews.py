#!/usr/bin/env python3
"""
Generate animated GIF previews for motion presets.
Creates a simple stick figure and applies the motion to demonstrate each preset.
"""
import os
import sys
import math
from io import BytesIO
from PIL import Image, ImageDraw

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from django.core.files.base import ContentFile
from animator.models import MotionPreset

# GIF settings
WIDTH = 200
HEIGHT = 200
FPS = 15
BG_COLOR = (248, 249, 250)  # Light gray background
FIGURE_COLOR = (59, 130, 246)  # Blue (#3b82f6)
SECONDARY_COLOR = (37, 99, 235)  # Darker blue


def draw_stick_figure(draw, center_x, center_y, scale=1.0, rotation=0, arm_angle=0, leg_angle=0):
    """Draw a properly proportioned stick figure with natural motion"""
    # Apply rotation around center point
    cos_r = math.cos(math.radians(rotation))
    sin_r = math.sin(math.radians(rotation))

    def rotate(x, y):
        dx, dy = x - center_x, y - center_y
        nx = center_x + (dx * cos_r - dy * sin_r)
        ny = center_y + (dx * sin_r + dy * cos_r)
        return nx, ny

    # Better proportions for 200x200 canvas
    head_center_y = center_y - 55 * scale
    neck_y = center_y - 42 * scale
    shoulder_y = center_y - 38 * scale
    hip_y = center_y - 5 * scale

    line_width = 3
    head_r = 12 * scale

    # HEAD
    hx, hy = rotate(center_x, head_center_y)
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=FIGURE_COLOR)

    # TORSO (neck to hip)
    neck_pt = rotate(center_x, neck_y)
    hip_pt = rotate(center_x, hip_y)
    draw.line([neck_pt, hip_pt], fill=FIGURE_COLOR, width=line_width)

    # ARMS - hang from shoulders, swing forward/back
    arm_len = 28 * scale
    shoulder_l = rotate(center_x - 2 * scale, shoulder_y)
    shoulder_r = rotate(center_x + 2 * scale, shoulder_y)

    # Left arm swings with arm_angle
    la_rad = math.radians(arm_angle * 0.8)
    left_hand = (
        shoulder_l[0] + math.sin(la_rad) * arm_len,
        shoulder_l[1] + math.cos(la_rad) * arm_len
    )
    draw.line([shoulder_l, left_hand], fill=FIGURE_COLOR, width=line_width)

    # Right arm swings opposite
    ra_rad = math.radians(-arm_angle * 0.8)
    right_hand = (
        shoulder_r[0] + math.sin(ra_rad) * arm_len,
        shoulder_r[1] + math.cos(ra_rad) * arm_len
    )
    draw.line([shoulder_r, right_hand], fill=FIGURE_COLOR, width=line_width)

    # LEGS - properly proportioned
    leg_len = 55 * scale
    hip_width = 8 * scale

    # Left leg
    left_hip = rotate(center_x - hip_width/2, hip_y)
    ll_rad = math.radians(leg_angle)
    left_foot = (
        left_hip[0] + math.sin(ll_rad) * leg_len,
        left_hip[1] + math.cos(ll_rad) * leg_len
    )
    draw.line([left_hip, left_foot], fill=FIGURE_COLOR, width=line_width)

    # Right leg (swings opposite)
    right_hip = rotate(center_x + hip_width/2, hip_y)
    rl_rad = math.radians(-leg_angle)
    right_foot = (
        right_hip[0] + math.sin(rl_rad) * leg_len,
        right_hip[1] + math.cos(rl_rad) * leg_len
    )
    draw.line([right_hip, right_foot], fill=FIGURE_COLOR, width=line_width)


def generate_walk_frames(num_frames):
    """Generate walking animation frames with natural motion"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Natural walking motion
        leg_swing = math.sin(t) * 20
        arm_swing = -math.sin(t - 0.2) * 18  # Slight delay for follow-through
        bounce = abs(math.sin(t * 2)) * 4
        lean = math.sin(t) * 2  # Subtle body lean

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - bounce,
                          rotation=lean, arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)
    return frames


def generate_run_frames(num_frames):
    """Generate running animation frames - faster, more dynamic"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Running is faster with larger movements
        leg_swing = math.sin(t) * 30
        arm_swing = -math.sin(t) * 35
        bounce = abs(math.sin(t * 2)) * 10  # Higher bounce
        lean = 8 + math.sin(t) * 3  # Forward lean with slight variation

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - bounce,
                          rotation=lean, arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)
    return frames


def generate_jump_frames(num_frames):
    """Generate jumping animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Jump arc
        t = i / num_frames
        jump_height = -math.sin(t * math.pi) * 40

        # Arms up during jump
        arm_angle = -math.sin(t * math.pi) * 45 - 20

        # Legs together during jump
        leg_angle = math.sin(t * math.pi) * 15

        # Scale slightly during jump
        scale = 1.0 + math.sin(t * math.pi) * 0.05

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - jump_height,
                          scale=scale, arm_angle=arm_angle, leg_angle=leg_angle)
        frames.append(img)
    return frames


def generate_dance_frames(num_frames):
    """Generate dancing animation frames - rhythmic and expressive"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 4 * math.pi

        # Rhythmic dancing with multiple components
        sway_x = math.sin(t) * 8
        rotation = math.sin(t) * 12
        bounce = abs(math.sin(t * 2)) * 8
        arm_angle = math.sin(t * 1.5) * 45 + math.sin(t * 0.75) * 15
        leg_angle = math.sin(t * 2) * 18

        draw_stick_figure(draw, WIDTH//2 + sway_x, HEIGHT//2 - bounce,
                          rotation=rotation, arm_angle=arm_angle, leg_angle=leg_angle)
        frames.append(img)
    return frames


def generate_wave_frames(num_frames):
    """Generate waving animation frames - friendly greeting"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 4 * math.pi

        # Subtle body sway while waving
        sway = math.sin(t * 0.5) * 2

        # Draw base figure
        draw_stick_figure(draw, WIDTH//2 + sway, HEIGHT//2, rotation=sway * 0.5)

        # Draw waving arm raised high
        shoulder_y = HEIGHT//2 - 38
        shoulder = (WIDTH//2 + 2 + sway, shoulder_y)
        arm_len = 28

        # Arm raised and waving
        wave = math.sin(t) * 35
        base_angle = -70

        hand_x = shoulder[0] + arm_len * math.sin(math.radians(base_angle + wave))
        hand_y = shoulder[1] - arm_len * math.cos(math.radians(base_angle + wave))

        draw.line([shoulder, (hand_x, hand_y)], fill=FIGURE_COLOR, width=4)
        draw.ellipse([hand_x - 4, hand_y - 4, hand_x + 4, hand_y + 4], fill=FIGURE_COLOR)

        frames.append(img)
    return frames


def generate_nod_frames(num_frames):
    """Generate nodding animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Head nods forward
        rotation = math.sin(t) * 8

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2, rotation=rotation)
        frames.append(img)
    return frames


def generate_shake_frames(num_frames):
    """Generate head shaking animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 3 * math.pi

        # Horizontal shake
        offset_x = math.sin(t) * 8

        draw_stick_figure(draw, WIDTH//2 + offset_x, HEIGHT//2)
        frames.append(img)
    return frames


def generate_idle_frames(num_frames):
    """Generate subtle idle animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Very subtle breathing motion
        scale = 1.0 + math.sin(t) * 0.015
        slight_sway = math.sin(t * 0.5) * 2

        draw_stick_figure(draw, WIDTH//2 + slight_sway, HEIGHT//2, scale=scale)
        frames.append(img)
    return frames


def generate_breathe_frames(num_frames):
    """Generate breathing animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Breathing - scale and slight shoulder rise
        scale = 1.0 + math.sin(t) * 0.02
        y_offset = math.sin(t) * 2

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - y_offset, scale=scale)
        frames.append(img)
    return frames


def generate_robot_frames(num_frames):
    """Generate robot walk animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Quantized movement (steps)
        steps = 8
        step_index = int(i / num_frames * steps) % steps
        t = step_index / steps * 2 * math.pi

        leg_swing = math.sin(t) * 20
        arm_swing = -math.sin(t) * 15
        rotation = math.sin(t) * 5

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2,
                          rotation=rotation, arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)
    return frames


def generate_ai_action_frames(num_frames):
    """Generate dynamic AI action animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Dynamic motion with multiple components
        rotation = math.sin(t) * 15
        scale = 1.0 + math.sin(t * 2) * 0.08
        arm_angle = math.sin(t * 1.5) * 45
        leg_angle = math.sin(t) * 20
        bounce = abs(math.sin(t * 2)) * 10

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - bounce,
                          scale=scale, rotation=rotation,
                          arm_angle=arm_angle, leg_angle=leg_angle)
        frames.append(img)
    return frames


def generate_gentle_sway_frames(num_frames):
    """Generate gentle swaying animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Gentle side-to-side sway
        rotation = math.sin(t) * 5
        x_offset = math.sin(t) * 3

        draw_stick_figure(draw, WIDTH//2 + x_offset, HEIGHT//2, rotation=rotation)
        frames.append(img)
    return frames


def generate_natural_motion_frames(num_frames):
    """Generate natural flowing motion frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi

        # Natural organic motion
        rotation = math.sin(t) * 6 + math.sin(t * 2) * 3
        scale = 1.0 + math.sin(t) * 0.02
        arm_angle = math.sin(t * 0.7) * 15
        leg_angle = math.sin(t * 0.5) * 8

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2,
                          scale=scale, rotation=rotation,
                          arm_angle=arm_angle, leg_angle=leg_angle)
        frames.append(img)
    return frames


def save_gif(frames, duration_ms=67):
    """Save frames as animated GIF and return bytes"""
    output = BytesIO()
    frames[0].save(
        output,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0
    )
    output.seek(0)
    return output.getvalue()


# Map preset names to animation generators
PRESET_GENERATORS = {
    'Walk': (generate_walk_frames, 30),
    'Run': (generate_run_frames, 20),
    'Jump': (generate_jump_frames, 22),
    'Dance': (generate_dance_frames, 45),
    'Wave': (generate_wave_frames, 30),
    'Nod': (generate_nod_frames, 15),
    'Shake': (generate_shake_frames, 15),
    'Idle': (generate_idle_frames, 45),
    'Breathe': (generate_breathe_frames, 45),
    'Robot': (generate_robot_frames, 30),
    'AI Dynamic Action': (generate_ai_action_frames, 30),
    'AI Gentle Sway': (generate_gentle_sway_frames, 30),
    'AI Natural Motion': (generate_natural_motion_frames, 30),
}


def generate_previews():
    """Generate preview GIFs for all motion presets"""
    presets = MotionPreset.objects.filter(is_system=True)

    for preset in presets:
        print(f"Processing: {preset.name}")

        # Find matching generator
        generator_info = PRESET_GENERATORS.get(preset.name)

        if generator_info:
            generator_func, num_frames = generator_info
            frames = generator_func(num_frames)
        else:
            # Default animation based on category
            if preset.category == 'locomotion':
                frames = generate_walk_frames(30)
            elif preset.category == 'gesture':
                frames = generate_wave_frames(30)
            elif preset.category == 'dance':
                frames = generate_dance_frames(45)
            elif preset.category == 'action':
                frames = generate_jump_frames(22)
            elif preset.category == 'emotion':
                frames = generate_nod_frames(15)
            elif preset.category == 'idle':
                frames = generate_idle_frames(45)
            else:
                frames = generate_idle_frames(45)

        # Calculate duration per frame from preset duration
        total_duration_ms = int(preset.duration_seconds * 1000)
        frame_duration = max(33, total_duration_ms // len(frames))  # Min 30fps

        # Generate GIF
        gif_data = save_gif(frames, duration_ms=frame_duration)

        # Save to preset
        filename = f"{preset.name.lower().replace(' ', '_')}_{preset.id}.gif"
        preset.preview_gif.save(filename, ContentFile(gif_data), save=True)

        print(f"  Saved: {preset.preview_gif.name} ({len(gif_data)} bytes)")

    print("\nDone! All preview GIFs generated.")


if __name__ == '__main__':
    generate_previews()
