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
    """Draw a simple stick figure with optional transformations"""
    # Apply rotation matrix
    cos_r = math.cos(math.radians(rotation))
    sin_r = math.sin(math.radians(rotation))

    def rotate_point(x, y):
        # Rotate around center
        dx, dy = x - center_x, y - center_y
        new_x = center_x + (dx * cos_r - dy * sin_r) * scale
        new_y = center_y + (dx * sin_r + dy * cos_r) * scale
        return new_x, new_y

    # Body proportions (relative to center)
    head_y = center_y - 45 * scale
    shoulder_y = center_y - 25 * scale
    hip_y = center_y + 10 * scale
    foot_y = center_y + 50 * scale

    # Head
    head_x, head_y_rot = rotate_point(center_x, head_y)
    head_radius = int(12 * scale)
    draw.ellipse([head_x - head_radius, head_y_rot - head_radius,
                  head_x + head_radius, head_y_rot + head_radius],
                 fill=FIGURE_COLOR)

    # Body (neck to hip)
    neck_x, neck_y = rotate_point(center_x, head_y + head_radius)
    hip_x, hip_y_rot = rotate_point(center_x, hip_y)
    draw.line([neck_x, neck_y, hip_x, hip_y_rot], fill=FIGURE_COLOR, width=3)

    # Arms
    shoulder_x, shoulder_y_rot = rotate_point(center_x, shoulder_y)
    arm_len = 30 * scale

    # Left arm
    left_arm_angle = math.radians(-45 + arm_angle)
    left_hand_x = shoulder_x - arm_len * math.cos(left_arm_angle)
    left_hand_y = shoulder_y_rot + arm_len * math.sin(left_arm_angle)
    draw.line([shoulder_x, shoulder_y_rot, left_hand_x, left_hand_y], fill=FIGURE_COLOR, width=3)

    # Right arm
    right_arm_angle = math.radians(45 - arm_angle)
    right_hand_x = shoulder_x + arm_len * math.cos(right_arm_angle)
    right_hand_y = shoulder_y_rot + arm_len * math.sin(right_arm_angle)
    draw.line([shoulder_x, shoulder_y_rot, right_hand_x, right_hand_y], fill=FIGURE_COLOR, width=3)

    # Legs
    leg_len = 40 * scale

    # Left leg - starts slightly left of hip, swings with leg_angle
    left_hip_x = hip_x - 8 * scale
    left_foot_x = left_hip_x + math.sin(math.radians(leg_angle)) * leg_len * 0.5
    left_foot_y = hip_y_rot + leg_len
    draw.line([left_hip_x, hip_y_rot, left_foot_x, left_foot_y], fill=FIGURE_COLOR, width=3)

    # Right leg - starts slightly right of hip, swings opposite to left
    right_hip_x = hip_x + 8 * scale
    right_foot_x = right_hip_x + math.sin(math.radians(-leg_angle)) * leg_len * 0.5
    right_foot_y = hip_y_rot + leg_len
    draw.line([right_hip_x, hip_y_rot, right_foot_x, right_foot_y], fill=FIGURE_COLOR, width=3)


def generate_walk_frames(num_frames):
    """Generate walking animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi
        leg_swing = math.sin(t) * 25
        arm_swing = -math.sin(t) * 20
        bounce = abs(math.sin(t)) * 3

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - bounce,
                          arm_angle=arm_swing, leg_angle=leg_swing)
        frames.append(img)
    return frames


def generate_run_frames(num_frames):
    """Generate running animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 2 * math.pi
        leg_swing = math.sin(t) * 35
        arm_swing = -math.sin(t) * 30
        bounce = abs(math.sin(t)) * 8
        lean = 5  # Forward lean

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
    """Generate dancing animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 4 * math.pi  # Faster movement

        # Sway and bounce
        rotation = math.sin(t) * 10
        bounce = abs(math.sin(t * 2)) * 5
        arm_angle = math.sin(t * 1.5) * 40
        leg_angle = math.sin(t) * 15

        draw_stick_figure(draw, WIDTH//2, HEIGHT//2 - bounce,
                          rotation=rotation, arm_angle=arm_angle, leg_angle=leg_angle)
        frames.append(img)
    return frames


def generate_wave_frames(num_frames):
    """Generate waving animation frames"""
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        t = i / num_frames * 3 * math.pi

        # Only right arm waves
        # First draw normal figure
        draw_stick_figure(draw, WIDTH//2, HEIGHT//2)

        # Override with custom waving arm
        center_x, center_y = WIDTH//2, HEIGHT//2
        shoulder_y = center_y - 25

        # Waving arm goes up and swings
        wave_angle = math.sin(t) * 30 - 60  # Swings between -30 and -90 degrees
        arm_len = 30
        hand_x = center_x + arm_len * math.cos(math.radians(wave_angle))
        hand_y = shoulder_y - arm_len * math.sin(math.radians(abs(wave_angle)))

        # Draw waving arm (cover old arm with background, draw new)
        draw.line([center_x, shoulder_y, hand_x, hand_y], fill=FIGURE_COLOR, width=4)

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
