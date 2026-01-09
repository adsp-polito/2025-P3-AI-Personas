# Testing Guide

How to run and write tests for the AI Personas project.

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test file

```bash
pytest tests/test_auth_service.py
```

### Run with verbose output

```bash
pytest -v
```

### Run tests matching a pattern

```bash
pytest -k "auth"
```

### See print statements

```bash
pytest -s
```

## Test Organization

Tests are organized in the `tests/` directory:

```
tests/
├── test_auth_service.py       # Authentication tests
├── test_business_db.py         # Database tests
├── test_vector_db.py           # Vector storage tests
├── test_chat_session.py        # Session state tests
├── test_config_paths.py        # Configuration tests
├── test_types_validation.py    # Data model tests
├── test_prompt_builder.py      # Prompt construction tests
├── test_api_client.py          # API client tests
├── test_data.py                # High-level smoke tests
├── test_api_openapi.py         # API contract tests
└── test_orchestrator_filtering.py  # Context filtering tests
```

## Writing New Tests

### Basic test structure

```python
"""
Brief description of what this test file covers.
"""

from adsp.some_module import SomeClass


def test_something():
    # Setup
    obj = SomeClass()

    # Execute
    result = obj.do_something()

    # Assert
    assert result == expected_value
```

### Test naming convention

- Test files: `test_<module_name>.py`
- Test functions: `test_<what_it_tests>()`

Examples:
- `test_auth_service.py` → `test_register_new_user()`
- `test_memory.py` → `test_stores_messages()`

### Keep tests simple

Good:
```python
def test_vector_db_stores_document():
    db = VectorDatabase()
    db.upsert("p1", "doc1")

    result = db.search("p1", "query")
    assert result == "doc1"
```

Avoid:
```python
def test_complex_scenario_with_multiple_edge_cases_and_validations():
    # 100 lines of setup
    # Complex logic
    # Many assertions
```

### Use fixtures sparingly

For shared setup, pytest fixtures are useful:

```python
import pytest

@pytest.fixture
def auth_service():
    service = AuthService()
    service.register("test_user", "test_token")
    return service

def test_authorized_user(auth_service):
    assert auth_service.is_authorized("test_user", "test_token")
```

But for simple cases, just create objects in the test.

## Test Types

### Unit tests

Test individual components in isolation:

```python
def test_memory_stores_message():
    memory = ConversationMemory()
    memory.store("p1", {"query": "hello"})

    history = memory.get_history("p1")
    assert len(history) == 1
```

### Integration tests

Test multiple components together:

```python
def test_orchestrator_with_memory():
    orchestrator = Orchestrator(
        memory=ConversationMemory(),
        retriever=FakeRetriever()
    )
    response = orchestrator.handle(request)
    assert response.answer
```

### Smoke tests

Quick checks that basic functionality works:

```python
def test_api_server_starts():
    from adsp.app.api_server import create_app
    app = create_app()
    assert app is not None
```

## Coverage

Check test coverage:

```bash
pip install pytest-cov
pytest --cov=adsp --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

We don't enforce 100% coverage, but aim for:
- Core logic: 80%+
- Utilities: 70%+
- UI/scripts: 50%+

## Continuous Integration

Tests run automatically on every push via GitHub Actions.

See `.github/workflows/tests.yml` for configuration.

## Troubleshooting Tests

### Import errors

Make sure the package is installed:

```bash
pip install -e .
```

### Tests pass locally but fail in CI

Check Python version differences. We test on 3.10 and 3.11.

### Slow tests

Mark slow tests:

```python
import pytest

@pytest.mark.slow
def test_expensive_operation():
    # ...
```

Then skip them:

```bash
pytest -m "not slow"
```

### Flaky tests

If a test sometimes passes and sometimes fails, it might depend on:
- External services (mock them)
- Random data (use fixed seeds)
- Timing (add retries or timeouts)

## Best Practices

1. **One assertion per test** (when possible)
2. **Test behavior, not implementation**
3. **Use descriptive test names**
4. **Keep tests independent**
5. **Mock external dependencies**
6. **Don't test framework code** (e.g., don't test that FastAPI works)

## What NOT to test

- Third-party libraries (trust they work)
- Trivial getters/setters
- Configuration files
- Generated code

Focus testing effort on:
- Business logic
- Data transformations
- Error handling
- Edge cases
