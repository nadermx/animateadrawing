"""
Image processing service for background removal and character segmentation.
Uses rembg (based on U2-Net) for background removal.
"""
import cv2
import numpy as np
from PIL import Image
import os
import uuid
from django.conf import settings


class ImageProcessor:
    """
    Processes character images:
    - Background removal
    - Image segmentation
    - Edge detection for clean outlines
    """

    def __init__(self):
        self.rembg_session = None
        self._init_rembg()

    def _init_rembg(self):
        """Initialize rembg for background removal"""
        try:
            from rembg import new_session
            self.rembg_session = new_session("u2net")
        except ImportError:
            print("rembg not available, using fallback background removal")

    def remove_background(self, image_path: str) -> str:
        """
        Remove background from image.

        Args:
            image_path: Path to input image

        Returns:
            str: Path to processed image with transparent background
        """
        if self.rembg_session:
            return self._remove_bg_rembg(image_path)
        else:
            return self._remove_bg_fallback(image_path)

    def _remove_bg_rembg(self, image_path: str) -> str:
        """Remove background using rembg (U2-Net)"""
        from rembg import remove

        # Load image
        with open(image_path, 'rb') as f:
            input_data = f.read()

        # Remove background
        output_data = remove(
            input_data,
            session=self.rembg_session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
        )

        # Save result
        output_path = self._get_output_path()
        with open(output_path, 'wb') as f:
            f.write(output_data)

        return output_path

    def _remove_bg_fallback(self, image_path: str) -> str:
        """Fallback background removal using OpenCV"""
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to RGBA
        image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

        # Detect background (assume white or near-white)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold to find non-white areas
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Apply mask to alpha channel
        image_rgba[:, :, 3] = mask

        # Save result
        output_path = self._get_output_path()
        cv2.imwrite(output_path, image_rgba)

        return output_path

    def _get_output_path(self) -> str:
        """Generate output file path"""
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, f'processed_{uuid.uuid4()}.png')

    def segment_character(self, image_path: str) -> dict:
        """
        Segment character into parts for animation.

        Returns dict with paths to segmented parts:
        - head
        - torso
        - left_arm
        - right_arm
        - left_leg
        - right_leg
        """
        # Load image with transparency
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None or image.shape[2] < 4:
            raise ValueError("Image must have alpha channel")

        # Get mask from alpha
        mask = image[:, :, 3]

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {}

        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Segment based on proportions (simple approach)
        segments = {}

        # Head region (top 20%)
        head_h = int(h * 0.2)
        segments['head'] = self._extract_region(image, x, y, w, head_h)

        # Torso (20-50%)
        torso_y = y + head_h
        torso_h = int(h * 0.3)
        segments['torso'] = self._extract_region(image, x, torso_y, w, torso_h)

        # Arms (sides of torso region)
        arm_width = int(w * 0.25)
        segments['left_arm'] = self._extract_region(image, x, torso_y, arm_width, torso_h)
        segments['right_arm'] = self._extract_region(image, x + w - arm_width, torso_y, arm_width, torso_h)

        # Legs (bottom 50%)
        legs_y = torso_y + torso_h
        legs_h = h - head_h - torso_h
        leg_width = int(w * 0.4)
        segments['left_leg'] = self._extract_region(image, x, legs_y, leg_width, legs_h)
        segments['right_leg'] = self._extract_region(image, x + w - leg_width, legs_y, leg_width, legs_h)

        return segments

    def _extract_region(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> str:
        """Extract region from image and save to file."""
        region = image[y:y+h, x:x+w].copy()
        output_path = self._get_output_path()
        cv2.imwrite(output_path, region)
        return output_path

    def enhance_drawing(self, image_path: str) -> str:
        """
        Enhance drawing for better animation:
        - Clean up lines
        - Enhance contrast
        - Smooth edges
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # If has alpha, work with RGB only
        has_alpha = image.shape[2] == 4
        if has_alpha:
            alpha = image[:, :, 3]
            rgb = image[:, :, :3]
        else:
            rgb = image

        # Convert to grayscale for processing
        gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Smooth while preserving edges
        smooth = cv2.bilateralFilter(enhanced, 9, 75, 75)

        # Convert back to BGR
        result = cv2.cvtColor(smooth, cv2.COLOR_GRAY2BGR)

        # Restore alpha if present
        if has_alpha:
            result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = alpha

        output_path = self._get_output_path()
        cv2.imwrite(output_path, result)

        return output_path

    def create_silhouette(self, image_path: str, color: tuple = (0, 0, 0)) -> str:
        """Create a solid silhouette of the character."""
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None or image.shape[2] < 4:
            raise ValueError("Image must have alpha channel")

        # Get alpha mask
        alpha = image[:, :, 3]

        # Create solid color image
        silhouette = np.zeros_like(image)
        silhouette[:, :, 0] = color[0]  # B
        silhouette[:, :, 1] = color[1]  # G
        silhouette[:, :, 2] = color[2]  # R
        silhouette[:, :, 3] = alpha

        output_path = self._get_output_path()
        cv2.imwrite(output_path, silhouette)

        return output_path

    def resize_for_animation(self, image_path: str, max_size: int = 1024) -> str:
        """Resize image while maintaining aspect ratio."""
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        h, w = image.shape[:2]

        if max(h, w) <= max_size:
            return image_path

        # Calculate new size
        if h > w:
            new_h = max_size
            new_w = int(w * max_size / h)
        else:
            new_w = max_size
            new_h = int(h * max_size / w)

        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        output_path = self._get_output_path()
        cv2.imwrite(output_path, resized)

        return output_path
