"""OCR providers for text extraction from images."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class OCRWord(BaseModel):
    """A single word detected by OCR."""

    text: str
    confidence: float  # 0.0 to 1.0
    bounding_box: tuple[int, int, int, int]  # x, y, width, height


class OCRLine(BaseModel):
    """A line of text detected by OCR."""

    text: str
    confidence: float
    words: list[OCRWord] = Field(default_factory=list)
    bounding_box: tuple[int, int, int, int]


class OCRBlock(BaseModel):
    """A block of text detected by OCR."""

    text: str
    confidence: float
    lines: list[OCRLine] = Field(default_factory=list)
    bounding_box: tuple[int, int, int, int]
    block_type: str = "text"  # text, table, image, etc.


class OCRResult(BaseModel):
    """
    Complete OCR result from an image.

    Attributes:
        full_text: All extracted text concatenated
        blocks: Structured text blocks with positions
        confidence: Overall confidence score (0.0 to 1.0)
        language: Detected or specified language
        metadata: Additional provider-specific data
    """

    full_text: str
    blocks: list[OCRBlock] = Field(default_factory=list)
    confidence: float
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class OCRProvider(Protocol):
    """
    Protocol for OCR providers.

    Implementations should extract text from images using various
    OCR engines (Tesseract, Cloud Vision API, etc.).
    """

    @property
    def name(self) -> str:
        """Provider name identifier."""
        ...

    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> OCRResult:
        """
        Perform OCR on an image.

        Args:
            image: Raw image bytes (PNG, JPEG, etc.)
            languages: List of language codes (e.g., ["en", "es"])
            options: Provider-specific options

        Returns:
            OCRResult with extracted text and positions
        """
        ...


class TesseractOCR:
    """
    OCR using Tesseract (local, open-source).

    Requires pytesseract and Tesseract to be installed on the system.

    Example:
        ```python
        ocr = TesseractOCR()
        with open("document.png", "rb") as f:
            result = await ocr.recognize(f.read(), languages=["en"])
        print(result.full_text)
        ```
    """

    @property
    def name(self) -> str:
        return "tesseract"

    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> OCRResult:
        """
        Perform OCR using Tesseract.

        Args:
            image: Raw image bytes
            languages: Language codes (default: ["eng"])
            options: Tesseract-specific options

        Returns:
            OCRResult with text and positions
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "pytesseract and pillow are required for Tesseract OCR. "
                "Install with: pip install pytesseract pillow"
            ) from e

        from io import BytesIO

        options = options or {}
        lang = "+".join(languages) if languages else "eng"

        # Load image
        img = Image.open(BytesIO(image))

        # Get detailed OCR data
        data = pytesseract.image_to_data(
            img,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )

        # Build structured result
        blocks = self._build_blocks(data)
        full_text = pytesseract.image_to_string(img, lang=lang)

        # Calculate average confidence
        confidences = [float(c) for c in data["conf"] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0

        return OCRResult(
            full_text=full_text.strip(),
            blocks=blocks,
            confidence=avg_confidence,
            language=lang,
        )

    def _build_blocks(self, data: dict) -> list[OCRBlock]:
        """Build block structure from Tesseract output."""
        # Group by block number
        blocks_dict: dict[int, dict] = {}

        for i in range(len(data["text"])):
            if int(data["conf"][i]) == -1:
                continue

            text = data["text"][i]
            if not text.strip():
                continue

            block_num = data["block_num"][i]
            line_num = data["line_num"][i]

            if block_num not in blocks_dict:
                blocks_dict[block_num] = {"lines": {}}

            if line_num not in blocks_dict[block_num]["lines"]:
                blocks_dict[block_num]["lines"][line_num] = []

            word = OCRWord(
                text=text,
                confidence=int(data["conf"][i]) / 100,
                bounding_box=(
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                ),
            )
            blocks_dict[block_num]["lines"][line_num].append(word)

        # Convert to OCRBlock list
        result: list[OCRBlock] = []
        for block_data in blocks_dict.values():
            lines: list[OCRLine] = []
            for words in block_data["lines"].values():
                if words:
                    line_text = " ".join(w.text for w in words)
                    line_conf = sum(w.confidence for w in words) / len(words)
                    lines.append(
                        OCRLine(
                            text=line_text,
                            confidence=line_conf,
                            words=words,
                            bounding_box=self._merge_boxes([w.bounding_box for w in words]),
                        )
                    )

            if lines:
                block_text = "\n".join(line.text for line in lines)
                block_conf = sum(line.confidence for line in lines) / len(lines)
                result.append(
                    OCRBlock(
                        text=block_text,
                        confidence=block_conf,
                        lines=lines,
                        bounding_box=self._merge_boxes([line.bounding_box for line in lines]),
                    )
                )

        return result

    def _merge_boxes(
        self, boxes: list[tuple[int, int, int, int]]
    ) -> tuple[int, int, int, int]:
        """Merge multiple bounding boxes into one encompassing box."""
        if not boxes:
            return (0, 0, 0, 0)

        min_x = min(b[0] for b in boxes)
        min_y = min(b[1] for b in boxes)
        max_x = max(b[0] + b[2] for b in boxes)
        max_y = max(b[1] + b[3] for b in boxes)

        return (min_x, min_y, max_x - min_x, max_y - min_y)


class CloudVisionOCR:
    """
    OCR using Google Cloud Vision API (stub implementation).

    This is a placeholder for cloud-based OCR. Requires google-cloud-vision
    package and valid credentials.

    Example:
        ```python
        ocr = CloudVisionOCR(credentials_path="/path/to/credentials.json")
        result = await ocr.recognize(image_bytes)
        ```
    """

    def __init__(self, credentials_path: str | None = None):
        """
        Initialize Cloud Vision OCR.

        Args:
            credentials_path: Path to Google Cloud credentials JSON
        """
        self.credentials_path = credentials_path
        self._client = None

    @property
    def name(self) -> str:
        return "cloud_vision"

    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> OCRResult:
        """
        Perform OCR using Google Cloud Vision API.

        Note: This is a stub implementation. Full implementation requires
        google-cloud-vision package.

        Args:
            image: Raw image bytes
            languages: Language hints
            options: Cloud Vision-specific options

        Returns:
            OCRResult with text and positions

        Raises:
            NotImplementedError: Cloud Vision not yet fully implemented
        """
        # Stub implementation - full implementation would use:
        # from google.cloud import vision
        # client = vision.ImageAnnotatorClient()
        # response = client.text_detection(image=vision.Image(content=image))

        raise NotImplementedError(
            "CloudVisionOCR is a stub. To implement:\n"
            "1. Install google-cloud-vision: pip install google-cloud-vision\n"
            "2. Set up Google Cloud credentials\n"
            "3. Implement the recognize method using Vision API"
        )
