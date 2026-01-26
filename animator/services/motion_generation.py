"""
Motion generation service using open source models.
Generates animation data from text prompts or motion capture data.
"""
import numpy as np
import json
import os
from typing import Optional


class MotionGenerator:
    """
    Generates motion data for character animation.
    Can use:
    - Pre-defined motion patterns
    - Motion diffusion models (MDM, MotionDiffuse)
    - BVH motion capture files
    """

    # Pre-defined motion patterns
    PRESET_MOTIONS = {
        'walk': {
            'type': 'locomotion',
            'loop': True,
            'duration': 1.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'walk_contact_left'},
                {'time': 0.25, 'pose': 'walk_pass_left'},
                {'time': 0.5, 'pose': 'walk_contact_right'},
                {'time': 0.75, 'pose': 'walk_pass_right'},
                {'time': 1.0, 'pose': 'walk_contact_left'},
            ]
        },
        'run': {
            'type': 'locomotion',
            'loop': True,
            'duration': 0.6,
            'keyframes': [
                {'time': 0.0, 'pose': 'run_flight_left'},
                {'time': 0.15, 'pose': 'run_contact_left'},
                {'time': 0.3, 'pose': 'run_flight_right'},
                {'time': 0.45, 'pose': 'run_contact_right'},
                {'time': 0.6, 'pose': 'run_flight_left'},
            ]
        },
        'jump': {
            'type': 'action',
            'loop': False,
            'duration': 1.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'jump_prepare'},
                {'time': 0.2, 'pose': 'jump_takeoff'},
                {'time': 0.5, 'pose': 'jump_peak'},
                {'time': 0.8, 'pose': 'jump_land'},
                {'time': 1.0, 'pose': 'jump_recover'},
            ]
        },
        'wave': {
            'type': 'gesture',
            'loop': False,
            'duration': 2.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'idle'},
                {'time': 0.3, 'pose': 'wave_up'},
                {'time': 0.5, 'pose': 'wave_right'},
                {'time': 0.7, 'pose': 'wave_left'},
                {'time': 0.9, 'pose': 'wave_right'},
                {'time': 1.1, 'pose': 'wave_left'},
                {'time': 1.5, 'pose': 'wave_down'},
                {'time': 2.0, 'pose': 'idle'},
            ]
        },
        'dance': {
            'type': 'dance',
            'loop': True,
            'duration': 2.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'dance_idle'},
                {'time': 0.25, 'pose': 'dance_left'},
                {'time': 0.5, 'pose': 'dance_center'},
                {'time': 0.75, 'pose': 'dance_right'},
                {'time': 1.0, 'pose': 'dance_center'},
                {'time': 1.25, 'pose': 'dance_jump'},
                {'time': 1.5, 'pose': 'dance_land'},
                {'time': 2.0, 'pose': 'dance_idle'},
            ]
        },
        'idle': {
            'type': 'idle',
            'loop': True,
            'duration': 3.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'idle_breathe_in'},
                {'time': 1.5, 'pose': 'idle_breathe_out'},
                {'time': 3.0, 'pose': 'idle_breathe_in'},
            ]
        },
        'sit': {
            'type': 'action',
            'loop': False,
            'duration': 1.5,
            'keyframes': [
                {'time': 0.0, 'pose': 'standing'},
                {'time': 0.5, 'pose': 'sitting_down'},
                {'time': 1.0, 'pose': 'seated'},
                {'time': 1.5, 'pose': 'seated_relaxed'},
            ]
        },
        'punch': {
            'type': 'action',
            'loop': False,
            'duration': 0.5,
            'keyframes': [
                {'time': 0.0, 'pose': 'punch_ready'},
                {'time': 0.15, 'pose': 'punch_wind'},
                {'time': 0.25, 'pose': 'punch_extend'},
                {'time': 0.35, 'pose': 'punch_impact'},
                {'time': 0.5, 'pose': 'punch_recover'},
            ]
        },
        'kick': {
            'type': 'action',
            'loop': False,
            'duration': 0.7,
            'keyframes': [
                {'time': 0.0, 'pose': 'kick_ready'},
                {'time': 0.2, 'pose': 'kick_raise'},
                {'time': 0.35, 'pose': 'kick_extend'},
                {'time': 0.45, 'pose': 'kick_impact'},
                {'time': 0.7, 'pose': 'kick_recover'},
            ]
        },
        'bow': {
            'type': 'gesture',
            'loop': False,
            'duration': 2.0,
            'keyframes': [
                {'time': 0.0, 'pose': 'standing'},
                {'time': 0.5, 'pose': 'bow_down'},
                {'time': 1.0, 'pose': 'bow_hold'},
                {'time': 1.5, 'pose': 'bow_up'},
                {'time': 2.0, 'pose': 'standing'},
            ]
        },
    }

    # Pose definitions (joint angles relative to rest pose)
    POSE_LIBRARY = {
        'idle': {
            'left_shoulder': {'rotation': 0},
            'right_shoulder': {'rotation': 0},
            'left_elbow': {'rotation': 0},
            'right_elbow': {'rotation': 0},
            'left_hip': {'rotation': 0},
            'right_hip': {'rotation': 0},
            'left_knee': {'rotation': 0},
            'right_knee': {'rotation': 0},
            'spine': {'rotation': 0},
            'head': {'rotation': 0},
        },
        'walk_contact_left': {
            'left_shoulder': {'rotation': -20},
            'right_shoulder': {'rotation': 20},
            'left_hip': {'rotation': 30},
            'right_hip': {'rotation': -15},
            'left_knee': {'rotation': 0},
            'right_knee': {'rotation': 30},
        },
        'walk_pass_left': {
            'left_shoulder': {'rotation': 0},
            'right_shoulder': {'rotation': 0},
            'left_hip': {'rotation': 0},
            'right_hip': {'rotation': 0},
            'left_knee': {'rotation': 45},
            'right_knee': {'rotation': 0},
        },
        'walk_contact_right': {
            'left_shoulder': {'rotation': 20},
            'right_shoulder': {'rotation': -20},
            'left_hip': {'rotation': -15},
            'right_hip': {'rotation': 30},
            'left_knee': {'rotation': 30},
            'right_knee': {'rotation': 0},
        },
        'walk_pass_right': {
            'left_shoulder': {'rotation': 0},
            'right_shoulder': {'rotation': 0},
            'left_hip': {'rotation': 0},
            'right_hip': {'rotation': 0},
            'left_knee': {'rotation': 0},
            'right_knee': {'rotation': 45},
        },
        'wave_up': {
            'right_shoulder': {'rotation': -150},
            'right_elbow': {'rotation': 45},
        },
        'wave_left': {
            'right_shoulder': {'rotation': -150},
            'right_elbow': {'rotation': 30},
            'right_wrist': {'rotation': -20},
        },
        'wave_right': {
            'right_shoulder': {'rotation': -150},
            'right_elbow': {'rotation': 30},
            'right_wrist': {'rotation': 20},
        },
        'wave_down': {
            'right_shoulder': {'rotation': -90},
            'right_elbow': {'rotation': 20},
        },
        'jump_prepare': {
            'left_hip': {'rotation': 30},
            'right_hip': {'rotation': 30},
            'left_knee': {'rotation': 60},
            'right_knee': {'rotation': 60},
            'spine': {'rotation': 15},
        },
        'jump_takeoff': {
            'left_hip': {'rotation': -20},
            'right_hip': {'rotation': -20},
            'left_knee': {'rotation': 0},
            'right_knee': {'rotation': 0},
            'left_shoulder': {'rotation': -45},
            'right_shoulder': {'rotation': -45},
        },
        'jump_peak': {
            'left_hip': {'rotation': 15},
            'right_hip': {'rotation': 15},
            'left_knee': {'rotation': 30},
            'right_knee': {'rotation': 30},
            'left_shoulder': {'rotation': -90},
            'right_shoulder': {'rotation': -90},
        },
        'jump_land': {
            'left_hip': {'rotation': 45},
            'right_hip': {'rotation': 45},
            'left_knee': {'rotation': 90},
            'right_knee': {'rotation': 90},
            'spine': {'rotation': 20},
        },
        'jump_recover': {
            'left_hip': {'rotation': 15},
            'right_hip': {'rotation': 15},
            'left_knee': {'rotation': 30},
            'right_knee': {'rotation': 30},
        },
    }

    def __init__(self):
        self.mdm_model = None
        self._init_models()

    def _init_models(self):
        """Initialize motion diffusion model if available"""
        try:
            # Try to load motion diffusion model
            # This would be MDM or MotionDiffuse in production
            pass
        except Exception:
            pass

    def generate_from_prompt(self, prompt: str, character_type: str = 'humanoid',
                            rig_data: Optional[dict] = None) -> dict:
        """
        Generate motion from text prompt.

        Args:
            prompt: Text description of desired motion (e.g., "walk forward", "wave hello")
            character_type: Type of character ('humanoid', 'quadruped', etc.)
            rig_data: Character's rig data for joint mapping

        Returns:
            dict: Motion data with keyframes
        """
        # Normalize prompt
        prompt_lower = prompt.lower().strip()

        # Try to match to preset motion
        motion = self._match_preset(prompt_lower)

        if motion:
            return self._expand_motion(motion, rig_data)

        # If no preset match, try AI generation
        if self.mdm_model:
            return self._generate_with_mdm(prompt, character_type, rig_data)

        # Fallback: Generate procedural motion based on keywords
        return self._generate_procedural(prompt_lower, character_type, rig_data)

    def _match_preset(self, prompt: str) -> Optional[dict]:
        """Match prompt to preset motion."""
        keywords = {
            'walk': 'walk',
            'walking': 'walk',
            'run': 'run',
            'running': 'run',
            'jump': 'jump',
            'jumping': 'jump',
            'wave': 'wave',
            'waving': 'wave',
            'hello': 'wave',
            'dance': 'dance',
            'dancing': 'dance',
            'idle': 'idle',
            'stand': 'idle',
            'standing': 'idle',
            'sit': 'sit',
            'sitting': 'sit',
            'punch': 'punch',
            'punching': 'punch',
            'kick': 'kick',
            'kicking': 'kick',
            'bow': 'bow',
            'bowing': 'bow',
        }

        for keyword, motion_name in keywords.items():
            if keyword in prompt:
                if motion_name in self.PRESET_MOTIONS:
                    return self.PRESET_MOTIONS[motion_name].copy()

        return None

    def _expand_motion(self, motion: dict, rig_data: Optional[dict]) -> dict:
        """Expand motion keyframes with full pose data."""
        expanded_keyframes = []

        for kf in motion.get('keyframes', []):
            pose_name = kf.get('pose', 'idle')
            pose_data = self.POSE_LIBRARY.get(pose_name, self.POSE_LIBRARY['idle'])

            expanded_kf = {
                'time': kf['time'],
                'joints': {}
            }

            # Copy pose data for each joint
            for joint_name, joint_data in pose_data.items():
                expanded_kf['joints'][joint_name] = joint_data.copy()

            expanded_keyframes.append(expanded_kf)

        return {
            'type': motion.get('type', 'custom'),
            'loop': motion.get('loop', False),
            'duration': motion.get('duration', 1.0),
            'keyframes': expanded_keyframes,
            'interpolation': 'smooth',
        }

    def _generate_with_mdm(self, prompt: str, character_type: str,
                          rig_data: Optional[dict]) -> dict:
        """Generate motion using Motion Diffusion Model."""
        # In production, this would use a real MDM model
        # For now, return a placeholder
        return self._generate_procedural(prompt, character_type, rig_data)

    def _generate_procedural(self, prompt: str, character_type: str,
                            rig_data: Optional[dict]) -> dict:
        """Generate procedural motion based on prompt analysis."""
        # Default gentle motion
        keyframes = [
            {
                'time': 0.0,
                'joints': {
                    'left_shoulder': {'rotation': 0},
                    'right_shoulder': {'rotation': 0},
                    'spine': {'rotation': 0},
                }
            },
            {
                'time': 1.0,
                'joints': {
                    'left_shoulder': {'rotation': 5},
                    'right_shoulder': {'rotation': -5},
                    'spine': {'rotation': 2},
                }
            },
            {
                'time': 2.0,
                'joints': {
                    'left_shoulder': {'rotation': 0},
                    'right_shoulder': {'rotation': 0},
                    'spine': {'rotation': 0},
                }
            },
        ]

        return {
            'type': 'custom',
            'loop': True,
            'duration': 2.0,
            'keyframes': keyframes,
            'interpolation': 'smooth',
            'generated_from': prompt,
        }

    def load_bvh(self, bvh_path: str) -> dict:
        """
        Load motion from BVH file.

        Args:
            bvh_path: Path to BVH motion capture file

        Returns:
            dict: Motion data
        """
        # Parse BVH file
        with open(bvh_path, 'r') as f:
            bvh_content = f.read()

        # Simple BVH parser (production would use a proper library)
        lines = bvh_content.split('\n')
        motion_data = {
            'type': 'mocap',
            'loop': False,
            'keyframes': [],
            'source': 'bvh',
        }

        # Find MOTION section
        in_motion = False
        frame_time = 0.033  # Default 30fps
        frame_count = 0
        current_frame = 0

        for line in lines:
            line = line.strip()

            if line == 'MOTION':
                in_motion = True
                continue

            if in_motion:
                if line.startswith('Frames:'):
                    frame_count = int(line.split(':')[1].strip())
                elif line.startswith('Frame Time:'):
                    frame_time = float(line.split(':')[1].strip())
                elif line and not line.startswith('Frames') and not line.startswith('Frame'):
                    # Parse motion data
                    values = [float(v) for v in line.split()]
                    if values:
                        kf = {
                            'time': current_frame * frame_time,
                            'raw_values': values,
                        }
                        motion_data['keyframes'].append(kf)
                        current_frame += 1

        motion_data['duration'] = current_frame * frame_time
        motion_data['frame_rate'] = 1.0 / frame_time if frame_time > 0 else 30

        return motion_data

    def retarget_motion(self, motion_data: dict, source_rig: dict,
                       target_rig: dict) -> dict:
        """
        Retarget motion from one rig to another.

        Args:
            motion_data: Original motion data
            source_rig: Source character rig
            target_rig: Target character rig

        Returns:
            dict: Retargeted motion data
        """
        # Simple retargeting: scale positions based on rig proportions
        retargeted = motion_data.copy()
        retargeted['keyframes'] = []

        # Calculate scale factors
        source_height = self._estimate_rig_height(source_rig)
        target_height = self._estimate_rig_height(target_rig)
        scale = target_height / source_height if source_height > 0 else 1.0

        for kf in motion_data.get('keyframes', []):
            new_kf = {
                'time': kf['time'],
                'joints': {}
            }

            for joint_name, joint_data in kf.get('joints', {}).items():
                new_joint = joint_data.copy()
                # Rotations don't need scaling
                # Positions would need scaling by the factor
                if 'position' in new_joint:
                    new_joint['position'] = {
                        'x': new_joint['position']['x'] * scale,
                        'y': new_joint['position']['y'] * scale,
                    }
                new_kf['joints'][joint_name] = new_joint

            retargeted['keyframes'].append(new_kf)

        return retargeted

    def _estimate_rig_height(self, rig: dict) -> float:
        """Estimate character height from rig data."""
        joints = rig.get('joints', {})

        if 'head_top' in joints and 'left_ankle' in joints:
            head = joints['head_top']
            ankle = joints['left_ankle']
            return abs(head.get('y', 0) - ankle.get('y', 0))

        return 500  # Default height
