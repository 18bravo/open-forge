"""PDF document extraction using pypdf."""

from __future__ import annotations

from io import BytesIO

from forge_media.documents.extractors.base import (
    DocumentExtractor,
    DocumentPage,
    ExtractedDocument,
    ExtractedTable,
    ExtractionError,
    ExtractionOptions,
)


class PDFExtractor(DocumentExtractor):
    """
    Extract content from PDF documents.

    Uses pypdf for basic text extraction. For advanced features like
    table extraction, install the 'advanced' extras which adds pdfplumber.

    Example:
        ```python
        extractor = PDFExtractor()
        with open("document.pdf", "rb") as f:
            data = f.read()

        result = await extractor.extract(data)
        print(result.full_text)
        print(f"Pages: {result.page_count}")
        ```
    """

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    async def extract(
        self,
        data: bytes,
        options: ExtractionOptions | None = None,
    ) -> ExtractedDocument:
        """
        Extract content from a PDF document.

        Args:
            data: Raw PDF bytes
            options: Extraction options

        Returns:
            ExtractedDocument with pages, text, and metadata
        """
        options = options or ExtractionOptions()

        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ExtractionError(
                "pypdf is required for PDF extraction. Install with: pip install pypdf",
                cause=e,
            )

        try:
            reader = PdfReader(BytesIO(data))
        except Exception as e:
            raise ExtractionError(f"Failed to read PDF: {e}", cause=e)

        pages: list[DocumentPage] = []
        all_tables: list[ExtractedTable] = []
        full_text_parts: list[str] = []

        # Determine pages to process
        total_pages = len(reader.pages)
        max_pages = options.max_pages or total_pages
        pages_to_process = min(total_pages, max_pages)

        for page_num in range(pages_to_process):
            page = reader.pages[page_num]

            # Extract text
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            full_text_parts.append(text)

            # Create page object
            pages.append(
                DocumentPage(
                    page_number=page_num + 1,
                    text=text,
                    tables=[],  # Basic pypdf doesn't extract tables
                    images=[],
                )
            )

        # Extract tables if pdfplumber is available and enabled
        if options.extract_tables:
            try:
                tables = await self._extract_tables_with_pdfplumber(data, pages_to_process)
                all_tables.extend(tables)

                # Associate tables with pages
                for table in tables:
                    if table.page_number and table.page_number <= len(pages):
                        pages[table.page_number - 1].tables.append(table)
            except ImportError:
                # pdfplumber not available, skip table extraction
                pass

        full_text = "\n\n".join(full_text_parts)

        # Extract metadata
        metadata = {}
        if options.extract_metadata and reader.metadata:
            metadata = {
                "title": reader.metadata.title,
                "author": reader.metadata.author,
                "subject": reader.metadata.subject,
                "creator": reader.metadata.creator,
                "producer": reader.metadata.producer,
                "creation_date": str(reader.metadata.creation_date)
                if reader.metadata.creation_date
                else None,
                "modification_date": str(reader.metadata.modification_date)
                if reader.metadata.modification_date
                else None,
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}

        return ExtractedDocument(
            pages=pages,
            full_text=full_text,
            tables=all_tables,
            metadata=metadata,
            page_count=len(pages),
            word_count=len(full_text.split()),
        )

    async def _extract_tables_with_pdfplumber(
        self, data: bytes, max_pages: int
    ) -> list[ExtractedTable]:
        """Extract tables using pdfplumber (if available)."""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber required for table extraction")

        tables: list[ExtractedTable] = []

        with pdfplumber.open(BytesIO(data)) as pdf:
            for page_num, page in enumerate(pdf.pages[:max_pages]):
                page_tables = page.extract_tables()

                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 0:
                        # Determine if first row is headers
                        headers = table[0] if self._looks_like_headers(table[0]) else None
                        rows = table[1:] if headers else table

                        # Clean up cell values
                        clean_headers = (
                            [str(h) if h else "" for h in headers] if headers else None
                        )
                        clean_rows = [
                            [str(cell) if cell else "" for cell in row] for row in rows
                        ]

                        tables.append(
                            ExtractedTable(
                                page_number=page_num + 1,
                                table_index=table_idx,
                                headers=clean_headers,
                                rows=clean_rows,
                            )
                        )

        return tables

    def _looks_like_headers(self, row: list) -> bool:
        """Heuristic to detect if a row looks like headers."""
        if not row:
            return False

        # Headers are usually short text, not numbers
        for cell in row:
            if cell is None:
                continue
            cell_str = str(cell).strip()
            if not cell_str:
                continue
            # If cell is a number, probably not a header
            try:
                float(cell_str.replace(",", "").replace("$", ""))
                return False
            except ValueError:
                pass
            # If cell is too long, probably not a header
            if len(cell_str) > 50:
                return False

        return True
