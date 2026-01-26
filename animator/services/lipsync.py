"""
Lip sync generation service.
Analyzes audio to generate phoneme timing for lip animation.
"""
import os
import json
from typing import List, Dict


class LipSyncGenerator:
    """
    Generates lip sync data from audio.
    Uses phoneme detection to create mouth shape timings.
    """

    # Standard viseme (mouth shape) mappings
    VISEME_MAP = {
        # Phoneme to viseme mapping
        'AA': 'open',      # father
        'AE': 'open',      # cat
        'AH': 'open',      # cut
        'AO': 'round',     # dog
        'AW': 'round',     # cow
        'AY': 'wide',      # hide
        'B': 'closed',     # be
        'CH': 'pursed',    # cheese
        'D': 'teeth',      # dee
        'DH': 'teeth',     # thee
        'EH': 'wide',      # red
        'ER': 'round',     # bird
        'EY': 'wide',      # ate
        'F': 'fv',         # fee
        'G': 'open',       # green
        'HH': 'open',      # he
        'IH': 'wide',      # it
        'IY': 'wide',      # eat
        'JH': 'pursed',    # gee
        'K': 'open',       # key
        'L': 'teeth',      # lee
        'M': 'closed',     # me
        'N': 'teeth',      # knee
        'NG': 'open',      # ping
        'OW': 'round',     # oat
        'OY': 'round',     # toy
        'P': 'closed',     # pee
        'R': 'pursed',     # read
        'S': 'teeth',      # sea
        'SH': 'pursed',    # she
        'T': 'teeth',      # tea
        'TH': 'teeth',     # theta
        'UH': 'round',     # hood
        'UW': 'round',     # too
        'V': 'fv',         # vee
        'W': 'round',      # we
        'Y': 'wide',       # yield
        'Z': 'teeth',      # zee
        'ZH': 'pursed',    # seizure
        'SIL': 'rest',     # silence
    }

    # Mouth shape descriptions for animation
    MOUTH_SHAPES = {
        'rest': {'openness': 0.0, 'width': 0.5, 'roundness': 0.0},
        'closed': {'openness': 0.0, 'width': 0.5, 'roundness': 0.0},
        'open': {'openness': 0.8, 'width': 0.6, 'roundness': 0.0},
        'wide': {'openness': 0.5, 'width': 0.9, 'roundness': 0.0},
        'round': {'openness': 0.6, 'width': 0.3, 'roundness': 0.9},
        'pursed': {'openness': 0.3, 'width': 0.2, 'roundness': 0.8},
        'teeth': {'openness': 0.2, 'width': 0.7, 'roundness': 0.0},
        'fv': {'openness': 0.1, 'width': 0.6, 'roundness': 0.0},
    }

    def __init__(self):
        self.aligner = None
        self._init_aligner()

    def _init_aligner(self):
        """Initialize forced aligner for phoneme detection."""
        try:
            # Try to use gentle or similar aligner
            pass
        except ImportError:
            pass

    def generate(self, audio_path: str) -> List[Dict]:
        """
        Generate lip sync data from audio.

        Args:
            audio_path: Path to audio file

        Returns:
            list: Phoneme timing data
        """
        if self.aligner:
            return self._generate_with_aligner(audio_path)
        else:
            return self._generate_from_amplitude(audio_path)

    def _generate_with_aligner(self, audio_path: str) -> List[Dict]:
        """Generate using forced alignment."""
        # Would use gentle, Montreal Forced Aligner, or similar
        # For now, fall back to amplitude-based
        return self._generate_from_amplitude(audio_path)

    def _generate_from_amplitude(self, audio_path: str) -> List[Dict]:
        """
        Generate lip sync from audio amplitude.
        Less accurate but works without transcription.
        """
        try:
            import numpy as np
            from scipy.io import wavfile

            sample_rate, audio_data = wavfile.read(audio_path)

            # Handle stereo
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)

            # Normalize
            audio_data = audio_data.astype(float) / np.max(np.abs(audio_data))

            # Calculate RMS energy in windows
            window_size = int(sample_rate * 0.05)  # 50ms windows
            hop_size = int(sample_rate * 0.02)  # 20ms hops

            phoneme_data = []
            current_time = 0

            for i in range(0, len(audio_data) - window_size, hop_size):
                window = audio_data[i:i + window_size]
                rms = np.sqrt(np.mean(window ** 2))

                # Map RMS to viseme
                if rms < 0.05:
                    viseme = 'rest'
                elif rms < 0.15:
                    viseme = 'closed'
                elif rms < 0.3:
                    viseme = 'teeth'
                elif rms < 0.5:
                    viseme = 'wide'
                else:
                    viseme = 'open'

                phoneme_data.append({
                    'time': current_time,
                    'duration': hop_size / sample_rate,
                    'phoneme': 'SIL' if viseme == 'rest' else 'AH',
                    'viseme': viseme,
                })

                current_time += hop_size / sample_rate

            # Smooth transitions
            phoneme_data = self._smooth_visemes(phoneme_data)

            return phoneme_data

        except ImportError:
            return self._generate_placeholder(audio_path)

    def _generate_placeholder(self, audio_path: str) -> List[Dict]:
        """Generate placeholder lip sync data."""
        # Try to get audio duration
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ], capture_output=True, text=True)
            duration = float(result.stdout.strip())
        except:
            duration = 5.0

        # Generate simple on/off pattern
        phoneme_data = []
        time = 0
        while time < duration:
            phoneme_data.append({
                'time': time,
                'duration': 0.2,
                'phoneme': 'AH',
                'viseme': 'open',
            })
            time += 0.2

            phoneme_data.append({
                'time': time,
                'duration': 0.1,
                'phoneme': 'SIL',
                'viseme': 'rest',
            })
            time += 0.1

        return phoneme_data

    def _smooth_visemes(self, phoneme_data: List[Dict]) -> List[Dict]:
        """Smooth viseme transitions."""
        if len(phoneme_data) < 3:
            return phoneme_data

        smoothed = [phoneme_data[0]]

        for i in range(1, len(phoneme_data) - 1):
            current = phoneme_data[i]
            prev_vis = phoneme_data[i - 1]['viseme']
            next_vis = phoneme_data[i + 1]['viseme']

            # If current is different from both neighbors and very short,
            # smooth it out
            if (current['viseme'] != prev_vis and
                current['viseme'] != next_vis and
                current['duration'] < 0.05):
                current = current.copy()
                current['viseme'] = prev_vis

            smoothed.append(current)

        smoothed.append(phoneme_data[-1])
        return smoothed

    def get_mouth_shape_mapping(self) -> Dict:
        """Get mouth shape definitions for rendering."""
        return self.MOUTH_SHAPES

    def get_viseme_at_time(self, phoneme_data: List[Dict], time: float) -> Dict:
        """Get the mouth shape at a specific time."""
        for i, p in enumerate(phoneme_data):
            if p['time'] <= time < p['time'] + p['duration']:
                return self.MOUTH_SHAPES.get(p['viseme'], self.MOUTH_SHAPES['rest'])

        return self.MOUTH_SHAPES['rest']

    def interpolate_shapes(self, shape1: Dict, shape2: Dict, t: float) -> Dict:
        """Interpolate between two mouth shapes."""
        return {
            'openness': shape1['openness'] * (1 - t) + shape2['openness'] * t,
            'width': shape1['width'] * (1 - t) + shape2['width'] * t,
            'roundness': shape1['roundness'] * (1 - t) + shape2['roundness'] * t,
        }
