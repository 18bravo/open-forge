# Track F: Forge Media Platform Design

**Date:** 2026-01-20
**Status:** Draft
**Track:** F - Media Processing
**Dependencies:** api, ontology, forge-vectors (Track C)

---

## Executive Summary

Track F implements comprehensive media processing capabilities for Open Forge, enabling document extraction, OCR, image analysis, video processing, and audio transcription. This track addresses the ~15+ media features present in Palantir Foundry that enable unstructured data processing.

### Key Packages

| Package | Purpose | Palantir Equivalent |
|---------|---------|---------------------|
| `forge-media-core` | Media storage & management | Media Sets |
| `forge-documents` | PDF, DOCX, XLSX extraction | Document Service |
| `forge-vision` | OCR, image analysis | Vision Service |
| `forge-voice` | Transcription, diarization | Speech Service |
| `forge-video` | Video processing, frames | Video Analytics |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FORGE MEDIA PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       MEDIA PIPELINE                                   │  │
│  │                                                                        │  │
│  │   ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │  │
│  │   │  Ingest │ -> │   Process   │ -> │   Extract   │ -> │  Index   │  │  │
│  │   │         │    │             │    │             │    │          │  │  │
│  │   └─────────┘    └─────────────┘    └─────────────┘    └──────────┘  │  │
│  │        │               │                  │                  │        │  │
│  │        ▼               ▼                  ▼                  ▼        │  │
│  │   ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │  │
│  │   │ Storage │    │  Conversion │    │     NLP     │    │  Vector  │  │  │
│  │   │  (S3)   │    │  (FFmpeg)   │    │  (spaCy)    │    │  Store   │  │  │
│  │   └─────────┘    └─────────────┘    └─────────────┘    └──────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ FORGE DOCUMENTS │  │  FORGE VISION   │  │      FORGE VOICE            │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────────────┤  │
│  │  PDF Extraction │  │      OCR        │  │      Transcription          │  │
│  │  DOCX Parsing   │  │  Image Analysis │  │      Diarization            │  │
│  │  Table Extract  │  │  Object Detect  │  │      Language Detect        │  │
│  │  Form Recognize │  │  Face Detect    │  │      Keyword Spotting       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         FORGE VIDEO                                    │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │  │
│  │  │   Frame   │  │  Scene    │  │   Audio   │  │     Timeline      │  │  │
│  │  │ Extraction│  │ Detection │  │ Extraction│  │     Analysis      │  │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      FORGE MEDIA CORE                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Media     │  │   Storage   │  │   Format    │  │  Metadata   │  │  │
│  │  │   Sets      │  │   Adapters  │  │   Detection │  │  Extraction │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package 1: Forge Media Core

### Purpose

Core media management infrastructure providing storage abstraction, format detection, metadata extraction, and media set organization.

### Module Structure

```
packages/forge-media-core/
├── src/
│   └── forge_media/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── media.py           # Media item model
│       │   ├── media_set.py       # Media set model
│       │   └── metadata.py        # Metadata models
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py            # Storage interface
│       │   ├── s3.py              # AWS S3 backend
│       │   ├── minio.py           # MinIO backend
│       │   ├── azure.py           # Azure Blob backend
│       │   └── gcs.py             # Google Cloud Storage
│       ├── formats/
│       │   ├── __init__.py
│       │   ├── detector.py        # Format detection
│       │   ├── converter.py       # Format conversion
│       │   └── validators.py      # Format validation
│       ├── metadata/
│       │   ├── __init__.py
│       │   ├── extractor.py       # Metadata extraction
│       │   ├── exif.py            # EXIF extraction
│       │   └── ffprobe.py         # Media probe
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── processor.py       # Processing pipeline
│       │   └── tasks.py           # Async tasks
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/media.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"

class MediaStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class MediaItem(BaseModel):
    id: str
    media_set_id: str
    name: str
    media_type: MediaType
    mime_type: str
    status: MediaStatus = MediaStatus.PENDING

    # Storage
    storage_path: str
    storage_backend: str
    size_bytes: int
    checksum: str  # SHA-256

    # Metadata
    metadata: dict[str, Any] = {}
    extracted_text: str | None = None
    thumbnails: list[str] = []

    # Processing
    processed_at: datetime | None = None
    processing_errors: list[str] = []

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Ontology link
    ontology_object_id: str | None = None
```

```python
# models/media_set.py
class MediaSet(BaseModel):
    id: str
    name: str
    description: str | None = None

    # Configuration
    processing_config: "ProcessingConfig" = None
    auto_process: bool = True

    # Stats
    item_count: int = 0
    total_size_bytes: int = 0
    processed_count: int = 0

    # Access
    owner_id: str
    visibility: Literal["private", "team", "public"] = "private"

    # Timestamps
    created_at: datetime
    updated_at: datetime

class ProcessingConfig(BaseModel):
    """Configuration for media processing."""
    extract_text: bool = True
    generate_thumbnails: bool = True
    thumbnail_sizes: list[tuple[int, int]] = [(128, 128), (256, 256), (512, 512)]
    run_ocr: bool = False
    ocr_languages: list[str] = ["en"]
    extract_entities: bool = False
    embed_content: bool = True  # Generate vector embeddings
    custom_processors: list[str] = []
```

```python
# storage/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, BinaryIO

class StorageBackend(ABC):
    """Abstract storage backend."""

    @abstractmethod
    async def upload(
        self,
        path: str,
        data: BinaryIO | bytes,
        content_type: str | None = None
    ) -> str:
        """Upload file to storage."""
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """Download file from storage."""
        pass

    @abstractmethod
    async def stream(self, path: str) -> AsyncIterator[bytes]:
        """Stream file from storage."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    async def get_url(
        self,
        path: str,
        expiry_seconds: int = 3600
    ) -> str:
        """Get presigned URL for file."""
        pass

    @abstractmethod
    async def copy(self, source: str, destination: str) -> bool:
        """Copy file within storage."""
        pass
```

```python
# storage/s3.py
import aioboto3
from botocore.config import Config

class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        prefix: str = "",
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None
    ):
        self.bucket = bucket
        self.region = region
        self.prefix = prefix
        self.endpoint_url = endpoint_url

        self.session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def _full_path(self, path: str) -> str:
        if self.prefix:
            return f"{self.prefix}/{path}"
        return path

    async def upload(
        self,
        path: str,
        data: BinaryIO | bytes,
        content_type: str | None = None
    ) -> str:
        full_path = self._full_path(path)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
            if isinstance(data, bytes):
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=full_path,
                    Body=data,
                    **extra_args
                )
            else:
                await s3.upload_fileobj(
                    data,
                    self.bucket,
                    full_path,
                    ExtraArgs=extra_args
                )

        return full_path

    async def download(self, path: str) -> bytes:
        full_path = self._full_path(path)

        async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=full_path)
            return await response["Body"].read()

    async def stream(self, path: str) -> AsyncIterator[bytes]:
        full_path = self._full_path(path)

        async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=full_path)
            async for chunk in response["Body"].iter_chunks():
                yield chunk

    async def get_url(
        self,
        path: str,
        expiry_seconds: int = 3600
    ) -> str:
        full_path = self._full_path(path)

        async with self.session.client("s3", endpoint_url=self.endpoint_url) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": full_path},
                ExpiresIn=expiry_seconds
            )
            return url
```

```python
# formats/detector.py
import magic
from pathlib import Path

class FormatDetector:
    """Detect media format from file content."""

    MIME_TO_TYPE = {
        # Images
        "image/jpeg": MediaType.IMAGE,
        "image/png": MediaType.IMAGE,
        "image/gif": MediaType.IMAGE,
        "image/webp": MediaType.IMAGE,
        "image/tiff": MediaType.IMAGE,
        "image/bmp": MediaType.IMAGE,
        "image/svg+xml": MediaType.IMAGE,
        # Video
        "video/mp4": MediaType.VIDEO,
        "video/mpeg": MediaType.VIDEO,
        "video/quicktime": MediaType.VIDEO,
        "video/x-msvideo": MediaType.VIDEO,
        "video/webm": MediaType.VIDEO,
        "video/x-matroska": MediaType.VIDEO,
        # Audio
        "audio/mpeg": MediaType.AUDIO,
        "audio/wav": MediaType.AUDIO,
        "audio/ogg": MediaType.AUDIO,
        "audio/flac": MediaType.AUDIO,
        "audio/aac": MediaType.AUDIO,
        "audio/webm": MediaType.AUDIO,
        # Documents
        "application/pdf": MediaType.DOCUMENT,
        "application/msword": MediaType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": MediaType.DOCUMENT,
        "application/vnd.ms-excel": MediaType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": MediaType.DOCUMENT,
        "application/vnd.ms-powerpoint": MediaType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": MediaType.DOCUMENT,
        "text/plain": MediaType.DOCUMENT,
        "text/html": MediaType.DOCUMENT,
        "text/markdown": MediaType.DOCUMENT,
        "text/csv": MediaType.DOCUMENT,
        # Archives
        "application/zip": MediaType.ARCHIVE,
        "application/x-tar": MediaType.ARCHIVE,
        "application/gzip": MediaType.ARCHIVE,
        "application/x-7z-compressed": MediaType.ARCHIVE,
        "application/x-rar-compressed": MediaType.ARCHIVE,
    }

    def __init__(self):
        self.magic = magic.Magic(mime=True)

    def detect(self, data: bytes) -> tuple[str, MediaType]:
        """Detect MIME type and media type from file content."""
        mime_type = self.magic.from_buffer(data)
        media_type = self.MIME_TO_TYPE.get(mime_type, MediaType.UNKNOWN)
        return mime_type, media_type

    def detect_from_path(self, path: str | Path) -> tuple[str, MediaType]:
        """Detect from file path."""
        with open(path, "rb") as f:
            header = f.read(8192)  # Read first 8KB
        return self.detect(header)
```

```python
# metadata/extractor.py
from dataclasses import dataclass
import subprocess
import json

@dataclass
class MediaMetadata:
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    bitrate: int | None = None
    codec: str | None = None
    framerate: float | None = None
    channels: int | None = None
    sample_rate: int | None = None
    page_count: int | None = None
    title: str | None = None
    author: str | None = None
    creation_date: str | None = None
    extra: dict = None

class MetadataExtractor:
    """Extract metadata from media files."""

    async def extract(
        self,
        data: bytes,
        mime_type: str
    ) -> MediaMetadata:
        """Extract metadata based on media type."""
        if mime_type.startswith("image/"):
            return await self._extract_image_metadata(data)
        elif mime_type.startswith("video/") or mime_type.startswith("audio/"):
            return await self._extract_av_metadata(data)
        elif mime_type == "application/pdf":
            return await self._extract_pdf_metadata(data)
        return MediaMetadata()

    async def _extract_av_metadata(self, data: bytes) -> MediaMetadata:
        """Extract audio/video metadata using ffprobe."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    tmp_path
                ],
                capture_output=True,
                text=True
            )
            info = json.loads(result.stdout)

            video_stream = next(
                (s for s in info.get("streams", []) if s["codec_type"] == "video"),
                None
            )
            audio_stream = next(
                (s for s in info.get("streams", []) if s["codec_type"] == "audio"),
                None
            )
            format_info = info.get("format", {})

            metadata = MediaMetadata(
                duration_seconds=float(format_info.get("duration", 0)),
                bitrate=int(format_info.get("bit_rate", 0)),
                title=format_info.get("tags", {}).get("title"),
                extra=info
            )

            if video_stream:
                metadata.width = video_stream.get("width")
                metadata.height = video_stream.get("height")
                metadata.codec = video_stream.get("codec_name")
                # Calculate framerate from ratio
                fps_str = video_stream.get("r_frame_rate", "0/1")
                if "/" in fps_str:
                    num, den = map(int, fps_str.split("/"))
                    metadata.framerate = num / den if den else 0

            if audio_stream:
                metadata.channels = audio_stream.get("channels")
                metadata.sample_rate = int(audio_stream.get("sample_rate", 0))
                if not metadata.codec:
                    metadata.codec = audio_stream.get("codec_name")

            return metadata
        finally:
            os.unlink(tmp_path)

    async def _extract_image_metadata(self, data: bytes) -> MediaMetadata:
        """Extract image metadata using Pillow."""
        from PIL import Image
        from PIL.ExifTags import TAGS
        import io

        img = Image.open(io.BytesIO(data))

        metadata = MediaMetadata(
            width=img.width,
            height=img.height,
            extra={}
        )

        # Extract EXIF data
        if hasattr(img, "_getexif") and img._getexif():
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, (str, int, float)):
                    metadata.extra[tag] = value

        return metadata
```

```python
# pipeline/processor.py
from typing import Callable
import asyncio

class MediaProcessor:
    """Orchestrate media processing pipeline."""

    def __init__(
        self,
        storage: StorageBackend,
        format_detector: FormatDetector,
        metadata_extractor: MetadataExtractor
    ):
        self.storage = storage
        self.detector = format_detector
        self.metadata = metadata_extractor
        self._processors: dict[MediaType, list[Callable]] = {}

    def register_processor(
        self,
        media_type: MediaType,
        processor: Callable
    ):
        """Register a processor for a media type."""
        if media_type not in self._processors:
            self._processors[media_type] = []
        self._processors[media_type].append(processor)

    async def process(
        self,
        media_item: MediaItem,
        config: ProcessingConfig
    ) -> MediaItem:
        """Process a media item through the pipeline."""
        try:
            # Download file
            data = await self.storage.download(media_item.storage_path)

            # Detect format if not set
            if not media_item.mime_type:
                media_item.mime_type, media_item.media_type = self.detector.detect(data)

            # Extract metadata
            extracted_metadata = await self.metadata.extract(data, media_item.mime_type)
            media_item.metadata.update(vars(extracted_metadata))

            # Generate thumbnails
            if config.generate_thumbnails and media_item.media_type in [MediaType.IMAGE, MediaType.VIDEO]:
                thumbnails = await self._generate_thumbnails(
                    data,
                    media_item,
                    config.thumbnail_sizes
                )
                media_item.thumbnails = thumbnails

            # Run type-specific processors
            processors = self._processors.get(media_item.media_type, [])
            for processor in processors:
                media_item = await processor(media_item, data, config)

            # Generate embeddings if enabled
            if config.embed_content and media_item.extracted_text:
                await self._generate_embeddings(media_item)

            media_item.status = MediaStatus.READY
            media_item.processed_at = datetime.utcnow()

        except Exception as e:
            media_item.status = MediaStatus.FAILED
            media_item.processing_errors.append(str(e))

        return media_item

    async def _generate_thumbnails(
        self,
        data: bytes,
        item: MediaItem,
        sizes: list[tuple[int, int]]
    ) -> list[str]:
        """Generate thumbnails for image/video."""
        from PIL import Image
        import io

        thumbnails = []

        if item.media_type == MediaType.IMAGE:
            img = Image.open(io.BytesIO(data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            for width, height in sizes:
                thumb = img.copy()
                thumb.thumbnail((width, height))

                buffer = io.BytesIO()
                thumb.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)

                thumb_path = f"thumbnails/{item.id}/{width}x{height}.jpg"
                await self.storage.upload(thumb_path, buffer.getvalue(), "image/jpeg")
                thumbnails.append(thumb_path)

        elif item.media_type == MediaType.VIDEO:
            # Use ffmpeg for video thumbnails
            thumbnails = await self._extract_video_thumbnails(data, item, sizes)

        return thumbnails
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/media", tags=["media"])

@router.post("/sets")
async def create_media_set(
    name: str,
    description: str | None = None,
    config: ProcessingConfig | None = None
) -> MediaSet:
    """Create a new media set."""
    pass

@router.get("/sets")
async def list_media_sets(
    limit: int = 50,
    offset: int = 0
) -> list[MediaSet]:
    """List media sets."""
    pass

@router.get("/sets/{set_id}")
async def get_media_set(set_id: str) -> MediaSet:
    """Get media set details."""
    pass

@router.post("/sets/{set_id}/items")
async def upload_media(
    set_id: str,
    file: UploadFile,
    process: bool = True
) -> MediaItem:
    """Upload media to a set."""
    pass

@router.post("/sets/{set_id}/items/batch")
async def upload_batch(
    set_id: str,
    files: list[UploadFile]
) -> list[MediaItem]:
    """Batch upload media files."""
    pass

@router.get("/sets/{set_id}/items")
async def list_media_items(
    set_id: str,
    media_type: MediaType | None = None,
    status: MediaStatus | None = None,
    limit: int = 50,
    offset: int = 0
) -> list[MediaItem]:
    """List items in a media set."""
    pass

@router.get("/items/{item_id}")
async def get_media_item(item_id: str) -> MediaItem:
    """Get media item details."""
    pass

@router.get("/items/{item_id}/download")
async def download_media(item_id: str) -> StreamingResponse:
    """Download media file."""
    pass

@router.get("/items/{item_id}/thumbnail/{size}")
async def get_thumbnail(
    item_id: str,
    size: Literal["128", "256", "512"]
) -> StreamingResponse:
    """Get media thumbnail."""
    pass

@router.post("/items/{item_id}/reprocess")
async def reprocess_media(
    item_id: str,
    config: ProcessingConfig | None = None
) -> MediaItem:
    """Reprocess a media item."""
    pass

@router.delete("/items/{item_id}")
async def delete_media(item_id: str) -> dict:
    """Delete media item."""
    pass
```

---

## Package 2: Forge Documents

### Purpose

Extract text, tables, and structured data from documents including PDF, DOCX, XLSX, HTML, and more.

### Module Structure

```
packages/forge-documents/
├── src/
│   └── forge_documents/
│       ├── __init__.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── base.py            # Base extractor
│       │   ├── pdf.py             # PDF extraction
│       │   ├── docx.py            # Word documents
│       │   ├── xlsx.py            # Excel spreadsheets
│       │   ├── pptx.py            # PowerPoint
│       │   ├── html.py            # HTML pages
│       │   ├── email.py           # Email (EML/MSG)
│       │   └── markdown.py        # Markdown
│       ├── chunking/
│       │   ├── __init__.py
│       │   ├── strategies.py      # Chunking strategies
│       │   ├── page.py            # Page-based chunking
│       │   ├── semantic.py        # Semantic chunking
│       │   └── table.py           # Table extraction
│       ├── nlp/
│       │   ├── __init__.py
│       │   ├── entities.py        # Named entity extraction
│       │   ├── keywords.py        # Keyword extraction
│       │   └── summarize.py       # Summarization
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# extractors/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class DocumentPage(BaseModel):
    page_number: int
    text: str
    tables: list["ExtractedTable"] = []
    images: list["ExtractedImage"] = []
    metadata: dict[str, Any] = {}

class ExtractedTable(BaseModel):
    page_number: int | None = None
    table_index: int
    headers: list[str] | None = None
    rows: list[list[str]]
    confidence: float = 1.0

class ExtractedDocument(BaseModel):
    pages: list[DocumentPage]
    full_text: str
    tables: list[ExtractedTable]
    metadata: dict[str, Any]
    page_count: int
    word_count: int

class BaseExtractor(ABC):
    """Abstract base for document extractors."""

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        pass

    @abstractmethod
    async def extract(
        self,
        data: bytes,
        options: dict | None = None
    ) -> ExtractedDocument:
        pass
```

```python
# extractors/pdf.py
import fitz  # PyMuPDF
import pdfplumber
from io import BytesIO

class PDFExtractor(BaseExtractor):
    """Extract content from PDF documents."""

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    async def extract(
        self,
        data: bytes,
        options: dict | None = None
    ) -> ExtractedDocument:
        options = options or {}
        extract_tables = options.get("extract_tables", True)
        extract_images = options.get("extract_images", False)

        pages = []
        all_tables = []
        full_text_parts = []

        # Use PyMuPDF for text extraction
        doc = fitz.open(stream=data, filetype="pdf")

        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            full_text_parts.append(text)

            page_tables = []
            page_images = []

            if extract_images:
                for img in page.get_images():
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    page_images.append(ExtractedImage(
                        page_number=page_num + 1,
                        image_data=base_image["image"],
                        mime_type=f"image/{base_image['ext']}"
                    ))

            pages.append(DocumentPage(
                page_number=page_num + 1,
                text=text,
                tables=page_tables,
                images=page_images
            ))

        # Use pdfplumber for table extraction (more accurate)
        if extract_tables:
            with pdfplumber.open(BytesIO(data)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 0:
                            # First row as headers if looks like headers
                            headers = table[0] if self._looks_like_headers(table[0]) else None
                            rows = table[1:] if headers else table

                            extracted = ExtractedTable(
                                page_number=page_num + 1,
                                table_index=table_idx,
                                headers=headers,
                                rows=rows
                            )
                            all_tables.append(extracted)
                            pages[page_num].tables.append(extracted)

        full_text = "\n\n".join(full_text_parts)

        return ExtractedDocument(
            pages=pages,
            full_text=full_text,
            tables=all_tables,
            metadata=self._extract_metadata(doc),
            page_count=len(pages),
            word_count=len(full_text.split())
        )

    def _extract_metadata(self, doc: fitz.Document) -> dict:
        """Extract PDF metadata."""
        meta = doc.metadata
        return {
            "title": meta.get("title"),
            "author": meta.get("author"),
            "subject": meta.get("subject"),
            "keywords": meta.get("keywords"),
            "creator": meta.get("creator"),
            "producer": meta.get("producer"),
            "creation_date": meta.get("creationDate"),
            "modification_date": meta.get("modDate")
        }

    def _looks_like_headers(self, row: list) -> bool:
        """Heuristic to detect header row."""
        if not row:
            return False
        # Headers are usually short and non-numeric
        return all(
            isinstance(cell, str) and
            len(cell) < 50 and
            not cell.replace(".", "").replace(",", "").isdigit()
            for cell in row if cell
        )
```

```python
# extractors/docx.py
from docx import Document
from docx.table import Table

class DOCXExtractor(BaseExtractor):
    """Extract content from Word documents."""

    @property
    def supported_mime_types(self) -> list[str]:
        return [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]

    async def extract(
        self,
        data: bytes,
        options: dict | None = None
    ) -> ExtractedDocument:
        doc = Document(BytesIO(data))

        text_parts = []
        tables = []

        for element in doc.element.body:
            if element.tag.endswith("p"):
                # Paragraph
                para = doc.paragraphs[len(text_parts)]
                text_parts.append(para.text)
            elif element.tag.endswith("tbl"):
                # Table
                table_idx = len(tables)
                table = doc.tables[table_idx]
                tables.append(self._extract_table(table, table_idx))

        full_text = "\n".join(text_parts)

        # DOCX doesn't have pages, create single page
        pages = [DocumentPage(
            page_number=1,
            text=full_text,
            tables=tables
        )]

        return ExtractedDocument(
            pages=pages,
            full_text=full_text,
            tables=tables,
            metadata=self._extract_metadata(doc),
            page_count=1,
            word_count=len(full_text.split())
        )

    def _extract_table(self, table: Table, index: int) -> ExtractedTable:
        """Extract table from DOCX."""
        rows = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            rows.append(row_data)

        headers = rows[0] if rows else None
        data_rows = rows[1:] if len(rows) > 1 else rows

        return ExtractedTable(
            table_index=index,
            headers=headers,
            rows=data_rows
        )

    def _extract_metadata(self, doc: Document) -> dict:
        """Extract DOCX metadata."""
        props = doc.core_properties
        return {
            "title": props.title,
            "author": props.author,
            "subject": props.subject,
            "keywords": props.keywords,
            "created": props.created.isoformat() if props.created else None,
            "modified": props.modified.isoformat() if props.modified else None,
            "last_modified_by": props.last_modified_by
        }
```

```python
# extractors/xlsx.py
import openpyxl
import pandas as pd
from io import BytesIO

class XLSXExtractor(BaseExtractor):
    """Extract content from Excel spreadsheets."""

    @property
    def supported_mime_types(self) -> list[str]:
        return [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]

    async def extract(
        self,
        data: bytes,
        options: dict | None = None
    ) -> ExtractedDocument:
        options = options or {}
        sheet_names = options.get("sheets")  # None = all sheets

        workbook = openpyxl.load_workbook(BytesIO(data), data_only=True)

        pages = []
        tables = []
        text_parts = []

        sheets_to_process = sheet_names or workbook.sheetnames

        for sheet_idx, sheet_name in enumerate(sheets_to_process):
            if sheet_name not in workbook.sheetnames:
                continue

            sheet = workbook[sheet_name]

            # Convert sheet to table
            rows = []
            for row in sheet.iter_rows(values_only=True):
                row_data = [str(cell) if cell is not None else "" for cell in row]
                if any(row_data):  # Skip empty rows
                    rows.append(row_data)

            if rows:
                # First row as headers
                headers = rows[0]
                data_rows = rows[1:]

                table = ExtractedTable(
                    page_number=sheet_idx + 1,
                    table_index=len(tables),
                    headers=headers,
                    rows=data_rows
                )
                tables.append(table)

                # Convert to text representation
                sheet_text = f"Sheet: {sheet_name}\n"
                sheet_text += "\t".join(headers) + "\n"
                for row in data_rows:
                    sheet_text += "\t".join(row) + "\n"
                text_parts.append(sheet_text)

                pages.append(DocumentPage(
                    page_number=sheet_idx + 1,
                    text=sheet_text,
                    tables=[table],
                    metadata={"sheet_name": sheet_name}
                ))

        full_text = "\n\n".join(text_parts)

        return ExtractedDocument(
            pages=pages,
            full_text=full_text,
            tables=tables,
            metadata=self._extract_metadata(workbook),
            page_count=len(pages),
            word_count=len(full_text.split())
        )
```

```python
# chunking/strategies.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class TextChunk(BaseModel):
    text: str
    start_index: int
    end_index: int
    metadata: dict = {}
    page_number: int | None = None
    section: str | None = None

class ChunkingStrategy(ABC):
    """Abstract chunking strategy."""

    @abstractmethod
    def chunk(
        self,
        document: ExtractedDocument,
        config: dict | None = None
    ) -> list[TextChunk]:
        pass

class FixedSizeChunker(ChunkingStrategy):
    """Chunk by fixed character/token count with overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        separator: str = "\n"
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separator = separator

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict | None = None
    ) -> list[TextChunk]:
        text = document.full_text
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at separator
            if end < len(text):
                break_point = text.rfind(self.separator, start, end)
                if break_point > start:
                    end = break_point + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    start_index=start,
                    end_index=end
                ))

            start = end - self.overlap

        return chunks

class SemanticChunker(ChunkingStrategy):
    """Chunk by semantic boundaries (paragraphs, sections)."""

    def __init__(self, max_chunk_size: int = 2000):
        self.max_chunk_size = max_chunk_size

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict | None = None
    ) -> list[TextChunk]:
        chunks = []

        for page in document.pages:
            # Split page into paragraphs
            paragraphs = page.text.split("\n\n")

            current_chunk = []
            current_size = 0
            start_idx = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if current_size + len(para) > self.max_chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(TextChunk(
                        text=chunk_text,
                        start_index=start_idx,
                        end_index=start_idx + len(chunk_text),
                        page_number=page.page_number
                    ))
                    current_chunk = []
                    current_size = 0
                    start_idx += len(chunk_text) + 2

                current_chunk.append(para)
                current_size += len(para) + 2

            # Save remaining
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(TextChunk(
                    text=chunk_text,
                    start_index=start_idx,
                    end_index=start_idx + len(chunk_text),
                    page_number=page.page_number
                ))

        return chunks

class PageChunker(ChunkingStrategy):
    """Chunk by document pages."""

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict | None = None
    ) -> list[TextChunk]:
        chunks = []
        current_index = 0

        for page in document.pages:
            text = page.text.strip()
            if text:
                chunks.append(TextChunk(
                    text=text,
                    start_index=current_index,
                    end_index=current_index + len(text),
                    page_number=page.page_number
                ))
            current_index += len(text) + 2

        return chunks
```

```python
# nlp/entities.py
import spacy
from pydantic import BaseModel

class NamedEntity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0

class EntityExtractor:
    """Extract named entities from text."""

    ENTITY_MAPPING = {
        "PERSON": "person",
        "ORG": "organization",
        "GPE": "location",
        "DATE": "date",
        "TIME": "time",
        "MONEY": "money",
        "PERCENT": "percentage",
        "PRODUCT": "product",
        "EVENT": "event",
        "LAW": "law",
        "NORP": "nationality",
        "FAC": "facility",
        "WORK_OF_ART": "work_of_art",
        "LANGUAGE": "language",
        "QUANTITY": "quantity",
        "ORDINAL": "ordinal",
        "CARDINAL": "cardinal"
    }

    def __init__(self, model: str = "en_core_web_sm"):
        self.nlp = spacy.load(model)

    async def extract(self, text: str) -> list[NamedEntity]:
        """Extract named entities from text."""
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            entities.append(NamedEntity(
                text=ent.text,
                label=self.ENTITY_MAPPING.get(ent.label_, ent.label_.lower()),
                start=ent.start_char,
                end=ent.end_char
            ))

        return entities

    async def extract_from_document(
        self,
        document: ExtractedDocument
    ) -> dict[str, list[NamedEntity]]:
        """Extract entities from each page."""
        results = {}

        for page in document.pages:
            entities = await self.extract(page.text)
            results[f"page_{page.page_number}"] = entities

        return results
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/extract")
async def extract_document(
    file: UploadFile,
    extract_tables: bool = True,
    extract_images: bool = False,
    run_ocr: bool = False
) -> ExtractedDocument:
    """Extract content from a document."""
    pass

@router.post("/chunk")
async def chunk_document(
    file: UploadFile,
    strategy: Literal["fixed", "semantic", "page"] = "semantic",
    chunk_size: int = 1000,
    overlap: int = 200
) -> list[TextChunk]:
    """Extract and chunk a document."""
    pass

@router.post("/entities")
async def extract_entities(
    file: UploadFile
) -> dict[str, list[NamedEntity]]:
    """Extract named entities from document."""
    pass

@router.post("/summarize")
async def summarize_document(
    file: UploadFile,
    max_length: int = 500
) -> dict:
    """Generate document summary."""
    pass

@router.post("/tables")
async def extract_tables(
    file: UploadFile
) -> list[ExtractedTable]:
    """Extract tables from document."""
    pass
```

---

## Package 3: Forge Vision

### Purpose

OCR text extraction, image analysis, object detection, and face detection capabilities.

### Module Structure

```
packages/forge-vision/
├── src/
│   └── forge_vision/
│       ├── __init__.py
│       ├── ocr/
│       │   ├── __init__.py
│       │   ├── base.py            # OCR interface
│       │   ├── tesseract.py       # Tesseract OCR
│       │   ├── easyocr.py         # EasyOCR
│       │   ├── paddleocr.py       # PaddleOCR
│       │   └── cloud.py           # Cloud OCR (Google/AWS/Azure)
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── classification.py  # Image classification
│       │   ├── detection.py       # Object detection
│       │   ├── segmentation.py    # Image segmentation
│       │   └── face.py            # Face detection
│       ├── processing/
│       │   ├── __init__.py
│       │   ├── resize.py          # Image resizing
│       │   ├── enhance.py         # Image enhancement
│       │   ├── tiling.py          # Large image tiling
│       │   └── convert.py         # Format conversion
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# ocr/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class OCRWord(BaseModel):
    text: str
    confidence: float
    bounding_box: tuple[int, int, int, int]  # x, y, width, height

class OCRLine(BaseModel):
    text: str
    confidence: float
    words: list[OCRWord]
    bounding_box: tuple[int, int, int, int]

class OCRBlock(BaseModel):
    text: str
    confidence: float
    lines: list[OCRLine]
    bounding_box: tuple[int, int, int, int]
    block_type: str = "text"  # text, table, image, etc.

class OCRResult(BaseModel):
    full_text: str
    blocks: list[OCRBlock]
    confidence: float
    language: str | None = None
    metadata: dict[str, Any] = {}

class BaseOCR(ABC):
    """Abstract OCR engine."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict | None = None
    ) -> OCRResult:
        pass
```

```python
# ocr/tesseract.py
import pytesseract
from PIL import Image
from io import BytesIO

class TesseractOCR(BaseOCR):
    """Tesseract OCR engine."""

    @property
    def name(self) -> str:
        return "tesseract"

    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict | None = None
    ) -> OCRResult:
        options = options or {}
        lang = "+".join(languages) if languages else "eng"

        img = Image.open(BytesIO(image))

        # Get detailed data
        data = pytesseract.image_to_data(
            img,
            lang=lang,
            output_type=pytesseract.Output.DICT
        )

        # Build structured result
        blocks = self._build_blocks(data)
        full_text = pytesseract.image_to_string(img, lang=lang)

        # Calculate average confidence
        confidences = [float(c) for c in data["conf"] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return OCRResult(
            full_text=full_text.strip(),
            blocks=blocks,
            confidence=avg_confidence / 100,
            language=lang
        )

    def _build_blocks(self, data: dict) -> list[OCRBlock]:
        """Build block structure from Tesseract data."""
        blocks = {}

        for i in range(len(data["text"])):
            if int(data["conf"][i]) == -1:
                continue

            block_num = data["block_num"][i]
            line_num = data["line_num"][i]
            word_num = data["word_num"][i]

            if block_num not in blocks:
                blocks[block_num] = {"lines": {}}

            if line_num not in blocks[block_num]["lines"]:
                blocks[block_num]["lines"][line_num] = {"words": []}

            word = OCRWord(
                text=data["text"][i],
                confidence=int(data["conf"][i]) / 100,
                bounding_box=(
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i]
                )
            )
            blocks[block_num]["lines"][line_num]["words"].append(word)

        # Convert to OCRBlock list
        result = []
        for block_data in blocks.values():
            lines = []
            for line_data in block_data["lines"].values():
                words = line_data["words"]
                if words:
                    line_text = " ".join(w.text for w in words)
                    line_conf = sum(w.confidence for w in words) / len(words)
                    lines.append(OCRLine(
                        text=line_text,
                        confidence=line_conf,
                        words=words,
                        bounding_box=self._merge_boxes([w.bounding_box for w in words])
                    ))

            if lines:
                block_text = "\n".join(l.text for l in lines)
                block_conf = sum(l.confidence for l in lines) / len(lines)
                result.append(OCRBlock(
                    text=block_text,
                    confidence=block_conf,
                    lines=lines,
                    bounding_box=self._merge_boxes([l.bounding_box for l in lines])
                ))

        return result
```

```python
# ocr/easyocr.py
import easyocr

class EasyOCREngine(BaseOCR):
    """EasyOCR engine (better for multilingual)."""

    def __init__(self, gpu: bool = True):
        self.gpu = gpu
        self._readers: dict[str, easyocr.Reader] = {}

    @property
    def name(self) -> str:
        return "easyocr"

    def _get_reader(self, languages: list[str]) -> easyocr.Reader:
        key = ",".join(sorted(languages))
        if key not in self._readers:
            self._readers[key] = easyocr.Reader(languages, gpu=self.gpu)
        return self._readers[key]

    async def recognize(
        self,
        image: bytes,
        languages: list[str] | None = None,
        options: dict | None = None
    ) -> OCRResult:
        languages = languages or ["en"]
        options = options or {}

        reader = self._get_reader(languages)

        # Run OCR
        results = reader.readtext(image, detail=1)

        # Build result
        blocks = []
        full_text_parts = []

        for bbox, text, conf in results:
            # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x1, y1 = int(bbox[0][0]), int(bbox[0][1])
            x2, y2 = int(bbox[2][0]), int(bbox[2][1])

            word = OCRWord(
                text=text,
                confidence=conf,
                bounding_box=(x1, y1, x2 - x1, y2 - y1)
            )

            line = OCRLine(
                text=text,
                confidence=conf,
                words=[word],
                bounding_box=(x1, y1, x2 - x1, y2 - y1)
            )

            blocks.append(OCRBlock(
                text=text,
                confidence=conf,
                lines=[line],
                bounding_box=(x1, y1, x2 - x1, y2 - y1)
            ))

            full_text_parts.append(text)

        avg_conf = sum(b.confidence for b in blocks) / len(blocks) if blocks else 0

        return OCRResult(
            full_text=" ".join(full_text_parts),
            blocks=blocks,
            confidence=avg_conf,
            language=languages[0]
        )
```

```python
# analysis/detection.py
from pydantic import BaseModel
import torch
from ultralytics import YOLO

class DetectedObject(BaseModel):
    label: str
    confidence: float
    bounding_box: tuple[int, int, int, int]  # x, y, width, height
    class_id: int

class DetectionResult(BaseModel):
    objects: list[DetectedObject]
    image_width: int
    image_height: int
    model: str

class ObjectDetector:
    """Detect objects in images using YOLO."""

    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)

    async def detect(
        self,
        image: bytes,
        confidence_threshold: float = 0.5,
        classes: list[int] | None = None
    ) -> DetectionResult:
        """Detect objects in an image."""
        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(image))

        # Run inference
        results = self.model(
            img,
            conf=confidence_threshold,
            classes=classes
        )[0]

        objects = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = results.names[cls_id]

            objects.append(DetectedObject(
                label=label,
                confidence=conf,
                bounding_box=(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                class_id=cls_id
            ))

        return DetectionResult(
            objects=objects,
            image_width=img.width,
            image_height=img.height,
            model=self.model.model_name
        )
```

```python
# analysis/face.py
from pydantic import BaseModel
import face_recognition
import numpy as np
from PIL import Image
from io import BytesIO

class DetectedFace(BaseModel):
    bounding_box: tuple[int, int, int, int]
    confidence: float
    landmarks: dict[str, tuple[int, int]] | None = None
    encoding: list[float] | None = None

class FaceDetectionResult(BaseModel):
    faces: list[DetectedFace]
    image_width: int
    image_height: int

class FaceDetector:
    """Detect and analyze faces in images."""

    async def detect(
        self,
        image: bytes,
        include_landmarks: bool = True,
        include_encodings: bool = False
    ) -> FaceDetectionResult:
        """Detect faces in an image."""
        img = Image.open(BytesIO(image))
        img_array = np.array(img)

        # Detect face locations
        face_locations = face_recognition.face_locations(img_array, model="hog")

        faces = []
        for top, right, bottom, left in face_locations:
            face = DetectedFace(
                bounding_box=(left, top, right - left, bottom - top),
                confidence=1.0  # face_recognition doesn't provide confidence
            )

            if include_landmarks:
                landmarks = face_recognition.face_landmarks(
                    img_array,
                    face_locations=[(top, right, bottom, left)]
                )
                if landmarks:
                    # Simplify landmarks to key points
                    lm = landmarks[0]
                    face.landmarks = {
                        "left_eye": self._center_point(lm.get("left_eye", [])),
                        "right_eye": self._center_point(lm.get("right_eye", [])),
                        "nose_tip": self._center_point(lm.get("nose_tip", [])),
                        "top_lip": self._center_point(lm.get("top_lip", [])),
                        "bottom_lip": self._center_point(lm.get("bottom_lip", []))
                    }

            if include_encodings:
                encodings = face_recognition.face_encodings(
                    img_array,
                    known_face_locations=[(top, right, bottom, left)]
                )
                if encodings:
                    face.encoding = encodings[0].tolist()

            faces.append(face)

        return FaceDetectionResult(
            faces=faces,
            image_width=img.width,
            image_height=img.height
        )

    def _center_point(self, points: list) -> tuple[int, int] | None:
        if not points:
            return None
        x = sum(p[0] for p in points) // len(points)
        y = sum(p[1] for p in points) // len(points)
        return (x, y)

    async def compare_faces(
        self,
        known_encoding: list[float],
        unknown_image: bytes,
        tolerance: float = 0.6
    ) -> list[dict]:
        """Compare a known face encoding against faces in an image."""
        result = await self.detect(unknown_image, include_encodings=True)

        matches = []
        known = np.array(known_encoding)

        for face in result.faces:
            if face.encoding:
                unknown = np.array(face.encoding)
                distance = np.linalg.norm(known - unknown)
                is_match = distance <= tolerance

                matches.append({
                    "bounding_box": face.bounding_box,
                    "is_match": is_match,
                    "distance": float(distance),
                    "confidence": max(0, 1 - distance)
                })

        return matches
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/vision", tags=["vision"])

@router.post("/ocr")
async def run_ocr(
    file: UploadFile,
    engine: Literal["tesseract", "easyocr", "paddleocr"] = "easyocr",
    languages: list[str] = ["en"]
) -> OCRResult:
    """Extract text from image using OCR."""
    pass

@router.post("/detect")
async def detect_objects(
    file: UploadFile,
    confidence: float = 0.5,
    classes: list[str] | None = None
) -> DetectionResult:
    """Detect objects in image."""
    pass

@router.post("/faces")
async def detect_faces(
    file: UploadFile,
    include_landmarks: bool = True,
    include_encodings: bool = False
) -> FaceDetectionResult:
    """Detect faces in image."""
    pass

@router.post("/faces/compare")
async def compare_faces(
    file: UploadFile,
    known_encoding: list[float],
    tolerance: float = 0.6
) -> list[dict]:
    """Compare face against known encoding."""
    pass

@router.post("/classify")
async def classify_image(
    file: UploadFile,
    top_k: int = 5
) -> list[dict]:
    """Classify image content."""
    pass

@router.post("/enhance")
async def enhance_image(
    file: UploadFile,
    operations: list[str] = ["auto_contrast", "sharpen"]
) -> StreamingResponse:
    """Enhance image quality."""
    pass
```

---

## Package 4: Forge Voice

### Purpose

Audio transcription, speaker diarization, language detection, and keyword spotting.

### Module Structure

```
packages/forge-voice/
├── src/
│   └── forge_voice/
│       ├── __init__.py
│       ├── transcription/
│       │   ├── __init__.py
│       │   ├── base.py            # Transcription interface
│       │   ├── whisper.py         # OpenAI Whisper
│       │   ├── faster_whisper.py  # Faster Whisper
│       │   ├── deepgram.py        # Deepgram API
│       │   └── assemblyai.py      # AssemblyAI API
│       ├── diarization/
│       │   ├── __init__.py
│       │   ├── pyannote.py        # Pyannote diarization
│       │   └── speaker.py         # Speaker identification
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── language.py        # Language detection
│       │   ├── keywords.py        # Keyword spotting
│       │   └── sentiment.py       # Audio sentiment
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# transcription/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class TranscriptWord(BaseModel):
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker: str | None = None

class TranscriptSegment(BaseModel):
    text: str
    start_time: float
    end_time: float
    confidence: float
    words: list[TranscriptWord] = []
    speaker: str | None = None
    language: str | None = None

class TranscriptionResult(BaseModel):
    text: str
    segments: list[TranscriptSegment]
    language: str
    duration_seconds: float
    confidence: float
    word_count: int
    metadata: dict[str, Any] = {}

class BaseTranscriber(ABC):
    """Abstract transcription engine."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        options: dict | None = None
    ) -> TranscriptionResult:
        pass
```

```python
# transcription/whisper.py
import whisper
import numpy as np
import tempfile
import os

class WhisperTranscriber(BaseTranscriber):
    """OpenAI Whisper transcription."""

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
        self.model_size = model_size

    @property
    def name(self) -> str:
        return f"whisper-{self.model_size}"

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        options: dict | None = None
    ) -> TranscriptionResult:
        options = options or {}

        # Write to temp file (Whisper needs file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name

        try:
            # Transcribe
            result = self.model.transcribe(
                tmp_path,
                language=language,
                word_timestamps=True,
                task="transcribe"
            )

            segments = []
            for seg in result["segments"]:
                words = []
                if "words" in seg:
                    for word in seg["words"]:
                        words.append(TranscriptWord(
                            text=word["word"],
                            start_time=word["start"],
                            end_time=word["end"],
                            confidence=word.get("probability", 1.0)
                        ))

                segments.append(TranscriptSegment(
                    text=seg["text"].strip(),
                    start_time=seg["start"],
                    end_time=seg["end"],
                    confidence=seg.get("avg_logprob", 0),
                    words=words,
                    language=result["language"]
                ))

            # Calculate duration from last segment
            duration = segments[-1].end_time if segments else 0

            return TranscriptionResult(
                text=result["text"].strip(),
                segments=segments,
                language=result["language"],
                duration_seconds=duration,
                confidence=self._calculate_confidence(result),
                word_count=len(result["text"].split()),
                metadata={"model": self.name}
            )
        finally:
            os.unlink(tmp_path)

    def _calculate_confidence(self, result: dict) -> float:
        """Calculate average confidence from segments."""
        if not result.get("segments"):
            return 0
        probs = [seg.get("avg_logprob", -1) for seg in result["segments"]]
        # Convert log prob to rough confidence (0-1)
        avg_log_prob = sum(probs) / len(probs)
        return min(1.0, max(0, np.exp(avg_log_prob)))
```

```python
# transcription/faster_whisper.py
from faster_whisper import WhisperModel

class FasterWhisperTranscriber(BaseTranscriber):
    """Faster Whisper (CTranslate2) transcription."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "float16"
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.model_size = model_size

    @property
    def name(self) -> str:
        return f"faster-whisper-{self.model_size}"

    async def transcribe(
        self,
        audio: bytes,
        language: str | None = None,
        options: dict | None = None
    ) -> TranscriptionResult:
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name

        try:
            segments_gen, info = self.model.transcribe(
                tmp_path,
                language=language,
                word_timestamps=True,
                beam_size=5
            )

            segments = []
            full_text_parts = []

            for seg in segments_gen:
                words = []
                if seg.words:
                    for word in seg.words:
                        words.append(TranscriptWord(
                            text=word.word,
                            start_time=word.start,
                            end_time=word.end,
                            confidence=word.probability
                        ))

                segments.append(TranscriptSegment(
                    text=seg.text.strip(),
                    start_time=seg.start,
                    end_time=seg.end,
                    confidence=seg.avg_logprob,
                    words=words,
                    language=info.language
                ))
                full_text_parts.append(seg.text.strip())

            return TranscriptionResult(
                text=" ".join(full_text_parts),
                segments=segments,
                language=info.language,
                duration_seconds=info.duration,
                confidence=info.language_probability,
                word_count=sum(len(seg.text.split()) for seg in segments),
                metadata={"model": self.name}
            )
        finally:
            os.unlink(tmp_path)
```

```python
# diarization/pyannote.py
from pyannote.audio import Pipeline
from pydantic import BaseModel
import torch

class SpeakerSegment(BaseModel):
    speaker: str
    start_time: float
    end_time: float
    confidence: float = 1.0

class DiarizationResult(BaseModel):
    segments: list[SpeakerSegment]
    num_speakers: int
    duration_seconds: float

class PyannoteDiarizer:
    """Speaker diarization using Pyannote."""

    def __init__(self, auth_token: str):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=auth_token
        )
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))

    async def diarize(
        self,
        audio: bytes,
        num_speakers: int | None = None,
        min_speakers: int = 1,
        max_speakers: int = 10
    ) -> DiarizationResult:
        """Perform speaker diarization."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name

        try:
            # Run diarization
            diarization = self.pipeline(
                tmp_path,
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )

            segments = []
            speakers = set()

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(SpeakerSegment(
                    speaker=speaker,
                    start_time=turn.start,
                    end_time=turn.end
                ))
                speakers.add(speaker)

            # Calculate duration
            duration = segments[-1].end_time if segments else 0

            return DiarizationResult(
                segments=segments,
                num_speakers=len(speakers),
                duration_seconds=duration
            )
        finally:
            os.unlink(tmp_path)

    async def diarize_and_transcribe(
        self,
        audio: bytes,
        transcriber: BaseTranscriber,
        num_speakers: int | None = None
    ) -> TranscriptionResult:
        """Combine diarization with transcription."""
        # Run both in parallel
        import asyncio
        diarization_task = self.diarize(audio, num_speakers)
        transcription_task = transcriber.transcribe(audio)

        diarization, transcription = await asyncio.gather(
            diarization_task,
            transcription_task
        )

        # Assign speakers to transcript segments
        for segment in transcription.segments:
            # Find overlapping speaker
            speaker = self._find_speaker_at_time(
                (segment.start_time + segment.end_time) / 2,
                diarization.segments
            )
            segment.speaker = speaker

            # Also assign to words
            for word in segment.words:
                word.speaker = self._find_speaker_at_time(
                    (word.start_time + word.end_time) / 2,
                    diarization.segments
                )

        transcription.metadata["num_speakers"] = diarization.num_speakers
        return transcription

    def _find_speaker_at_time(
        self,
        time: float,
        segments: list[SpeakerSegment]
    ) -> str | None:
        """Find speaker at a given time."""
        for seg in segments:
            if seg.start_time <= time <= seg.end_time:
                return seg.speaker
        return None
```

```python
# analysis/language.py
from pydantic import BaseModel

class LanguageDetectionResult(BaseModel):
    language: str
    language_name: str
    confidence: float
    alternatives: list[dict] = []

class LanguageDetector:
    """Detect language from audio."""

    def __init__(self, model_size: str = "base"):
        import whisper
        self.model = whisper.load_model(model_size)

    async def detect(self, audio: bytes) -> LanguageDetectionResult:
        """Detect language from audio sample."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio)
            tmp_path = tmp.name

        try:
            # Load audio and detect language
            audio_array = whisper.load_audio(tmp_path)
            audio_array = whisper.pad_or_trim(audio_array)

            mel = whisper.log_mel_spectrogram(audio_array).to(self.model.device)
            _, probs = self.model.detect_language(mel)

            # Get top languages
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

            top_lang, top_prob = sorted_probs[0]
            alternatives = [
                {"language": lang, "confidence": float(prob)}
                for lang, prob in sorted_probs[1:5]
            ]

            return LanguageDetectionResult(
                language=top_lang,
                language_name=self._get_language_name(top_lang),
                confidence=float(top_prob),
                alternatives=alternatives
            )
        finally:
            os.unlink(tmp_path)

    def _get_language_name(self, code: str) -> str:
        """Get full language name from code."""
        names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi"
        }
        return names.get(code, code)
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile,
    engine: Literal["whisper", "faster-whisper", "deepgram"] = "faster-whisper",
    language: str | None = None,
    model_size: str = "base"
) -> TranscriptionResult:
    """Transcribe audio to text."""
    pass

@router.post("/diarize")
async def diarize_audio(
    file: UploadFile,
    num_speakers: int | None = None,
    min_speakers: int = 1,
    max_speakers: int = 10
) -> DiarizationResult:
    """Identify speakers in audio."""
    pass

@router.post("/transcribe-diarize")
async def transcribe_with_diarization(
    file: UploadFile,
    num_speakers: int | None = None,
    language: str | None = None
) -> TranscriptionResult:
    """Transcribe with speaker identification."""
    pass

@router.post("/detect-language")
async def detect_language(
    file: UploadFile
) -> LanguageDetectionResult:
    """Detect spoken language."""
    pass

@router.post("/keywords")
async def spot_keywords(
    file: UploadFile,
    keywords: list[str]
) -> list[dict]:
    """Find keywords in audio."""
    pass
```

---

## Package 5: Forge Video

### Purpose

Video processing including frame extraction, scene detection, audio extraction, and timeline analysis.

### Module Structure

```
packages/forge-video/
├── src/
│   └── forge_video/
│       ├── __init__.py
│       ├── extraction/
│       │   ├── __init__.py
│       │   ├── frames.py          # Frame extraction
│       │   ├── audio.py           # Audio extraction
│       │   └── thumbnails.py      # Thumbnail generation
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── scenes.py          # Scene detection
│       │   ├── motion.py          # Motion analysis
│       │   └── timeline.py        # Timeline analysis
│       ├── processing/
│       │   ├── __init__.py
│       │   ├── transcode.py       # Video transcoding
│       │   ├── clip.py            # Video clipping
│       │   └── merge.py           # Video merging
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# extraction/frames.py
from pydantic import BaseModel
import subprocess
import tempfile
import os
from pathlib import Path

class ExtractedFrame(BaseModel):
    frame_number: int
    timestamp: float
    image_path: str
    width: int
    height: int

class FrameExtractor:
    """Extract frames from video."""

    async def extract_frames(
        self,
        video: bytes,
        fps: float = 1.0,
        start_time: float | None = None,
        end_time: float | None = None,
        max_frames: int | None = None
    ) -> list[ExtractedFrame]:
        """Extract frames at specified FPS."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write video to temp file
            video_path = Path(tmp_dir) / "input.mp4"
            video_path.write_bytes(video)

            frames_dir = Path(tmp_dir) / "frames"
            frames_dir.mkdir()

            # Build ffmpeg command
            cmd = ["ffmpeg", "-i", str(video_path)]

            if start_time:
                cmd.extend(["-ss", str(start_time)])
            if end_time:
                cmd.extend(["-to", str(end_time)])

            cmd.extend([
                "-vf", f"fps={fps}",
                "-frame_pts", "1",
                str(frames_dir / "frame_%06d.jpg")
            ])

            subprocess.run(cmd, capture_output=True, check=True)

            # Read extracted frames
            frames = []
            for frame_path in sorted(frames_dir.glob("frame_*.jpg")):
                frame_num = int(frame_path.stem.split("_")[1])
                timestamp = frame_num / fps

                # Get frame dimensions
                from PIL import Image
                img = Image.open(frame_path)

                frames.append(ExtractedFrame(
                    frame_number=frame_num,
                    timestamp=timestamp,
                    image_path=str(frame_path),
                    width=img.width,
                    height=img.height
                ))

                if max_frames and len(frames) >= max_frames:
                    break

            return frames

    async def extract_keyframes(
        self,
        video: bytes
    ) -> list[ExtractedFrame]:
        """Extract only keyframes (I-frames)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "input.mp4"
            video_path.write_bytes(video)

            frames_dir = Path(tmp_dir) / "frames"
            frames_dir.mkdir()

            # Extract keyframes only
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vf", "select=eq(pict_type\\,I)",
                "-vsync", "vfr",
                str(frames_dir / "keyframe_%06d.jpg")
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            frames = []
            for frame_path in sorted(frames_dir.glob("keyframe_*.jpg")):
                frame_num = int(frame_path.stem.split("_")[1])
                from PIL import Image
                img = Image.open(frame_path)

                frames.append(ExtractedFrame(
                    frame_number=frame_num,
                    timestamp=0,  # Would need to parse pts
                    image_path=str(frame_path),
                    width=img.width,
                    height=img.height
                ))

            return frames
```

```python
# analysis/scenes.py
from pydantic import BaseModel
from scenedetect import detect, ContentDetector, ThresholdDetector
import tempfile
from pathlib import Path

class SceneBoundary(BaseModel):
    scene_number: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    duration: float

class SceneDetectionResult(BaseModel):
    scenes: list[SceneBoundary]
    total_scenes: int
    video_duration: float

class SceneDetector:
    """Detect scene changes in video."""

    async def detect_scenes(
        self,
        video: bytes,
        threshold: float = 27.0,
        min_scene_len: float = 0.5
    ) -> SceneDetectionResult:
        """Detect scene boundaries using content-aware detection."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video)
            video_path = tmp.name

        try:
            # Run scene detection
            scene_list = detect(
                video_path,
                ContentDetector(threshold=threshold, min_scene_len=int(min_scene_len * 30))
            )

            scenes = []
            for i, (start, end) in enumerate(scene_list):
                scenes.append(SceneBoundary(
                    scene_number=i + 1,
                    start_time=start.get_seconds(),
                    end_time=end.get_seconds(),
                    start_frame=start.get_frames(),
                    end_frame=end.get_frames(),
                    duration=end.get_seconds() - start.get_seconds()
                ))

            video_duration = scenes[-1].end_time if scenes else 0

            return SceneDetectionResult(
                scenes=scenes,
                total_scenes=len(scenes),
                video_duration=video_duration
            )
        finally:
            os.unlink(video_path)

    async def extract_scene_thumbnails(
        self,
        video: bytes,
        scenes: list[SceneBoundary]
    ) -> list[str]:
        """Extract thumbnail for each scene."""
        thumbnails = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "input.mp4"
            video_path.write_bytes(video)

            for scene in scenes:
                # Extract frame from middle of scene
                middle_time = (scene.start_time + scene.end_time) / 2
                thumb_path = Path(tmp_dir) / f"scene_{scene.scene_number}.jpg"

                cmd = [
                    "ffmpeg", "-i", str(video_path),
                    "-ss", str(middle_time),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(thumb_path)
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                thumbnails.append(str(thumb_path))

            return thumbnails
```

```python
# analysis/timeline.py
from pydantic import BaseModel
from typing import Any

class TimelineEvent(BaseModel):
    timestamp: float
    end_timestamp: float | None = None
    event_type: str
    label: str
    confidence: float = 1.0
    metadata: dict[str, Any] = {}

class VideoTimeline(BaseModel):
    duration: float
    events: list[TimelineEvent]
    scenes: list[SceneBoundary] = []
    speakers: list[dict] = []
    objects: list[dict] = []

class TimelineAnalyzer:
    """Analyze video and build comprehensive timeline."""

    def __init__(
        self,
        scene_detector: SceneDetector,
        object_detector: "ObjectDetector",
        transcriber: "BaseTranscriber",
        diarizer: "PyannoteDiarizer"
    ):
        self.scene_detector = scene_detector
        self.object_detector = object_detector
        self.transcriber = transcriber
        self.diarizer = diarizer

    async def analyze(
        self,
        video: bytes,
        detect_scenes: bool = True,
        detect_objects: bool = True,
        transcribe: bool = True,
        diarize: bool = True
    ) -> VideoTimeline:
        """Build comprehensive video timeline."""
        import asyncio

        events = []
        scenes = []
        speakers = []
        objects = []

        tasks = []

        if detect_scenes:
            tasks.append(("scenes", self.scene_detector.detect_scenes(video)))

        if transcribe:
            # Extract audio first
            audio = await self._extract_audio(video)
            if diarize:
                tasks.append(("transcribe", self.diarizer.diarize_and_transcribe(
                    audio, self.transcriber
                )))
            else:
                tasks.append(("transcribe", self.transcriber.transcribe(audio)))

        # Run tasks in parallel
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for (task_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                continue

            if task_name == "scenes":
                scenes = result.scenes
                for scene in scenes:
                    events.append(TimelineEvent(
                        timestamp=scene.start_time,
                        end_timestamp=scene.end_time,
                        event_type="scene",
                        label=f"Scene {scene.scene_number}"
                    ))

            elif task_name == "transcribe":
                for segment in result.segments:
                    events.append(TimelineEvent(
                        timestamp=segment.start_time,
                        end_timestamp=segment.end_time,
                        event_type="speech",
                        label=segment.text,
                        confidence=segment.confidence,
                        metadata={"speaker": segment.speaker}
                    ))

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Get duration from ffprobe
        duration = await self._get_duration(video)

        return VideoTimeline(
            duration=duration,
            events=events,
            scenes=scenes,
            speakers=speakers,
            objects=objects
        )

    async def _extract_audio(self, video: bytes) -> bytes:
        """Extract audio track from video."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            tmp_video.write(video)
            video_path = tmp_video.name

        audio_path = video_path.replace(".mp4", ".wav")

        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            with open(audio_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(video_path)
            if os.path.exists(audio_path):
                os.unlink(audio_path)
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/video", tags=["video"])

@router.post("/frames")
async def extract_frames(
    file: UploadFile,
    fps: float = 1.0,
    start_time: float | None = None,
    end_time: float | None = None,
    max_frames: int = 100
) -> list[ExtractedFrame]:
    """Extract frames from video."""
    pass

@router.post("/keyframes")
async def extract_keyframes(
    file: UploadFile
) -> list[ExtractedFrame]:
    """Extract keyframes only."""
    pass

@router.post("/scenes")
async def detect_scenes(
    file: UploadFile,
    threshold: float = 27.0,
    min_scene_len: float = 0.5
) -> SceneDetectionResult:
    """Detect scene boundaries."""
    pass

@router.post("/audio")
async def extract_audio(
    file: UploadFile,
    format: Literal["wav", "mp3", "flac"] = "wav"
) -> StreamingResponse:
    """Extract audio track from video."""
    pass

@router.post("/timeline")
async def analyze_timeline(
    file: UploadFile,
    detect_scenes: bool = True,
    transcribe: bool = True,
    diarize: bool = True
) -> VideoTimeline:
    """Build comprehensive video timeline."""
    pass

@router.post("/clip")
async def clip_video(
    file: UploadFile,
    start_time: float,
    end_time: float
) -> StreamingResponse:
    """Extract video clip."""
    pass

@router.post("/transcode")
async def transcode_video(
    file: UploadFile,
    format: Literal["mp4", "webm", "mov"] = "mp4",
    resolution: str | None = None,
    bitrate: str | None = None
) -> StreamingResponse:
    """Transcode video to different format."""
    pass
```

---

## Implementation Roadmap

### Phase F1: Media Core + Documents (Weeks 1-2)

**Goals:**
- Core media storage and management
- Document extraction (PDF, DOCX, XLSX)
- Chunking strategies for RAG

**Deliverables:**
1. forge-media-core package
2. forge-documents package
3. Storage backends (S3, MinIO)
4. Document extraction APIs

**Acceptance Criteria:**
- [ ] Can upload and manage media sets
- [ ] Can extract text from PDF, DOCX, XLSX
- [ ] Can chunk documents for vector embedding
- [ ] Thumbnails generated automatically

### Phase F2: Vision + Video (Weeks 3-4)

**Goals:**
- OCR with multiple engines
- Object and face detection
- Video frame extraction and scene detection

**Deliverables:**
1. forge-vision package
2. forge-video package
3. OCR integration (Tesseract, EasyOCR)
4. YOLO object detection

**Acceptance Criteria:**
- [ ] Can extract text from images
- [ ] Can detect objects in images
- [ ] Can detect faces with landmarks
- [ ] Can extract frames and detect scenes

### Phase F3: Voice (Weeks 5-6)

**Goals:**
- Audio transcription
- Speaker diarization
- Language detection

**Deliverables:**
1. forge-voice package
2. Whisper integration
3. Pyannote diarization
4. Combined transcription + diarization

**Acceptance Criteria:**
- [ ] Can transcribe audio accurately
- [ ] Can identify multiple speakers
- [ ] Can detect spoken language
- [ ] Word-level timestamps available

---

## Integration Points

### With Forge Vectors (Track C)

- Document chunks are embedded for RAG
- OCR text is vectorized for semantic search
- Transcriptions indexed for audio search

### With Forge Navigator (Track B)

- Media assets cataloged with metadata
- Document content indexed for search
- Automatic PII detection in extracted text

### With Forge Studio (Track D)

- Media viewer widgets
- Document preview component
- Video player with timeline

### With Forge AI (Track C)

- Documents provide context for LLM queries
- Images analyzed by vision models
- Audio transcripts used for AI analysis

---

## Security Considerations

1. **File Validation**: Strict MIME type validation before processing
2. **Size Limits**: Configurable upload size limits
3. **Virus Scanning**: Optional ClamAV integration
4. **PII Detection**: Automatic scanning for sensitive content
5. **Access Control**: Media sets respect workspace permissions
6. **Audit Logging**: All media access logged

---

## Performance Considerations

1. **Async Processing**: All extraction runs asynchronously
2. **Worker Pools**: Dedicated workers for CPU-intensive tasks
3. **Caching**: Extracted content cached in Redis
4. **Streaming**: Large files streamed, not loaded to memory
5. **GPU Acceleration**: OCR and ML models use GPU when available
6. **Batch Processing**: Support for bulk media processing
