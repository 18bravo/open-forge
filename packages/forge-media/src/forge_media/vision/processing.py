"""Image processing utilities."""

from __future__ import annotations

from enum import Enum
from io import BytesIO
from typing import Any


class ImageFormat(str, Enum):
    """Supported output image formats."""

    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"


class ResizeMode(str, Enum):
    """Image resize modes."""

    FIT = "fit"  # Fit within dimensions, maintain aspect ratio
    FILL = "fill"  # Fill dimensions, crop if necessary
    STRETCH = "stretch"  # Stretch to exact dimensions


class ImageProcessor:
    """
    Basic image processing operations.

    Provides common image operations like resizing, format conversion,
    and thumbnail generation.

    Example:
        ```python
        processor = ImageProcessor()

        # Resize an image
        resized = await processor.resize(image_bytes, 800, 600)

        # Generate a thumbnail
        thumb = await processor.thumbnail(image_bytes, 256, 256)

        # Convert format
        webp = await processor.convert(image_bytes, ImageFormat.WEBP)
        ```
    """

    async def resize(
        self,
        image: bytes,
        width: int,
        height: int,
        mode: ResizeMode = ResizeMode.FIT,
        format: ImageFormat = ImageFormat.JPEG,
        quality: int = 85,
    ) -> bytes:
        """
        Resize an image.

        Args:
            image: Raw image bytes
            width: Target width
            height: Target height
            mode: Resize mode (fit, fill, stretch)
            format: Output format
            quality: JPEG/WEBP quality (1-100)

        Returns:
            Resized image bytes
        """
        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError("pillow is required for image processing") from e

        img = Image.open(BytesIO(image))

        # Handle transparency for JPEG
        if format == ImageFormat.JPEG and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        if mode == ResizeMode.FIT:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        elif mode == ResizeMode.FILL:
            img = self._resize_and_crop(img, width, height)
        elif mode == ResizeMode.STRETCH:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        save_kwargs: dict[str, Any] = {"format": format.value.upper()}
        if format in (ImageFormat.JPEG, ImageFormat.WEBP):
            save_kwargs["quality"] = quality
        if format == ImageFormat.PNG:
            save_kwargs["optimize"] = True

        img.save(output, **save_kwargs)
        return output.getvalue()

    async def thumbnail(
        self,
        image: bytes,
        width: int,
        height: int,
        format: ImageFormat = ImageFormat.JPEG,
        quality: int = 85,
    ) -> bytes:
        """
        Generate a thumbnail image.

        Shortcut for resize with FIT mode.

        Args:
            image: Raw image bytes
            width: Maximum width
            height: Maximum height
            format: Output format
            quality: Output quality

        Returns:
            Thumbnail image bytes
        """
        return await self.resize(
            image,
            width,
            height,
            mode=ResizeMode.FIT,
            format=format,
            quality=quality,
        )

    async def convert(
        self,
        image: bytes,
        format: ImageFormat,
        quality: int = 85,
    ) -> bytes:
        """
        Convert image to a different format.

        Args:
            image: Raw image bytes
            format: Target format
            quality: Output quality (for JPEG/WEBP)

        Returns:
            Converted image bytes
        """
        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError("pillow is required for image processing") from e

        img = Image.open(BytesIO(image))

        # Handle transparency for JPEG
        if format == ImageFormat.JPEG and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output = BytesIO()
        save_kwargs: dict[str, Any] = {"format": format.value.upper()}
        if format in (ImageFormat.JPEG, ImageFormat.WEBP):
            save_kwargs["quality"] = quality

        img.save(output, **save_kwargs)
        return output.getvalue()

    async def get_dimensions(self, image: bytes) -> tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image: Raw image bytes

        Returns:
            Tuple of (width, height)
        """
        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError("pillow is required for image processing") from e

        img = Image.open(BytesIO(image))
        return img.size

    async def get_metadata(self, image: bytes) -> dict[str, Any]:
        """
        Extract image metadata (EXIF, etc.).

        Args:
            image: Raw image bytes

        Returns:
            Dictionary of metadata
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
        except ImportError as e:
            raise ImportError("pillow is required for image processing") from e

        img = Image.open(BytesIO(image))

        metadata: dict[str, Any] = {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
        }

        # Extract EXIF data if available
        if hasattr(img, "_getexif") and img._getexif():
            exif = img._getexif()
            exif_data = {}
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                # Only include serializable values
                if isinstance(value, (str, int, float, bool)):
                    exif_data[str(tag)] = value
            if exif_data:
                metadata["exif"] = exif_data

        return metadata

    def _resize_and_crop(self, img, target_width: int, target_height: int):
        """Resize and center-crop to fill exact dimensions."""
        from PIL import Image

        # Calculate ratios
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            # Image is wider - resize by height, crop width
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller - resize by width, crop height
            new_width = target_width
            new_height = int(new_width / img_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center crop
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        return img.crop((left, top, right, bottom))
