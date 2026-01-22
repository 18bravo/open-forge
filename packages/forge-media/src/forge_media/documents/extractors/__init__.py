"""Document extractors for various file formats."""

from forge_media.documents.extractors.base import (
    DocumentExtractor,
    ExtractedDocument,
    DocumentPage,
    ExtractedTable,
    ExtractedImage,
)
from forge_media.documents.extractors.pdf import PDFExtractor
from forge_media.documents.extractors.docx import DOCXExtractor
from forge_media.documents.extractors.xlsx import XLSXExtractor

__all__ = [
    "DocumentExtractor",
    "ExtractedDocument",
    "DocumentPage",
    "ExtractedTable",
    "ExtractedImage",
    "PDFExtractor",
    "DOCXExtractor",
    "XLSXExtractor",
]
