"""
PII (Personally Identifiable Information) detection and masking.

This module provides:
- Detection of common PII types (emails, phones, SSNs, credit cards, etc.)
- Multiple masking strategies (redact, hash, pseudonymize)
- Integration with Presidio for advanced entity recognition
"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    NAME = "name"
    ADDRESS = "address"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    BANK_ACCOUNT = "bank_account"
    MEDICAL_RECORD = "medical_record"
    CUSTOM = "custom"


class PIIMaskingStrategy(str, Enum):
    """Strategy for masking PII."""

    REDACT = "redact"  # Replace with [PII_TYPE_REDACTED]
    HASH = "hash"  # Replace with hash of value
    PSEUDONYMIZE = "pseudonymize"  # Replace with consistent fake value
    PARTIAL = "partial"  # Partially mask (e.g., ***-**-1234)
    REMOVE = "remove"  # Remove entirely


@dataclass
class PIIEntity:
    """A detected PII entity."""

    type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 1.0
    context: str | None = None


@dataclass
class PIIConfig:
    """Configuration for PII detection and masking."""

    # Which PII types to detect
    detect_types: list[PIIType] = field(
        default_factory=lambda: [
            PIIType.EMAIL,
            PIIType.PHONE,
            PIIType.SSN,
            PIIType.CREDIT_CARD,
            PIIType.IP_ADDRESS,
        ]
    )

    # Masking strategy per type (defaults to REDACT)
    masking_strategies: dict[PIIType, PIIMaskingStrategy] = field(default_factory=dict)

    # Default masking strategy
    default_strategy: PIIMaskingStrategy = PIIMaskingStrategy.REDACT

    # Custom patterns for detection
    custom_patterns: dict[str, str] = field(default_factory=dict)

    # Use Presidio for advanced detection (if available)
    use_presidio: bool = True

    # Minimum confidence threshold for detection
    confidence_threshold: float = 0.7


class PIIFilter:
    """
    PII detection and masking filter.

    Detects and masks personally identifiable information in text
    using regex patterns and optionally Presidio for advanced detection.
    """

    # Regex patterns for common PII types
    PATTERNS: dict[PIIType, str] = {
        PIIType.EMAIL: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        PIIType.PHONE: r"\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
        PIIType.SSN: r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        PIIType.CREDIT_CARD: r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        PIIType.IP_ADDRESS: r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        PIIType.DATE_OF_BIRTH: r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b",
        PIIType.PASSPORT: r"\b[A-Z]{1,2}[0-9]{6,9}\b",
        PIIType.BANK_ACCOUNT: r"\b\d{8,17}\b",  # Simplified - real detection would be more complex
    }

    # Partial masking patterns
    PARTIAL_MASKS: dict[PIIType, tuple[int, int]] = {
        PIIType.SSN: (7, 4),  # Show last 4 digits
        PIIType.CREDIT_CARD: (12, 4),  # Show last 4 digits
        PIIType.PHONE: (6, 4),  # Show last 4 digits
        PIIType.EMAIL: (3, 0),  # Show first 3 chars
    }

    def __init__(self, config: PIIConfig | None = None):
        """
        Initialize the PII filter.

        Args:
            config: Configuration for detection and masking.
        """
        self.config = config or PIIConfig()
        self._presidio_analyzer = None
        self._presidio_anonymizer = None

        # Compile regex patterns
        self._compiled_patterns: dict[PIIType, re.Pattern] = {
            pii_type: re.compile(pattern)
            for pii_type, pattern in self.PATTERNS.items()
            if pii_type in self.config.detect_types
        }

        # Add custom patterns
        for name, pattern in self.config.custom_patterns.items():
            self._compiled_patterns[PIIType.CUSTOM] = re.compile(pattern)

        # Initialize Presidio if configured
        if self.config.use_presidio:
            self._init_presidio()

        # Pseudonymization cache for consistent replacements
        self._pseudonym_cache: dict[str, str] = {}

    def _init_presidio(self) -> None:
        """Initialize Presidio analyzer and anonymizer."""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._presidio_analyzer = AnalyzerEngine()
            self._presidio_anonymizer = AnonymizerEngine()
            logger.info("Presidio initialized for advanced PII detection")
        except ImportError:
            logger.warning(
                "Presidio not available, falling back to regex-only detection. "
                "Install with: pip install presidio-analyzer presidio-anonymizer"
            )
            self._presidio_analyzer = None
            self._presidio_anonymizer = None

    def detect(self, text: str) -> list[PIIEntity]:
        """
        Detect PII entities in text.

        Args:
            text: Text to scan for PII.

        Returns:
            List of detected PII entities.
        """
        entities: list[PIIEntity] = []

        # Regex-based detection
        for pii_type, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                entities.append(
                    PIIEntity(
                        type=pii_type,
                        value=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,
                    )
                )

        # Presidio-based detection (more sophisticated)
        if self._presidio_analyzer is not None:
            try:
                presidio_results = self._presidio_analyzer.analyze(
                    text=text,
                    language="en",
                    score_threshold=self.config.confidence_threshold,
                )

                for result in presidio_results:
                    # Map Presidio entity types to our types
                    pii_type = self._map_presidio_type(result.entity_type)
                    if pii_type and pii_type in self.config.detect_types:
                        # Check for duplicates (already found by regex)
                        is_duplicate = any(
                            e.start == result.start and e.end == result.end
                            for e in entities
                        )
                        if not is_duplicate:
                            entities.append(
                                PIIEntity(
                                    type=pii_type,
                                    value=text[result.start : result.end],
                                    start=result.start,
                                    end=result.end,
                                    confidence=result.score,
                                )
                            )
            except Exception as e:
                logger.warning("Presidio detection failed", error=str(e))

        # Sort by position
        entities.sort(key=lambda e: e.start)

        return entities

    def mask(self, text: str) -> str:
        """
        Detect and mask all PII in text.

        Args:
            text: Text to mask.

        Returns:
            Text with PII masked according to configured strategies.
        """
        entities = self.detect(text)

        if not entities:
            return text

        # Apply masks from end to start to preserve positions
        masked_text = text
        for entity in reversed(entities):
            strategy = self.config.masking_strategies.get(
                entity.type, self.config.default_strategy
            )
            replacement = self._get_replacement(entity, strategy)
            masked_text = (
                masked_text[: entity.start] + replacement + masked_text[entity.end :]
            )

        return masked_text

    def _get_replacement(self, entity: PIIEntity, strategy: PIIMaskingStrategy) -> str:
        """Get the replacement string for a PII entity."""
        if strategy == PIIMaskingStrategy.REDACT:
            return f"[{entity.type.value.upper()}_REDACTED]"

        elif strategy == PIIMaskingStrategy.HASH:
            # Use SHA-256 truncated to 8 chars
            hash_value = hashlib.sha256(entity.value.encode()).hexdigest()[:8]
            return f"[{entity.type.value.upper()}:{hash_value}]"

        elif strategy == PIIMaskingStrategy.PSEUDONYMIZE:
            # Return consistent pseudonym for the same value
            if entity.value not in self._pseudonym_cache:
                pseudonym = self._generate_pseudonym(entity.type)
                self._pseudonym_cache[entity.value] = pseudonym
            return self._pseudonym_cache[entity.value]

        elif strategy == PIIMaskingStrategy.PARTIAL:
            return self._partial_mask(entity)

        elif strategy == PIIMaskingStrategy.REMOVE:
            return ""

        return f"[{entity.type.value.upper()}_MASKED]"

    def _partial_mask(self, entity: PIIEntity) -> str:
        """Apply partial masking to preserve some information."""
        mask_info = self.PARTIAL_MASKS.get(entity.type)
        if not mask_info:
            return f"[{entity.type.value.upper()}_MASKED]"

        mask_count, visible_count = mask_info
        value = entity.value

        # Remove non-alphanumeric for cleaner masking
        alphanumeric = re.sub(r"[^a-zA-Z0-9]", "", value)

        if visible_count > 0:
            # Show last N characters
            visible = alphanumeric[-visible_count:]
            masked = "*" * mask_count
            return masked + visible
        else:
            # Show first N characters
            visible = alphanumeric[:mask_count]
            masked = "*" * (len(alphanumeric) - mask_count)
            return visible + masked

    def _generate_pseudonym(self, pii_type: PIIType) -> str:
        """Generate a pseudonym for a PII type."""
        # Simple pseudonym generation - in production would use a proper library
        pseudonyms: dict[PIIType, list[str]] = {
            PIIType.EMAIL: ["user@example.com", "contact@example.org"],
            PIIType.PHONE: ["555-123-4567", "555-987-6543"],
            PIIType.NAME: ["John Doe", "Jane Smith"],
            PIIType.ADDRESS: ["123 Main St, Anytown, USA"],
        }

        import random
        options = pseudonyms.get(pii_type, [f"[PSEUDONYM_{pii_type.value.upper()}]"])
        return random.choice(options)

    def _map_presidio_type(self, presidio_type: str) -> PIIType | None:
        """Map Presidio entity types to our PII types."""
        mapping = {
            "EMAIL_ADDRESS": PIIType.EMAIL,
            "PHONE_NUMBER": PIIType.PHONE,
            "US_SSN": PIIType.SSN,
            "CREDIT_CARD": PIIType.CREDIT_CARD,
            "IP_ADDRESS": PIIType.IP_ADDRESS,
            "DATE_TIME": PIIType.DATE_OF_BIRTH,
            "PERSON": PIIType.NAME,
            "LOCATION": PIIType.ADDRESS,
            "US_PASSPORT": PIIType.PASSPORT,
            "US_DRIVER_LICENSE": PIIType.DRIVERS_LICENSE,
            "US_BANK_NUMBER": PIIType.BANK_ACCOUNT,
            "MEDICAL_LICENSE": PIIType.MEDICAL_RECORD,
        }
        return mapping.get(presidio_type)

    def add_custom_pattern(self, name: str, pattern: str) -> None:
        """Add a custom PII detection pattern."""
        self._compiled_patterns[PIIType.CUSTOM] = re.compile(pattern)
        self.config.custom_patterns[name] = pattern

    def get_detection_report(self, text: str) -> dict[str, Any]:
        """
        Generate a detailed report of PII detection.

        Returns a report suitable for compliance/audit purposes.
        """
        entities = self.detect(text)

        return {
            "total_entities_found": len(entities),
            "entities_by_type": {
                pii_type.value: len([e for e in entities if e.type == pii_type])
                for pii_type in PIIType
                if any(e.type == pii_type for e in entities)
            },
            "entities": [
                {
                    "type": e.type.value,
                    "position": (e.start, e.end),
                    "confidence": e.confidence,
                    # Don't include actual value in report
                }
                for e in entities
            ],
            "text_length": len(text),
            "presidio_enabled": self._presidio_analyzer is not None,
        }
