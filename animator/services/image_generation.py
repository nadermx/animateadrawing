"""
Image generation service for backgrounds using Stable Diffusion.
"""
import os
import uuid
from django.conf import settings


class ImageGenerator:
    """
    Generates images using AI models (Stable Diffusion).
    Used for creating backgrounds, props, and effects.
    """

    def __init__(self):
        self.pipe = None
        self._init_model()

    def _init_model(self):
        """Initialize Stable Diffusion pipeline."""
        try:
            from diffusers import StableDiffusionPipeline
            import torch

            # Use a lightweight model
            model_id = "runwayml/stable-diffusion-v1-5"

            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )

            if torch.cuda.is_available():
                self.pipe = self.pipe.to("cuda")
            else:
                # Use CPU with reduced memory
                self.pipe.enable_attention_slicing()

        except ImportError:
            print("Diffusers not available, image generation disabled")
        except Exception as e:
            print(f"Error initializing Stable Diffusion: {e}")

    def generate_background(self, prompt: str, width: int = 1920,
                           height: int = 1080) -> str:
        """
        Generate a background image from text prompt.

        Args:
            prompt: Description of desired background
            width: Output width
            height: Output height

        Returns:
            str: Path to generated image
        """
        output_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'bg_{uuid.uuid4()}.png')

        if self.pipe:
            return self._generate_with_sd(prompt, width, height, output_path)
        else:
            return self._generate_placeholder(prompt, width, height, output_path)

    def _generate_with_sd(self, prompt: str, width: int, height: int,
                         output_path: str) -> str:
        """Generate using Stable Diffusion."""
        # Enhance prompt for backgrounds
        enhanced_prompt = f"high quality background for animation, {prompt}, professional, detailed"
        negative_prompt = "text, watermark, signature, blurry, low quality, people, characters"

        # Generate at smaller size then upscale
        gen_width = min(width, 768)
        gen_height = min(height, 512)

        # Maintain aspect ratio
        aspect_ratio = width / height
        if gen_width / gen_height > aspect_ratio:
            gen_width = int(gen_height * aspect_ratio)
        else:
            gen_height = int(gen_width / aspect_ratio)

        # Make divisible by 8
        gen_width = (gen_width // 8) * 8
        gen_height = (gen_height // 8) * 8

        image = self.pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            width=gen_width,
            height=gen_height,
            num_inference_steps=30,
        ).images[0]

        # Upscale if needed
        if gen_width != width or gen_height != height:
            image = image.resize((width, height), resample=3)  # LANCZOS

        image.save(output_path)
        return output_path

    def _generate_placeholder(self, prompt: str, width: int, height: int,
                             output_path: str) -> str:
        """Generate a placeholder gradient background."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import hashlib

            # Generate colors from prompt
            hash_bytes = hashlib.md5(prompt.encode()).digest()
            color1 = (hash_bytes[0], hash_bytes[1], hash_bytes[2])
            color2 = (hash_bytes[3], hash_bytes[4], hash_bytes[5])

            # Create gradient
            image = Image.new('RGB', (width, height))
            for y in range(height):
                r = int(color1[0] + (color2[0] - color1[0]) * y / height)
                g = int(color1[1] + (color2[1] - color1[1]) * y / height)
                b = int(color1[2] + (color2[2] - color1[2]) * y / height)
                for x in range(width):
                    image.putpixel((x, y), (r, g, b))

            image.save(output_path)

        except ImportError:
            # Create minimal PNG
            import struct
            import zlib

            def create_png(width, height, color):
                def png_chunk(chunk_type, data):
                    chunk_len = struct.pack('>I', len(data))
                    chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
                    return chunk_len + chunk_type + data + chunk_crc

                # IHDR
                ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

                # IDAT
                raw_data = b''
                for y in range(height):
                    raw_data += b'\x00'  # Filter byte
                    for x in range(width):
                        raw_data += bytes(color)

                compressed = zlib.compress(raw_data)

                # Build PNG
                png_data = b'\x89PNG\r\n\x1a\n'
                png_data += png_chunk(b'IHDR', ihdr)
                png_data += png_chunk(b'IDAT', compressed)
                png_data += png_chunk(b'IEND', b'')

                return png_data

            png_bytes = create_png(width, height, (200, 200, 220))

            with open(output_path, 'wb') as f:
                f.write(png_bytes)

        return output_path

    def generate_prop(self, prompt: str, size: int = 256) -> str:
        """Generate a prop/object image with transparent background."""
        output_dir = os.path.join(settings.MEDIA_ROOT, 'temp', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'prop_{uuid.uuid4()}.png')

        if self.pipe:
            enhanced_prompt = f"single {prompt}, isolated on white background, cartoon style, clean"
            image = self.pipe(
                prompt=enhanced_prompt,
                negative_prompt="background, multiple objects, text",
                width=size,
                height=size,
                num_inference_steps=25,
            ).images[0]

            image.save(output_path)
        else:
            self._generate_placeholder(prompt, size, size, output_path)

        return output_path
