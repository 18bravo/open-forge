# Contributing to Open Forge

Thank you for your interest in contributing to Open Forge! This guide explains how to contribute effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Guidelines](#code-guidelines)
- [Pull Request Process](#pull-request-process)
- [Review Process](#review-process)
- [Community Guidelines](#community-guidelines)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Read the documentation**
   - [Architecture Overview](./architecture.md)
   - [Local Setup Guide](./local-setup.md)

2. **Set up your development environment**
   ```bash
   git clone https://github.com/18bravo/open-forge.git
   cd open-forge
   make setup
   ```

3. **Run the test suite**
   ```bash
   make test
   ```

### Finding Issues to Work On

- **Good First Issues**: Look for issues labeled `good first issue`
- **Help Wanted**: Issues labeled `help wanted` need contributors
- **Feature Requests**: Check discussions for feature ideas

---

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes

Follow the code guidelines below when making changes.

### 3. Write Tests

All new code should include tests:

```python
# tests/unit/test_my_feature.py

import pytest
from my_module import MyFeature

class TestMyFeature:
    def test_basic_functionality(self):
        feature = MyFeature()
        result = feature.do_something()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        feature = MyFeature()
        result = await feature.do_something_async()
        assert result is not None
```

### 4. Run Quality Checks

```bash
# Run all checks
make lint
make typecheck
make test

# Or run individually
ruff check packages/
mypy packages/
pytest packages/*/tests
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "Add stakeholder analysis agent with LLM reasoning"
git commit -m "Fix race condition in task queue processing"
git commit -m "Update ontology compiler to support enum types"

# Bad commit messages
git commit -m "Fix bug"
git commit -m "Update code"
git commit -m "WIP"
```

**Commit message format:**
```
<type>: <short description>

<optional longer description>

<optional footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Code Guidelines

### Python Style

We use **Ruff** for linting and formatting:

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
```

**Key conventions:**
- Line length: 100 characters
- Use type hints for all functions
- Use async/await for I/O operations
- Prefer `polars` over `pandas` for data processing

```python
# Good
async def get_engagement(engagement_id: str) -> Engagement:
    """Fetch an engagement by ID.

    Args:
        engagement_id: The unique engagement identifier.

    Returns:
        The engagement object.

    Raises:
        NotFoundError: If engagement doesn't exist.
    """
    engagement = await db.get(Engagement, engagement_id)
    if not engagement:
        raise NotFoundError(f"Engagement {engagement_id} not found")
    return engagement


# Bad
def get_engagement(id):
    e = db.get(Engagement, id)
    return e
```

### TypeScript Style

For frontend code:

```typescript
// Good
interface EngagementProps {
  engagement: Engagement;
  onUpdate: (engagement: Engagement) => void;
}

const EngagementCard: React.FC<EngagementProps> = ({ engagement, onUpdate }) => {
  // Component logic
};

// Bad
const EngagementCard = (props) => {
  // No types
};
```

### Documentation

All public functions and classes should have docstrings:

```python
class OntologyDesignerAgent(BaseOpenForgeAgent):
    """Agent that designs ontologies from requirements.

    This agent analyzes requirements documents and data source schemas
    to generate LinkML ontologies that model the customer's domain.

    Attributes:
        llm: The language model used for reasoning.
        schema_manager: Manager for ontology schemas.

    Example:
        >>> agent = OntologyDesignerAgent(llm=claude)
        >>> result = await agent.execute(requirements)
        >>> print(result.ontology)
    """
```

### Testing Guidelines

**Unit tests** should be fast and isolated:

```python
# tests/unit/test_ontology_compiler.py

import pytest
from ontology.compiler import OntologyCompiler, OutputFormat

class TestOntologyCompiler:
    @pytest.fixture
    def compiler(self):
        return OntologyCompiler()

    @pytest.fixture
    def sample_schema(self):
        return """
        id: https://example.org/test
        name: test_ontology
        classes:
          Person:
            attributes:
              name:
                range: string
        """

    def test_compile_sql(self, compiler, sample_schema):
        result = compiler.compile(sample_schema, formats=[OutputFormat.SQL])
        assert not result.has_errors()
        assert "CREATE TABLE" in result.get_output(OutputFormat.SQL)
```

**Integration tests** verify component interaction:

```python
# tests/integration/test_engagement_flow.py

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestEngagementFlow:
    @pytest.mark.asyncio
    async def test_create_and_start_engagement(self, client: AsyncClient):
        # Create engagement
        response = await client.post("/api/v1/engagements", json={
            "name": "Test Engagement",
            "objective": "Test the flow"
        })
        assert response.status_code == 201

        engagement_id = response.json()["id"]

        # Start discovery
        response = await client.post(
            f"/api/v1/engagements/{engagement_id}/start"
        )
        assert response.status_code == 200
```

---

## Pull Request Process

### PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear
- [ ] PR description explains the changes

### PR Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Screenshots
(If applicable)

## Related Issues
Fixes #123
```

### PR Size Guidelines

- **Small PRs** (< 200 lines): Quick reviews, easy to merge
- **Medium PRs** (200-500 lines): Normal review cycle
- **Large PRs** (> 500 lines): Consider splitting

### Review Response

When reviewers request changes:

1. Address all comments
2. Re-request review when ready
3. Don't force-push after review starts

---

## Review Process

### What Reviewers Look For

1. **Correctness**: Does the code do what it's supposed to?
2. **Testing**: Are there adequate tests?
3. **Style**: Does it follow guidelines?
4. **Documentation**: Is it documented?
5. **Performance**: Are there performance concerns?
6. **Security**: Are there security issues?

### Providing Reviews

When reviewing others' code:

- Be respectful and constructive
- Explain the "why" behind suggestions
- Distinguish between required changes and suggestions
- Approve promptly when changes look good

```markdown
# Good review comment
Consider using `polars` instead of `pandas` here for better performance
with large datasets. See the performance guide for benchmarks.

# Bad review comment
Don't use pandas.
```

---

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Assume good intent
- Focus on the technical merits

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Requests**: Code contributions

### Getting Help

If you're stuck:

1. Check existing documentation
2. Search closed issues
3. Ask in GitHub Discussions
4. Tag maintainers if urgent

---

## Recognition

Contributors are recognized in:

- Release notes
- Contributors file
- GitHub contributor graph

---

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

---

## Related Documentation

- [Local Setup Guide](./local-setup.md)
- [Testing Guide](./testing.md)
- [Code Style Guide](./code-style.md)
- [Architecture Overview](./architecture.md)
