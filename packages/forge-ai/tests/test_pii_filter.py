"""Tests for PII detection and masking."""

import pytest

from forge_ai.security.pii_filter import (
    PIIFilter,
    PIIConfig,
    PIIMaskingStrategy,
    PIIType,
    PIIEntity,
)


class TestPIIFilter:
    """Tests for the PIIFilter class."""

    @pytest.fixture
    def pii_filter(self):
        """Create a PII filter with default config."""
        config = PIIConfig(use_presidio=False)  # Don't require Presidio for tests
        return PIIFilter(config)

    def test_detect_email(self, pii_filter):
        """Test email detection."""
        entities = pii_filter.detect("Contact me at john.doe@example.com")

        assert len(entities) == 1
        assert entities[0].type == PIIType.EMAIL
        assert entities[0].value == "john.doe@example.com"

    def test_detect_phone(self, pii_filter):
        """Test phone number detection."""
        entities = pii_filter.detect("Call me at 555-123-4567")

        assert len(entities) == 1
        assert entities[0].type == PIIType.PHONE

    def test_detect_ssn(self, pii_filter):
        """Test SSN detection."""
        entities = pii_filter.detect("My SSN is 123-45-6789")

        assert len(entities) == 1
        assert entities[0].type == PIIType.SSN

    def test_detect_credit_card(self, pii_filter):
        """Test credit card detection."""
        entities = pii_filter.detect("Card number: 4111-1111-1111-1111")

        assert len(entities) == 1
        assert entities[0].type == PIIType.CREDIT_CARD

    def test_detect_ip_address(self, pii_filter):
        """Test IP address detection."""
        entities = pii_filter.detect("Server IP: 192.168.1.1")

        assert len(entities) == 1
        assert entities[0].type == PIIType.IP_ADDRESS

    def test_detect_multiple(self, pii_filter):
        """Test detecting multiple PII types."""
        text = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789"
        entities = pii_filter.detect(text)

        assert len(entities) == 3
        types = {e.type for e in entities}
        assert PIIType.EMAIL in types
        assert PIIType.PHONE in types
        assert PIIType.SSN in types

    def test_mask_redact(self, pii_filter):
        """Test masking with redaction strategy."""
        text = "Email me at john@example.com"
        masked = pii_filter.mask(text)

        assert "john@example.com" not in masked
        assert "[EMAIL_REDACTED]" in masked

    def test_mask_preserves_context(self, pii_filter):
        """Test that masking preserves surrounding text."""
        text = "My email is john@example.com and I need help."
        masked = pii_filter.mask(text)

        assert masked.startswith("My email is")
        assert masked.endswith("and I need help.")

    def test_no_pii_unchanged(self, pii_filter):
        """Test that text without PII is unchanged."""
        text = "Hello, how are you today?"
        masked = pii_filter.mask(text)

        assert masked == text

    def test_partial_masking(self):
        """Test partial masking strategy."""
        config = PIIConfig(
            masking_strategies={PIIType.SSN: PIIMaskingStrategy.PARTIAL},
            use_presidio=False,
        )
        pii_filter = PIIFilter(config)

        # Note: partial masking shows last 4 digits for SSN
        text = "SSN: 123-45-6789"
        masked = pii_filter.mask(text)

        # Should show last 4 digits
        assert "6789" in masked
        assert "123-45" not in masked

    def test_hash_masking(self):
        """Test hash masking strategy."""
        config = PIIConfig(
            masking_strategies={PIIType.EMAIL: PIIMaskingStrategy.HASH},
            use_presidio=False,
        )
        pii_filter = PIIFilter(config)

        text = "Email: test@example.com"
        masked = pii_filter.mask(text)

        assert "test@example.com" not in masked
        assert "[EMAIL:" in masked

    def test_custom_pattern(self, pii_filter):
        """Test adding custom detection pattern."""
        pii_filter.add_custom_pattern(
            name="employee_id",
            pattern=r"EMP-\d{6}",
        )

        entities = pii_filter.detect("Employee ID: EMP-123456")
        assert len(entities) >= 1

    def test_detection_report(self, pii_filter):
        """Test generating detection report."""
        text = "Contact: john@example.com, Phone: 555-123-4567"
        report = pii_filter.get_detection_report(text)

        assert report["total_entities_found"] == 2
        assert "email" in report["entities_by_type"]
        assert "phone" in report["entities_by_type"]
        assert report["text_length"] == len(text)

    def test_confidence_threshold(self):
        """Test confidence threshold filtering."""
        config = PIIConfig(
            confidence_threshold=0.9,
            use_presidio=False,
        )
        pii_filter = PIIFilter(config)

        # Regex-based detection has confidence 1.0, so it should pass
        entities = pii_filter.detect("Email: test@example.com")
        assert len(entities) == 1


class TestPIIEntity:
    """Tests for PIIEntity class."""

    def test_entity_creation(self):
        """Test creating a PII entity."""
        entity = PIIEntity(
            type=PIIType.EMAIL,
            value="test@example.com",
            start=0,
            end=16,
            confidence=0.95,
        )

        assert entity.type == PIIType.EMAIL
        assert entity.value == "test@example.com"
        assert entity.confidence == 0.95

    def test_entity_positions(self):
        """Test entity position tracking."""
        text = "Email: test@example.com"
        config = PIIConfig(use_presidio=False)
        pii_filter = PIIFilter(config)

        entities = pii_filter.detect(text)
        entity = entities[0]

        # Verify the position matches the actual location
        assert text[entity.start:entity.end] == entity.value
