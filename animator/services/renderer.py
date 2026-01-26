"""
Animation renderer service.
Renders animated drawings to video or GIF format.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
import subprocess
import tempfile
from typing import Callable, Optional
from django.conf import settings


class AnimationRenderer:
    """
    Renders animation projects to various output formats.
    Uses OpenCV for frame rendering and FFmpeg for video encoding.
    """

    QUALITY_SETTINGS = {
        'low': {'width': 854, 'height': 480, 'bitrate': '1M'},
        'medium': {'width': 1280, 'height': 720, 'bitrate': '2.5M'},
        'high': {'width': 1920, 'height': 1080, 'bitrate': '5M'},
        'ultra': {'width': 3840, 'height': 2160, 'bitrate': '15M'},
    }

    def __init__(self, project):
        """
        Initialize renderer with project.

        Args:
            project: Project model instance
        """
        self.project = project
        self.width = project.width
        self.height = project.height
        self.fps = project.fps
        self.duration = project.duration_seconds

        # Cache loaded images
        self.image_cache = {}

    def render(self, format: str = 'mp4', quality: str = 'high',
               include_audio: bool = True, transparent: bool = False,
               progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """
        Render complete animation.

        Args:
            format: Output format ('mp4', 'webm', 'gif', 'png_sequence', 'mov')
            quality: Quality preset
            include_audio: Include audio tracks
            transparent: Use transparent background (for gif/webm/mov)
            progress_callback: Called with progress percentage

        Returns:
            str: Path to output file
        """
        # Get quality settings
        settings = self.QUALITY_SETTINGS.get(quality, self.QUALITY_SETTINGS['high'])
        out_width = min(settings['width'], self.width)
        out_height = min(settings['height'], self.height)

        # Calculate total frames
        total_frames = int(self.duration * self.fps)

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp()
        frames_dir = os.path.join(temp_dir, 'frames')
        os.makedirs(frames_dir)

        try:
            # Render all frames
            for frame_num in range(total_frames):
                frame = self._render_frame_at_time(frame_num / self.fps, transparent)

                # Resize if needed
                if frame.shape[1] != out_width or frame.shape[0] != out_height:
                    frame = cv2.resize(frame, (out_width, out_height),
                                      interpolation=cv2.INTER_LANCZOS4)

                # Save frame
                frame_path = os.path.join(frames_dir, f'frame_{frame_num:06d}.png')
                cv2.imwrite(frame_path, frame)

                # Report progress
                if progress_callback:
                    render_progress = int((frame_num / total_frames) * 80)
                    progress_callback(render_progress)

            # Encode video
            output_path = self._encode_video(
                frames_dir, format, quality, include_audio,
                transparent, out_width, out_height
            )

            if progress_callback:
                progress_callback(100)

            return output_path

        finally:
            # Cleanup temp frames
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def render_frame(self, scene, frame_number: int) -> str:
        """
        Render a single frame for preview.

        Args:
            scene: Scene model instance
            frame_number: Frame number to render

        Returns:
            str: Path to rendered frame image
        """
        time = frame_number / self.fps
        frame = self._render_scene_at_time(scene, time, False)

        # Save to temp file
        output_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'previews')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'preview_{uuid.uuid4()}.png')

        cv2.imwrite(output_path, frame)
        return output_path

    def _render_frame_at_time(self, time: float, transparent: bool) -> np.ndarray:
        """Render complete frame at given time."""
        # Create canvas
        if transparent:
            canvas = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        else:
            canvas = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255

        # Find active scene at this time
        current_time = 0
        for scene in self.project.scenes.all().order_by('order'):
            scene_end = current_time + scene.duration

            if current_time <= time < scene_end:
                scene_time = time - current_time
                canvas = self._render_scene_at_time(scene, scene_time, transparent)
                break

            current_time = scene_end

        return canvas

    def _render_scene_at_time(self, scene, time: float, transparent: bool) -> np.ndarray:
        """Render a scene at given time."""
        # Create canvas
        if transparent:
            canvas = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        else:
            # Parse background color
            bg_color = self._hex_to_bgr(scene.background_color)
            canvas = np.full((self.height, self.width, 3), bg_color, dtype=np.uint8)

        # Draw background image if present
        if scene.background:
            bg_image = self._load_image(scene.background.image.path)
            if bg_image is not None:
                canvas = self._composite_image(canvas, bg_image, 0, 0, 1.0, 0)

        # Draw characters sorted by z-index
        for scene_char in scene.scene_characters.all().order_by('z_index'):
            # Check if character is visible at this time
            if time < scene_char.enter_time:
                continue
            if scene_char.exit_time and time >= scene_char.exit_time:
                continue

            # Get character image
            char = scene_char.character
            if char.processed_image:
                char_image = self._load_image(char.processed_image.path)
            else:
                char_image = self._load_image(char.original_image.path)

            if char_image is None:
                continue

            # Apply animations
            animated_image = self._apply_animations(
                char_image, scene_char, char.rig_data, time
            )

            # Apply flip if needed
            if scene_char.flip_horizontal:
                animated_image = cv2.flip(animated_image, 1)

            # Composite onto canvas
            canvas = self._composite_image(
                canvas, animated_image,
                scene_char.position_x, scene_char.position_y,
                scene_char.scale, scene_char.rotation
            )

        # Draw text overlays
        for overlay in scene.text_overlays.all():
            if overlay.start_time <= time < overlay.start_time + overlay.duration:
                overlay_time = time - overlay.start_time
                canvas = self._render_text_overlay(canvas, overlay, overlay_time)

        # Apply camera
        if scene.camera_zoom != 1.0 or scene.camera_x != 0 or scene.camera_y != 0:
            canvas = self._apply_camera(canvas, scene)

        return canvas

    def _apply_animations(self, image: np.ndarray, scene_char,
                         rig_data: dict, time: float) -> np.ndarray:
        """Apply animations to character image."""
        # Get all animations for this scene character
        animations = scene_char.animations.all()

        if not animations:
            return image

        # Find active animation
        for anim in animations:
            anim_start = anim.start_time
            anim_duration = anim.duration * anim.speed_multiplier

            if anim.loop:
                # Loop the animation
                if time >= anim_start:
                    local_time = (time - anim_start) % anim_duration
                    return self._apply_motion(image, anim, rig_data, local_time)
            else:
                if anim_start <= time < anim_start + anim_duration:
                    local_time = time - anim_start
                    return self._apply_motion(image, anim, rig_data, local_time)

        return image

    def _apply_motion(self, image: np.ndarray, animation,
                     rig_data: dict, local_time: float) -> np.ndarray:
        """Apply motion data to image."""
        motion_data = {}

        if animation.motion_preset:
            motion_data = animation.motion_preset.motion_data
        elif animation.keyframes:
            motion_data = {'keyframes': animation.keyframes, 'duration': animation.duration}

        if not motion_data or 'keyframes' not in motion_data:
            return image

        # Interpolate between keyframes
        keyframes = motion_data['keyframes']
        duration = motion_data.get('duration', animation.duration)

        # Find surrounding keyframes
        prev_kf = keyframes[0]
        next_kf = keyframes[-1]

        for i, kf in enumerate(keyframes):
            if kf['time'] <= local_time:
                prev_kf = kf
                if i + 1 < len(keyframes):
                    next_kf = keyframes[i + 1]
                else:
                    next_kf = kf
            else:
                next_kf = kf
                break

        # Calculate interpolation factor
        time_range = next_kf['time'] - prev_kf['time']
        if time_range > 0:
            t = (local_time - prev_kf['time']) / time_range
            t = self._ease(t, animation.easing)
        else:
            t = 0

        # Interpolate joint values
        interpolated_joints = {}
        for joint_name in set(list(prev_kf.get('joints', {}).keys()) +
                             list(next_kf.get('joints', {}).keys())):
            prev_joint = prev_kf.get('joints', {}).get(joint_name, {'rotation': 0})
            next_joint = next_kf.get('joints', {}).get(joint_name, {'rotation': 0})

            interpolated_joints[joint_name] = {
                'rotation': prev_joint.get('rotation', 0) * (1 - t) +
                           next_joint.get('rotation', 0) * t
            }

        # Apply deformation based on interpolated joints
        return self._deform_image(image, rig_data, interpolated_joints)

    def _deform_image(self, image: np.ndarray, rig_data: dict,
                     joints: dict) -> np.ndarray:
        """
        Deform image based on joint rotations.
        Uses mesh deformation for smooth results.
        """
        if not rig_data or 'joints' not in rig_data:
            return image

        # For now, apply simple rotation-based deformation
        # In production, this would use proper skeletal deformation

        h, w = image.shape[:2]

        # Calculate overall rotation from spine/torso
        spine_rotation = joints.get('spine', {}).get('rotation', 0)

        if abs(spine_rotation) > 0.1:
            # Apply slight rotation to entire image
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, spine_rotation, 1.0)
            image = cv2.warpAffine(image, matrix, (w, h),
                                   flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=(0, 0, 0, 0) if image.shape[2] == 4 else (255, 255, 255))

        return image

    def _ease(self, t: float, easing: str) -> float:
        """Apply easing function to interpolation parameter."""
        if easing == 'linear':
            return t
        elif easing == 'ease-in':
            return t * t
        elif easing == 'ease-out':
            return 1 - (1 - t) * (1 - t)
        elif easing == 'ease-in-out':
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - pow(-2 * t + 2, 2) / 2
        elif easing == 'bounce':
            if t < 0.5:
                return 8 * t * t * t * t
            else:
                return 1 - pow(-2 * t + 2, 4) / 2
        return t

    def _load_image(self, path: str) -> Optional[np.ndarray]:
        """Load image from path with caching."""
        if path in self.image_cache:
            return self.image_cache[path].copy()

        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if image is not None:
            self.image_cache[path] = image.copy()

        return image

    def _composite_image(self, canvas: np.ndarray, image: np.ndarray,
                        x: float, y: float, scale: float, rotation: float) -> np.ndarray:
        """Composite image onto canvas with transformations."""
        if image is None:
            return canvas

        h, w = image.shape[:2]

        # Apply scale
        if scale != 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            h, w = new_h, new_w

        # Apply rotation
        if rotation != 0:
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)

            # Calculate new bounds
            cos = abs(matrix[0, 0])
            sin = abs(matrix[0, 1])
            new_w = int(h * sin + w * cos)
            new_h = int(h * cos + w * sin)

            matrix[0, 2] += (new_w - w) / 2
            matrix[1, 2] += (new_h - h) / 2

            image = cv2.warpAffine(image, matrix, (new_w, new_h),
                                   borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=(0, 0, 0, 0) if image.shape[2] == 4 else (255, 255, 255))
            h, w = new_h, new_w

        # Calculate position (centered)
        pos_x = int(x - w / 2)
        pos_y = int(y - h / 2)

        # Composite
        return self._alpha_composite(canvas, image, pos_x, pos_y)

    def _alpha_composite(self, canvas: np.ndarray, overlay: np.ndarray,
                        x: int, y: int) -> np.ndarray:
        """Alpha composite overlay onto canvas."""
        canvas_h, canvas_w = canvas.shape[:2]
        overlay_h, overlay_w = overlay.shape[:2]

        # Calculate visible region
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(canvas_w, x + overlay_w)
        y2 = min(canvas_h, y + overlay_h)

        if x1 >= x2 or y1 >= y2:
            return canvas

        # Overlay region
        ox1 = x1 - x
        oy1 = y1 - y
        ox2 = ox1 + (x2 - x1)
        oy2 = oy1 + (y2 - y1)

        # Check if overlay has alpha
        if overlay.shape[2] == 4:
            alpha = overlay[oy1:oy2, ox1:ox2, 3:4] / 255.0
            overlay_rgb = overlay[oy1:oy2, ox1:ox2, :3]

            if canvas.shape[2] == 4:
                canvas_rgb = canvas[y1:y2, x1:x2, :3]
                canvas[y1:y2, x1:x2, :3] = (alpha * overlay_rgb +
                                            (1 - alpha) * canvas_rgb).astype(np.uint8)
                canvas[y1:y2, x1:x2, 3:4] = np.maximum(
                    canvas[y1:y2, x1:x2, 3:4],
                    overlay[oy1:oy2, ox1:ox2, 3:4]
                )
            else:
                canvas_rgb = canvas[y1:y2, x1:x2]
                canvas[y1:y2, x1:x2] = (alpha * overlay_rgb +
                                        (1 - alpha) * canvas_rgb).astype(np.uint8)
        else:
            canvas[y1:y2, x1:x2, :3] = overlay[oy1:oy2, ox1:ox2]

        return canvas

    def _render_text_overlay(self, canvas: np.ndarray, overlay, time: float) -> np.ndarray:
        """Render text overlay onto canvas."""
        # Use PIL for text rendering (better font support)
        pil_image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # Load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                      overlay.font_size)
        except:
            font = ImageFont.load_default()

        # Calculate position
        text_x = int(overlay.position_x * self.width / 100)
        text_y = int(overlay.position_y * self.height / 100)

        # Parse color
        color = self._hex_to_rgb(overlay.color)

        # Apply animation
        alpha = 1.0
        if overlay.animation == 'fade':
            fade_duration = 0.5
            if time < fade_duration:
                alpha = time / fade_duration
            elif time > overlay.duration - fade_duration:
                alpha = (overlay.duration - time) / fade_duration

        # Draw text
        if alpha >= 0.1:
            draw.text((text_x, text_y), overlay.text, font=font, fill=color)

        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def _apply_camera(self, canvas: np.ndarray, scene) -> np.ndarray:
        """Apply camera transformations."""
        h, w = canvas.shape[:2]

        # Create transformation matrix
        center_x = w / 2 + scene.camera_x
        center_y = h / 2 + scene.camera_y

        matrix = cv2.getRotationMatrix2D((center_x, center_y), 0, scene.camera_zoom)

        return cv2.warpAffine(canvas, matrix, (w, h),
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(255, 255, 255))

    def _encode_video(self, frames_dir: str, format: str, quality: str,
                     include_audio: bool, transparent: bool,
                     width: int, height: int) -> str:
        """Encode frames to video using FFmpeg."""
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f'export_{uuid.uuid4()}.{format}'
        output_path = os.path.join(output_dir, output_filename)

        quality_settings = self.QUALITY_SETTINGS.get(quality, self.QUALITY_SETTINGS['high'])

        if format == 'gif':
            # Use palette-based GIF encoding
            palette_path = os.path.join(frames_dir, 'palette.png')

            # Generate palette
            subprocess.run([
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-vf', f'fps={min(self.fps, 15)},scale={width}:-1:flags=lanczos,palettegen',
                palette_path
            ], check=True, capture_output=True)

            # Create GIF
            subprocess.run([
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-i', palette_path,
                '-lavfi', f'fps={min(self.fps, 15)},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse',
                output_path
            ], check=True, capture_output=True)

        elif format == 'webm':
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-c:v', 'libvpx-vp9',
                '-b:v', quality_settings['bitrate'],
                '-pix_fmt', 'yuva420p' if transparent else 'yuv420p',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        elif format == 'mov':
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-c:v', 'prores_ks',
                '-profile:v', '4444' if transparent else '3',
                '-pix_fmt', 'yuva444p10le' if transparent else 'yuv422p10le',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        elif format == 'png_sequence':
            # Just copy frames to output
            import shutil
            output_path = os.path.join(output_dir, f'sequence_{uuid.uuid4()}')
            shutil.copytree(frames_dir, output_path)

        else:  # mp4
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-preset', 'slow',
                '-crf', '18',
                '-pix_fmt', 'yuv420p',
                '-b:v', quality_settings['bitrate'],
                output_path
            ]

            # Add audio if needed
            if include_audio and self.project.audio_tracks.exists():
                # Mix audio tracks (simplified - would need proper mixing in production)
                audio_track = self.project.audio_tracks.first()
                if audio_track and audio_track.audio_file:
                    cmd.extend(['-i', audio_track.audio_file.path])
                    cmd.extend(['-c:a', 'aac', '-b:a', '192k'])

            subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def _hex_to_bgr(self, hex_color: str) -> tuple:
        """Convert hex color to BGR tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
