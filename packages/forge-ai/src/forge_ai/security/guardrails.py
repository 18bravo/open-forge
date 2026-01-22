"""
Guardrails for LLM output validation.

This module provides output validation and safety guardrails:
- Topic filtering (block specific topics in outputs)
- Output schema validation
- Content safety checks
- Custom validation rules
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


class GuardrailAction(str, Enum):
    """Action to take when a guardrail is violated."""

    BLOCK = "block"  # Block the response entirely
    FILTER = "filter"  # Filter/redact the violating content
    WARN = "warn"  # Allow but log a warning
    PASSTHROUGH = "passthrough"  # Allow without action


@dataclass
class GuardrailViolation:
    """Details of a guardrail violation."""

    rule_name: str
    violation_type: str
    description: str
    action: GuardrailAction
    matched_content: str | None = None
    position: tuple[int, int] | None = None  # (start, end) if applicable


@dataclass
class OutputValidationRule:
    """A rule for validating LLM output."""

    name: str
    description: str
    validator: Callable[[str], bool]  # Returns True if valid
    action: GuardrailAction = GuardrailAction.BLOCK
    error_message: str | None = None

    def validate(self, content: str) -> GuardrailViolation | None:
        """
        Validate content against this rule.

        Returns None if valid, GuardrailViolation if invalid.
        """
        try:
            is_valid = self.validator(content)
            if not is_valid:
                return GuardrailViolation(
                    rule_name=self.name,
                    violation_type="validation_failed",
                    description=self.error_message or self.description,
                    action=self.action,
                )
            return None
        except Exception as e:
            logger.warning("Validation rule error", rule=self.name, error=str(e))
            return GuardrailViolation(
                rule_name=self.name,
                violation_type="validation_error",
                description=f"Validation error: {e}",
                action=GuardrailAction.WARN,
            )


@dataclass
class TopicConfig:
    """Configuration for a blocked topic."""

    name: str
    patterns: list[str]  # Regex patterns
    keywords: list[str]  # Simple keyword matches
    action: GuardrailAction = GuardrailAction.FILTER


class TopicFilter:
    """
    Filter outputs for blocked topics.

    Can be used to prevent the model from discussing certain topics
    even if instructed to do so.
    """

    # Default blocked topics for safety
    DEFAULT_BLOCKED_TOPICS: list[TopicConfig] = [
        TopicConfig(
            name="harmful_instructions",
            patterns=[
                r"how\s+to\s+(make|build|create)\s+a?\s*(bomb|weapon|explosive)",
                r"instructions\s+for\s+(violence|harming)",
            ],
            keywords=["bomb making", "weapon instructions"],
            action=GuardrailAction.BLOCK,
        ),
        TopicConfig(
            name="illegal_activities",
            patterns=[
                r"how\s+to\s+(hack|steal|fraud)",
                r"bypass\s+(security|authentication)",
            ],
            keywords=["illegal drugs", "money laundering"],
            action=GuardrailAction.FILTER,
        ),
    ]

    def __init__(
        self,
        blocked_topics: list[TopicConfig] | None = None,
        include_defaults: bool = True,
    ):
        """
        Initialize the topic filter.

        Args:
            blocked_topics: Custom blocked topics.
            include_defaults: Whether to include default blocked topics.
        """
        self.topics: list[TopicConfig] = []

        if include_defaults:
            self.topics.extend(self.DEFAULT_BLOCKED_TOPICS)

        if blocked_topics:
            self.topics.extend(blocked_topics)

        # Compile patterns
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for topic in self.topics:
            self._compiled_patterns[topic.name] = [
                re.compile(p, re.IGNORECASE) for p in topic.patterns
            ]

    def check(self, content: str) -> list[GuardrailViolation]:
        """
        Check content for blocked topics.

        Returns list of violations found.
        """
        violations: list[GuardrailViolation] = []
        content_lower = content.lower()

        for topic in self.topics:
            # Check keywords
            for keyword in topic.keywords:
                if keyword.lower() in content_lower:
                    violations.append(
                        GuardrailViolation(
                            rule_name=f"topic:{topic.name}",
                            violation_type="blocked_topic",
                            description=f"Content contains blocked topic: {topic.name}",
                            action=topic.action,
                            matched_content=keyword,
                        )
                    )

            # Check patterns
            for pattern in self._compiled_patterns.get(topic.name, []):
                match = pattern.search(content)
                if match:
                    violations.append(
                        GuardrailViolation(
                            rule_name=f"topic:{topic.name}",
                            violation_type="blocked_topic",
                            description=f"Content matches blocked pattern for: {topic.name}",
                            action=topic.action,
                            matched_content=match.group(0),
                            position=(match.start(), match.end()),
                        )
                    )

        return violations

    def filter_content(self, content: str) -> str:
        """
        Filter blocked content from output.

        Replaces blocked content with a placeholder.
        """
        filtered = content

        for topic in self.topics:
            if topic.action != GuardrailAction.FILTER:
                continue

            # Filter patterns
            for pattern in self._compiled_patterns.get(topic.name, []):
                filtered = pattern.sub("[CONTENT FILTERED]", filtered)

            # Filter keywords
            for keyword in topic.keywords:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                filtered = pattern.sub("[CONTENT FILTERED]", filtered)

        return filtered

    def contains_blocked(self, content: str) -> bool:
        """Check if content contains any blocked topics."""
        return len(self.check(content)) > 0


@dataclass
class GuardrailConfig:
    """
    Configuration for the guardrails engine.

    Controls which guardrails are active and their behavior.
    """

    # PII filtering
    enable_pii_filter: bool = True
    pii_action: GuardrailAction = GuardrailAction.FILTER

    # Topic filtering
    enable_topic_filter: bool = True
    blocked_topics: list[TopicConfig] = field(default_factory=list)
    include_default_topics: bool = True

    # Injection detection
    enable_injection_detection: bool = True
    injection_action: GuardrailAction = GuardrailAction.BLOCK

    # Output validation
    enable_output_validation: bool = True
    validation_rules: list[OutputValidationRule] = field(default_factory=list)

    # Length limits
    max_output_length: int | None = None
    max_output_length_action: GuardrailAction = GuardrailAction.FILTER

    # Custom validators
    custom_validators: list[Callable[[str], GuardrailViolation | None]] = field(
        default_factory=list
    )


@dataclass
class GuardrailResult:
    """Result of applying guardrails to content."""

    original_content: str
    filtered_content: str
    violations: list[GuardrailViolation]
    was_blocked: bool
    was_modified: bool

    @property
    def has_violations(self) -> bool:
        """Check if any violations occurred."""
        return len(self.violations) > 0


class GuardrailsEngine:
    """
    Engine for applying safety guardrails to LLM inputs and outputs.

    Orchestrates multiple guardrail checks and handles violations
    according to configured actions.
    """

    def __init__(
        self,
        config: GuardrailConfig | None = None,
        pii_filter: Any | None = None,  # PIIFilter instance
        injection_detector: Any | None = None,  # InjectionDetector instance
    ):
        """
        Initialize the guardrails engine.

        Args:
            config: Guardrail configuration.
            pii_filter: PII filter instance for PII masking.
            injection_detector: Injection detector for prompt injection detection.
        """
        self.config = config or GuardrailConfig()
        self.pii_filter = pii_filter
        self.injection_detector = injection_detector

        # Initialize topic filter
        self.topic_filter = TopicFilter(
            blocked_topics=self.config.blocked_topics,
            include_defaults=self.config.include_default_topics,
        )

    async def filter_input(self, content: str) -> GuardrailResult:
        """
        Apply input guardrails.

        Checks for prompt injection and PII in user input.

        Args:
            content: The input content to filter.

        Returns:
            GuardrailResult with filtered content and violations.
        """
        violations: list[GuardrailViolation] = []
        filtered_content = content
        was_blocked = False

        # Check for prompt injection
        if self.config.enable_injection_detection and self.injection_detector is not None:
            injection_result = await self.injection_detector.detect(content)
            if injection_result.is_injection:
                violations.append(
                    GuardrailViolation(
                        rule_name="injection_detection",
                        violation_type="prompt_injection",
                        description=f"Prompt injection detected: {injection_result.threat_level.value}",
                        action=self.config.injection_action,
                        matched_content=", ".join(injection_result.matched_patterns),
                    )
                )

                if self.config.injection_action == GuardrailAction.BLOCK:
                    was_blocked = True

        # Filter PII from input
        if self.config.enable_pii_filter and self.pii_filter is not None and not was_blocked:
            pii_result = self.pii_filter.mask(content)
            if pii_result != content:
                violations.append(
                    GuardrailViolation(
                        rule_name="pii_filter",
                        violation_type="pii_detected",
                        description="PII detected and masked in input",
                        action=self.config.pii_action,
                    )
                )
                filtered_content = pii_result

        return GuardrailResult(
            original_content=content,
            filtered_content="" if was_blocked else filtered_content,
            violations=violations,
            was_blocked=was_blocked,
            was_modified=filtered_content != content,
        )

    async def filter_output(self, content: str) -> GuardrailResult:
        """
        Apply output guardrails.

        Checks for blocked topics, PII, length limits, and custom rules.

        Args:
            content: The output content to filter.

        Returns:
            GuardrailResult with filtered content and violations.
        """
        violations: list[GuardrailViolation] = []
        filtered_content = content
        was_blocked = False

        # Check topic filter
        if self.config.enable_topic_filter:
            topic_violations = self.topic_filter.check(content)
            violations.extend(topic_violations)

            # Handle topic violations
            for violation in topic_violations:
                if violation.action == GuardrailAction.BLOCK:
                    was_blocked = True
                    break
                elif violation.action == GuardrailAction.FILTER:
                    filtered_content = self.topic_filter.filter_content(filtered_content)

        # Filter PII from output
        if self.config.enable_pii_filter and self.pii_filter is not None and not was_blocked:
            pii_result = self.pii_filter.mask(filtered_content)
            if pii_result != filtered_content:
                violations.append(
                    GuardrailViolation(
                        rule_name="pii_filter",
                        violation_type="pii_detected",
                        description="PII detected and masked in output",
                        action=self.config.pii_action,
                    )
                )
                filtered_content = pii_result

        # Check length limits
        if self.config.max_output_length and len(filtered_content) > self.config.max_output_length:
            violations.append(
                GuardrailViolation(
                    rule_name="length_limit",
                    violation_type="output_too_long",
                    description=f"Output exceeds maximum length of {self.config.max_output_length}",
                    action=self.config.max_output_length_action,
                )
            )

            if self.config.max_output_length_action == GuardrailAction.BLOCK:
                was_blocked = True
            elif self.config.max_output_length_action == GuardrailAction.FILTER:
                filtered_content = filtered_content[: self.config.max_output_length] + "..."

        # Run validation rules
        if self.config.enable_output_validation:
            for rule in self.config.validation_rules:
                violation = rule.validate(filtered_content)
                if violation:
                    violations.append(violation)
                    if violation.action == GuardrailAction.BLOCK:
                        was_blocked = True

        # Run custom validators
        for validator in self.config.custom_validators:
            try:
                violation = validator(filtered_content)
                if violation:
                    violations.append(violation)
                    if violation.action == GuardrailAction.BLOCK:
                        was_blocked = True
            except Exception as e:
                logger.warning("Custom validator error", error=str(e))

        # If blocked, return placeholder
        if was_blocked:
            filtered_content = "[Content blocked due to policy violation]"

        return GuardrailResult(
            original_content=content,
            filtered_content=filtered_content,
            violations=violations,
            was_blocked=was_blocked,
            was_modified=filtered_content != content,
        )

    def add_blocked_topic(
        self,
        name: str,
        patterns: list[str] | None = None,
        keywords: list[str] | None = None,
        action: GuardrailAction = GuardrailAction.FILTER,
    ) -> None:
        """Add a blocked topic at runtime."""
        topic = TopicConfig(
            name=name,
            patterns=patterns or [],
            keywords=keywords or [],
            action=action,
        )
        self.topic_filter.topics.append(topic)
        self.topic_filter._compiled_patterns[name] = [
            re.compile(p, re.IGNORECASE) for p in topic.patterns
        ]

    def add_validation_rule(self, rule: OutputValidationRule) -> None:
        """Add a validation rule at runtime."""
        self.config.validation_rules.append(rule)


# Pre-built validation rules
def no_code_execution_rule() -> OutputValidationRule:
    """Rule that blocks outputs containing code execution patterns."""
    dangerous_patterns = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"subprocess\.",
        r"os\.system\s*\(",
    ]

    def validator(content: str) -> bool:
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        return True

    return OutputValidationRule(
        name="no_code_execution",
        description="Block outputs containing code execution patterns",
        validator=validator,
        action=GuardrailAction.BLOCK,
        error_message="Output contains potentially dangerous code execution patterns",
    )


def json_only_rule() -> OutputValidationRule:
    """Rule that ensures output is valid JSON."""
    import json as json_module

    def validator(content: str) -> bool:
        try:
            json_module.loads(content)
            return True
        except json_module.JSONDecodeError:
            return False

    return OutputValidationRule(
        name="json_only",
        description="Ensure output is valid JSON",
        validator=validator,
        action=GuardrailAction.BLOCK,
        error_message="Output is not valid JSON",
    )
