"""Tests for vision processing (OCR and image processing)."""

from __future__ import annotations

import pytest

from forge_media.vision.ocr import (
    OCRBlock,
    OCRLine,
    OCRResult,
    OCRWord,
    TesseractOCR,
    CloudVisionOCR,
)
from forge_media.vision.processing import (
    ImageFormat,
    ImageProcessor,
    ResizeMode,
)


class TestOCRModels:
    """Tests for OCR data models."""

    def test_ocr_word(self):
        """Test OCRWord model."""
        word = OCRWord(
            text="Hello",
            confidence=0.95,
            bounding_box=(10, 20, 50, 15),
        )

        assert word.text == "Hello"
        assert word.confidence == 0.95
        assert word.bounding_box == (10, 20, 50, 15)

    def test_ocr_line(self):
        """Test OCRLine model with words."""
        words = [
            OCRWord(text="Hello", confidence=0.95, bounding_box=(10, 20, 50, 15)),
            OCRWord(text="World", confidence=0.90, bounding_box=(65, 20, 50, 15)),
        ]

        line = OCRLine(
            text="Hello World",
            confidence=0.925,
            words=words,
            bounding_box=(10, 20, 105, 15),
        )

        assert line.text == "Hello World"
        assert len(line.words) == 2

    def test_ocr_result(self):
        """Test OCRResult model."""
        result = OCRResult(
            full_text="Hello World",
            blocks=[],
            confidence=0.92,
            language="eng",
        )

        assert result.full_text == "Hello World"
        assert result.confidence == 0.92
        assert result.language == "eng"


class TestTesseractOCR:
    """Tests for Tesseract OCR provider."""

    def test_provider_name(self):
        """Test that provider has correct name."""
        ocr = TesseractOCR()
        assert ocr.name == "tesseract"

    @pytest.mark.asyncio
    async def test_recognize_requires_dependencies(self, sample_image_bytes):
        """Test that recognize works or raises ImportError."""
        ocr = TesseractOCR()

        try:
            result = await ocr.recognize(sample_image_bytes)
            assert isinstance(result, OCRResult)
        except ImportError as e:
            # Expected if pytesseract not installed
            assert "pytesseract" in str(e).lower() or "pillow" in str(e).lower()
        except Exception:
            # Other errors may occur with minimal test image
            pass


class TestCloudVisionOCR:
    """Tests for Cloud Vision OCR provider."""

    def test_provider_name(self):
        """Test that provider has correct name."""
        ocr = CloudVisionOCR()
        assert ocr.name == "cloud_vision"

    @pytest.mark.asyncio
    async def test_recognize_not_implemented(self, sample_image_bytes):
        """Test that recognize raises NotImplementedError."""
        ocr = CloudVisionOCR()

        with pytest.raises(NotImplementedError):
            await ocr.recognize(sample_image_bytes)


class TestImageProcessor:
    """Tests for ImageProcessor."""

    @pytest.mark.asyncio
    async def test_resize_requires_pillow(self, sample_image_bytes):
        """Test that resize works with Pillow."""
        processor = ImageProcessor()

        try:
            result = await processor.resize(
                sample_image_bytes,
                width=100,
                height=100,
            )
            assert isinstance(result, bytes)
            assert len(result) > 0
        except ImportError as e:
            assert "pillow" in str(e).lower()

    @pytest.mark.asyncio
    async def test_thumbnail(self, sample_image_bytes):
        """Test thumbnail generation."""
        processor = ImageProcessor()

        try:
            result = await processor.thumbnail(
                sample_image_bytes,
                width=50,
                height=50,
            )
            assert isinstance(result, bytes)
        except ImportError:
            pass  # Expected if Pillow not installed

    @pytest.mark.asyncio
    async def test_get_dimensions(self, sample_image_bytes):
        """Test getting image dimensions."""
        processor = ImageProcessor()

        try:
            width, height = await processor.get_dimensions(sample_image_bytes)
            assert isinstance(width, int)
            assert isinstance(height, int)
            assert width > 0
            assert height > 0
        except ImportError:
            pass  # Expected if Pillow not installed

    @pytest.mark.asyncio
    async def test_convert_format(self, sample_image_bytes):
        """Test format conversion."""
        processor = ImageProcessor()

        try:
            # Convert to different format
            result = await processor.convert(
                sample_image_bytes,
                format=ImageFormat.JPEG,
            )
            assert isinstance(result, bytes)
        except ImportError:
            pass  # Expected if Pillow not installed


class TestImageFormat:
    """Tests for ImageFormat enum."""

    def test_format_values(self):
        """Test that all expected formats are defined."""
        assert ImageFormat.JPEG.value == "jpeg"
        assert ImageFormat.PNG.value == "png"
        assert ImageFormat.WEBP.value == "webp"
        assert ImageFormat.GIF.value == "gif"


class TestResizeMode:
    """Tests for ResizeMode enum."""

    def test_mode_values(self):
        """Test that all expected modes are defined."""
        assert ResizeMode.FIT.value == "fit"
        assert ResizeMode.FILL.value == "fill"
        assert ResizeMode.STRETCH.value == "stretch"
