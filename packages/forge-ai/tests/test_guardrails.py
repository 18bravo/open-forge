"""Tests for guardrails and output validation."""

import pytest

from forge_ai.security.guardrails import (
    GuardrailConfig,
    GuardrailsEngine,
    GuardrailAction,
    GuardrailViolation,
    OutputValidationRule,
    TopicFilter,
    TopicConfig,
    no_code_execution_rule,
    json_only_rule,
)


class TestTopicFilter:
    """Tests for the TopicFilter class."""

    @pytest.fixture
    def topic_filter(self):
        """Create a topic filter with default blocked topics."""
        return TopicFilter(include_defaults=True)

    def test_safe_content(self, topic_filter):
        """Test that safe content passes."""
        violations = topic_filter.check("Here is the weather forecast for today.")
        assert len(violations) == 0

    def test_blocked_keyword(self, topic_filter):
        """Test detection of blocked keywords."""
        violations = topic_filter.check("Here are instructions for money laundering.")
        assert len(violations) > 0
        assert violations[0].violation_type == "blocked_topic"

    def test_blocked_pattern(self, topic_filter):
        """Test detection of blocked patterns."""
        violations = topic_filter.check("Here's how to hack into the system.")
        assert len(violations) > 0

    def test_filter_content(self, topic_filter):
        """Test content filtering."""
        original = "Here's how to hack into a system and steal data."
        filtered = topic_filter.filter_content(original)

        assert "[CONTENT FILTERED]" in filtered
        assert "hack" not in filtered.lower()

    def test_contains_blocked(self, topic_filter):
        """Test contains_blocked helper."""
        assert topic_filter.contains_blocked("How to bypass security measures")
        assert not topic_filter.contains_blocked("Here is the weather forecast")

    def test_custom_topic(self):
        """Test adding custom blocked topics."""
        custom_topic = TopicConfig(
            name="competitor_info",
            patterns=[r"competitor\s+pricing"],
            keywords=["competitor analysis"],
            action=GuardrailAction.BLOCK,
        )
        topic_filter = TopicFilter(blocked_topics=[custom_topic], include_defaults=False)

        violations = topic_filter.check("Here's our competitor analysis report.")
        assert len(violations) > 0
        assert "competitor_info" in violations[0].rule_name


class TestOutputValidationRule:
    """Tests for OutputValidationRule."""

    def test_valid_content(self):
        """Test valid content passes validation."""
        rule = OutputValidationRule(
            name="no_profanity",
            description="Block profanity",
            validator=lambda x: "badword" not in x.lower(),
        )

        violation = rule.validate("This is clean content.")
        assert violation is None

    def test_invalid_content(self):
        """Test invalid content fails validation."""
        rule = OutputValidationRule(
            name="no_profanity",
            description="Block profanity",
            validator=lambda x: "badword" not in x.lower(),
            error_message="Content contains profanity",
        )

        violation = rule.validate("This has badword in it.")
        assert violation is not None
        assert violation.rule_name == "no_profanity"
        assert violation.description == "Content contains profanity"


class TestPrebuiltRules:
    """Tests for pre-built validation rules."""

    def test_no_code_execution_safe(self):
        """Test no_code_execution allows safe content."""
        rule = no_code_execution_rule()
        violation = rule.validate("print('hello world')")
        assert violation is None

    def test_no_code_execution_blocks_eval(self):
        """Test no_code_execution blocks eval."""
        rule = no_code_execution_rule()
        violation = rule.validate("result = eval(user_input)")
        assert violation is not None
        assert violation.action == GuardrailAction.BLOCK

    def test_json_only_valid_json(self):
        """Test json_only allows valid JSON."""
        rule = json_only_rule()
        violation = rule.validate('{"key": "value", "number": 42}')
        assert violation is None

    def test_json_only_invalid_json(self):
        """Test json_only blocks invalid JSON."""
        rule = json_only_rule()
        violation = rule.validate("This is not JSON")
        assert violation is not None


class TestGuardrailsEngine:
    """Tests for the GuardrailsEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a guardrails engine with default config."""
        config = GuardrailConfig(
            enable_topic_filter=True,
            enable_pii_filter=False,  # No PII filter for these tests
            enable_injection_detection=False,  # No injection detection for these tests
        )
        return GuardrailsEngine(config)

    @pytest.mark.asyncio
    async def test_filter_input_safe(self, engine):
        """Test that safe input passes."""
        result = await engine.filter_input("Hello, how can I help you?")

        assert not result.was_blocked
        assert result.filtered_content == result.original_content

    @pytest.mark.asyncio
    async def test_filter_output_safe(self, engine):
        """Test that safe output passes."""
        result = await engine.filter_output("Here is your answer: 42")

        assert not result.was_blocked
        assert not result.has_violations

    @pytest.mark.asyncio
    async def test_filter_output_blocked_topic(self, engine):
        """Test that blocked topics are filtered in output."""
        result = await engine.filter_output(
            "Here's how to hack into a system and bypass security."
        )

        assert result.has_violations
        assert result.was_modified or result.was_blocked

    @pytest.mark.asyncio
    async def test_add_blocked_topic_runtime(self, engine):
        """Test adding blocked topics at runtime."""
        engine.add_blocked_topic(
            name="test_topic",
            keywords=["forbidden_word"],
            action=GuardrailAction.BLOCK,
        )

        result = await engine.filter_output("This contains forbidden_word.")
        assert result.was_blocked

    @pytest.mark.asyncio
    async def test_max_length_filter(self):
        """Test output length limiting."""
        config = GuardrailConfig(
            max_output_length=50,
            max_output_length_action=GuardrailAction.FILTER,
            enable_topic_filter=False,
        )
        engine = GuardrailsEngine(config)

        long_content = "A" * 100
        result = await engine.filter_output(long_content)

        assert result.was_modified
        assert len(result.filtered_content) <= 53  # 50 + "..."

    @pytest.mark.asyncio
    async def test_validation_rules(self):
        """Test custom validation rules."""
        config = GuardrailConfig(
            enable_topic_filter=False,
            validation_rules=[
                OutputValidationRule(
                    name="no_numbers",
                    description="No numbers allowed",
                    validator=lambda x: not any(c.isdigit() for c in x),
                    action=GuardrailAction.WARN,
                )
            ],
        )
        engine = GuardrailsEngine(config)

        result = await engine.filter_output("The answer is 42.")
        assert result.has_violations
        assert result.violations[0].rule_name == "no_numbers"
