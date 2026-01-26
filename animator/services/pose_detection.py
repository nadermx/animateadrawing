"""
Pose detection service using open source models.
Uses MediaPipe for fast pose detection or OpenPose for more accuracy.
"""
import cv2
import numpy as np
from PIL import Image
import json


class PoseDetector:
    """
    Detects human pose from drawings and creates rig data.
    Uses MediaPipe Pose for real-time detection.
    """

    # Standard skeleton joints for humanoid rig
    HUMANOID_JOINTS = [
        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
        'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
        'neck', 'head_top', 'pelvis',
    ]

    # Bone connections for humanoid
    HUMANOID_BONES = [
        ('head_top', 'nose'),
        ('nose', 'neck'),
        ('neck', 'left_shoulder'),
        ('neck', 'right_shoulder'),
        ('left_shoulder', 'left_elbow'),
        ('right_shoulder', 'right_elbow'),
        ('left_elbow', 'left_wrist'),
        ('right_elbow', 'right_wrist'),
        ('neck', 'pelvis'),
        ('pelvis', 'left_hip'),
        ('pelvis', 'right_hip'),
        ('left_hip', 'left_knee'),
        ('right_hip', 'right_knee'),
        ('left_knee', 'left_ankle'),
        ('right_knee', 'right_ankle'),
    ]

    def __init__(self):
        self.mp_pose = None
        self.pose = None
        self._init_mediapipe()

    def _init_mediapipe(self):
        """Initialize MediaPipe pose detector"""
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.5
            )
        except ImportError:
            print("MediaPipe not available, using fallback detection")

    def detect(self, image_path: str) -> dict:
        """
        Detect pose from image and return rig data.

        Args:
            image_path: Path to the character image

        Returns:
            dict: Rig data with joints and bones
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        height, width = image.shape[:2]

        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        joints = {}

        if self.pose:
            # Use MediaPipe for detection
            results = self.pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Map MediaPipe landmarks to our joint names
                landmark_mapping = {
                    0: 'nose',
                    2: 'left_eye',
                    5: 'right_eye',
                    7: 'left_ear',
                    8: 'right_ear',
                    11: 'left_shoulder',
                    12: 'right_shoulder',
                    13: 'left_elbow',
                    14: 'right_elbow',
                    15: 'left_wrist',
                    16: 'right_wrist',
                    23: 'left_hip',
                    24: 'right_hip',
                    25: 'left_knee',
                    26: 'right_knee',
                    27: 'left_ankle',
                    28: 'right_ankle',
                }

                for idx, joint_name in landmark_mapping.items():
                    if idx < len(landmarks):
                        landmark = landmarks[idx]
                        joints[joint_name] = {
                            'x': landmark.x * width,
                            'y': landmark.y * height,
                            'visibility': landmark.visibility
                        }

                # Calculate derived joints
                if 'left_shoulder' in joints and 'right_shoulder' in joints:
                    joints['neck'] = {
                        'x': (joints['left_shoulder']['x'] + joints['right_shoulder']['x']) / 2,
                        'y': (joints['left_shoulder']['y'] + joints['right_shoulder']['y']) / 2 - 20,
                        'visibility': 1.0
                    }

                if 'left_hip' in joints and 'right_hip' in joints:
                    joints['pelvis'] = {
                        'x': (joints['left_hip']['x'] + joints['right_hip']['x']) / 2,
                        'y': (joints['left_hip']['y'] + joints['right_hip']['y']) / 2,
                        'visibility': 1.0
                    }

                if 'nose' in joints:
                    joints['head_top'] = {
                        'x': joints['nose']['x'],
                        'y': joints['nose']['y'] - 50,
                        'visibility': 1.0
                    }
        else:
            # Fallback: estimate pose from image contours
            joints = self._fallback_detection(image)

        # Build rig data
        rig_data = {
            'joints': joints,
            'bones': self.HUMANOID_BONES,
            'image_size': {'width': width, 'height': height},
            'character_type': 'humanoid',
            'detection_method': 'mediapipe' if self.pose else 'contour'
        }

        return rig_data

    def _fallback_detection(self, image: np.ndarray) -> dict:
        """
        Fallback pose detection using contour analysis.
        Used when MediaPipe is not available.
        """
        height, width = image.shape[:2]

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            # Return default centered pose
            return self._get_default_pose(width, height)

        # Get the largest contour (assume it's the character)
        largest_contour = max(contours, key=cv2.contourArea)

        # Get bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Estimate joints based on typical human proportions
        center_x = x + w / 2

        joints = {
            'head_top': {'x': center_x, 'y': y, 'visibility': 0.8},
            'nose': {'x': center_x, 'y': y + h * 0.1, 'visibility': 0.8},
            'neck': {'x': center_x, 'y': y + h * 0.15, 'visibility': 0.8},
            'left_shoulder': {'x': center_x - w * 0.2, 'y': y + h * 0.2, 'visibility': 0.8},
            'right_shoulder': {'x': center_x + w * 0.2, 'y': y + h * 0.2, 'visibility': 0.8},
            'left_elbow': {'x': center_x - w * 0.3, 'y': y + h * 0.35, 'visibility': 0.8},
            'right_elbow': {'x': center_x + w * 0.3, 'y': y + h * 0.35, 'visibility': 0.8},
            'left_wrist': {'x': center_x - w * 0.35, 'y': y + h * 0.5, 'visibility': 0.8},
            'right_wrist': {'x': center_x + w * 0.35, 'y': y + h * 0.5, 'visibility': 0.8},
            'pelvis': {'x': center_x, 'y': y + h * 0.5, 'visibility': 0.8},
            'left_hip': {'x': center_x - w * 0.1, 'y': y + h * 0.55, 'visibility': 0.8},
            'right_hip': {'x': center_x + w * 0.1, 'y': y + h * 0.55, 'visibility': 0.8},
            'left_knee': {'x': center_x - w * 0.1, 'y': y + h * 0.75, 'visibility': 0.8},
            'right_knee': {'x': center_x + w * 0.1, 'y': y + h * 0.75, 'visibility': 0.8},
            'left_ankle': {'x': center_x - w * 0.1, 'y': y + h * 0.95, 'visibility': 0.8},
            'right_ankle': {'x': center_x + w * 0.1, 'y': y + h * 0.95, 'visibility': 0.8},
        }

        return joints

    def _get_default_pose(self, width: int, height: int) -> dict:
        """Get a default T-pose centered in the image."""
        center_x = width / 2
        center_y = height / 2

        return {
            'head_top': {'x': center_x, 'y': center_y - 150, 'visibility': 0.5},
            'nose': {'x': center_x, 'y': center_y - 120, 'visibility': 0.5},
            'neck': {'x': center_x, 'y': center_y - 80, 'visibility': 0.5},
            'left_shoulder': {'x': center_x - 60, 'y': center_y - 60, 'visibility': 0.5},
            'right_shoulder': {'x': center_x + 60, 'y': center_y - 60, 'visibility': 0.5},
            'left_elbow': {'x': center_x - 120, 'y': center_y - 60, 'visibility': 0.5},
            'right_elbow': {'x': center_x + 120, 'y': center_y - 60, 'visibility': 0.5},
            'left_wrist': {'x': center_x - 180, 'y': center_y - 60, 'visibility': 0.5},
            'right_wrist': {'x': center_x + 180, 'y': center_y - 60, 'visibility': 0.5},
            'pelvis': {'x': center_x, 'y': center_y + 20, 'visibility': 0.5},
            'left_hip': {'x': center_x - 40, 'y': center_y + 40, 'visibility': 0.5},
            'right_hip': {'x': center_x + 40, 'y': center_y + 40, 'visibility': 0.5},
            'left_knee': {'x': center_x - 40, 'y': center_y + 100, 'visibility': 0.5},
            'right_knee': {'x': center_x + 40, 'y': center_y + 100, 'visibility': 0.5},
            'left_ankle': {'x': center_x - 40, 'y': center_y + 150, 'visibility': 0.5},
            'right_ankle': {'x': center_x + 40, 'y': center_y + 150, 'visibility': 0.5},
        }

    def detect_quadruped(self, image_path: str) -> dict:
        """Detect pose for four-legged animals."""
        image = cv2.imread(image_path)
        height, width = image.shape[:2]

        # For quadrupeds, use contour-based detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return self._get_default_quadruped_pose(width, height)

        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Quadruped joints
        joints = {
            'head': {'x': x + w * 0.9, 'y': y + h * 0.3, 'visibility': 0.8},
            'neck': {'x': x + w * 0.75, 'y': y + h * 0.35, 'visibility': 0.8},
            'spine_front': {'x': x + w * 0.6, 'y': y + h * 0.4, 'visibility': 0.8},
            'spine_mid': {'x': x + w * 0.4, 'y': y + h * 0.4, 'visibility': 0.8},
            'spine_back': {'x': x + w * 0.2, 'y': y + h * 0.4, 'visibility': 0.8},
            'tail': {'x': x + w * 0.05, 'y': y + h * 0.35, 'visibility': 0.8},
            'front_left_shoulder': {'x': x + w * 0.65, 'y': y + h * 0.5, 'visibility': 0.8},
            'front_left_knee': {'x': x + w * 0.65, 'y': y + h * 0.7, 'visibility': 0.8},
            'front_left_foot': {'x': x + w * 0.65, 'y': y + h * 0.95, 'visibility': 0.8},
            'front_right_shoulder': {'x': x + w * 0.55, 'y': y + h * 0.5, 'visibility': 0.8},
            'front_right_knee': {'x': x + w * 0.55, 'y': y + h * 0.7, 'visibility': 0.8},
            'front_right_foot': {'x': x + w * 0.55, 'y': y + h * 0.95, 'visibility': 0.8},
            'back_left_hip': {'x': x + w * 0.25, 'y': y + h * 0.5, 'visibility': 0.8},
            'back_left_knee': {'x': x + w * 0.25, 'y': y + h * 0.7, 'visibility': 0.8},
            'back_left_foot': {'x': x + w * 0.25, 'y': y + h * 0.95, 'visibility': 0.8},
            'back_right_hip': {'x': x + w * 0.15, 'y': y + h * 0.5, 'visibility': 0.8},
            'back_right_knee': {'x': x + w * 0.15, 'y': y + h * 0.7, 'visibility': 0.8},
            'back_right_foot': {'x': x + w * 0.15, 'y': y + h * 0.95, 'visibility': 0.8},
        }

        bones = [
            ('head', 'neck'),
            ('neck', 'spine_front'),
            ('spine_front', 'spine_mid'),
            ('spine_mid', 'spine_back'),
            ('spine_back', 'tail'),
            ('spine_front', 'front_left_shoulder'),
            ('spine_front', 'front_right_shoulder'),
            ('front_left_shoulder', 'front_left_knee'),
            ('front_left_knee', 'front_left_foot'),
            ('front_right_shoulder', 'front_right_knee'),
            ('front_right_knee', 'front_right_foot'),
            ('spine_back', 'back_left_hip'),
            ('spine_back', 'back_right_hip'),
            ('back_left_hip', 'back_left_knee'),
            ('back_left_knee', 'back_left_foot'),
            ('back_right_hip', 'back_right_knee'),
            ('back_right_knee', 'back_right_foot'),
        ]

        return {
            'joints': joints,
            'bones': bones,
            'image_size': {'width': width, 'height': height},
            'character_type': 'quadruped',
            'detection_method': 'contour'
        }

    def _get_default_quadruped_pose(self, width: int, height: int) -> dict:
        """Get default quadruped pose."""
        return {
            'joints': {},
            'bones': [],
            'image_size': {'width': width, 'height': height},
            'character_type': 'quadruped',
            'detection_method': 'default'
        }
